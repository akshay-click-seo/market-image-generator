"""
sections/generate_all.py
Streamlit page: "Generate All" -- the market's core data (name, country,
currency, years, values, CAGR) plus segmentation info is entered ONCE on a
single page, and with a single click all four dashboard image templates
(Market Growth Style 1, Market Growth Style 2, Regional Analysis,
Segmentation) are generated together, each shown with its own export
controls right below it.
"""

import io
import os
import sys
import zipfile

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser import extract_from_text, generate_yearly_values, compute_cagr, extract_segments_from_text
from utils.export import export_image, file_extension_for, slugify_filename
from utils.fonts import list_available_fonts, get_default_font_path
from utils.state import init_state, get_canvas_size
from utils.units import UNIT_LABELS
from utils.numfmt import es_number_input, format_es_number_exact
from utils.map import find_country_feature, resolve_region
from templates import growth_style1, growth_style2, regional_style, segmentation_style
from templates.segmentation_style import DEFAULT_PALETTE


# Curated for this tool's actual usage -- mostly Latin American markets
# (this brand's core coverage) plus a handful of major global markets, with
# "Latin America" itself included as a region option (resolves via
# utils.map.resolve_region() to highlight every LatAm country on the
# Regional Analysis map, same as typing it into the free-text field would).
# "Global" (5-region world pins) and "Otro" (signposts the free-text field
# below, which overrides whatever is picked here -- for any country/region
# not in this list) are kept as the two special, non-country entries.
COUNTRY_OPTIONS = [
    "Global",
    "Colombia", "Chile", "Peru", "Argentina", "China", "Brazil", "Japan",
    "Uruguay", "Ecuador", "El Salvador", "Venezuela", "Latin America",
    "United States", "México", "Spain",
    "Otro",
]

# "None" is for reports whose value has no currency at all (e.g. a plain
# quantity in MMT/Toneladas). It's a real option in this dropdown, but the
# literal word "None" is never rendered onto a generated image -- every
# template strips it out via utils.numfmt.format_money_parts/has_currency.
CURRENCY_OPTIONS = ["USD", "EUR", "INR", "GBP", "JPY", "CNY", "None"]

PRESET_SEGMENT_LABELS = [
    "Por Tipo de Producto", "Por Aplicación", "Por Fuente",
    "Por Canal de Distribución", "Por Región", "Por Usuario Final",
]

# filename_fn(name_for_files) -> the download filename base (no extension).
# Growth Style 1 and Style 2 intentionally share the same "cuota-del-..."
# base name (both are, conceptually, "the graph" image) -- fine for
# individual downloads (each is its own click), but the Download-All ZIP
# below numbers them (-1 / -2) if both are selected together so neither
# silently overwrites the other inside the archive.
RESULT_SECTIONS = [
    ("all_growth1_image", "📈 Market Growth — Style 1", "all_g1", lambda name: f"cuota-del-{name}"),
    ("all_growth2_image", "📈 Market Growth — Style 2", "all_g2", lambda name: f"cuota-del-{name}"),
    ("all_regional_image", "🗺️ Regional Analysis", "all_reg", lambda name: f"{name}-region"),
    ("all_seg_image", "🍩 Segmentation", "all_seg", lambda name: f"{name}-segmento"),
]


def _seed(key, default):
    """Seed a widget's session_state key with a default ONLY if it doesn't
    already exist -- then the widget is instantiated below using ONLY
    `key=` (no separate `value=`/`index=`). This is the one pattern that
    lets code elsewhere (Auto-Fetch) reliably overwrite a field: Streamlit
    always prefers an existing session_state[key] over a widget's value=/
    index= argument on every rerun after the first, so a dual-key setup
    (a widget with `key="x_input"` but a default sourced from a DIFFERENT
    key "x") silently ignores any later attempt to update it via the wrong
    key -- Auto-Fetch would compute the right values but never see them
    reach the page."""
    if key not in st.session_state:
        st.session_state[key] = default


def _export_block(img, key_prefix, filename_base):
    st.subheader("Export")
    col_fmt, col_q, col_dl = st.columns([1, 1, 1])
    with col_fmt:
        fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1, key=f"{key_prefix}_fmt")
    with col_q:
        quality = st.slider("Calidad", 50, 100, 90, key=f"{key_prefix}_quality")
    data = export_image(img, fmt=fmt, quality=quality)
    ext = file_extension_for(fmt)
    with col_dl:
        st.download_button(
            "⬇️ Descargar", data=data, file_name=f"{filename_base}.{ext}",
            mime=f"image/{ext}" if fmt != "PDF" else "application/pdf",
            width='stretch', key=f"{key_prefix}_dl",
        )


def render_page():
    init_state()
    st.header("🎨 Generar Todas las Imágenes")
    st.caption(
        "Completa los datos del mercado una sola vez y genera las 4 imágenes "
        "(Growth Style 1, Growth Style 2, Regional Analysis, Segmentation) juntas, en un solo clic."
    )

    # ---- Auto Fetch: market growth figures (shared by both Growth styles + Regional) ----
    with st.expander("📋 Auto Fetch — Pega un párrafo de reporte (IMARC / IDE)", expanded=True):
        pasted_text = st.text_area(
            "Special Paste Box",
            placeholder=(
                "The market reached USD 145 Million in 2025 and is expected to reach "
                "USD 367.3 Million by 2035 growing at a CAGR of 9.74% during 2026-2035."
            ),
            height=100, key="all_paste_box",
        )
        if st.button("🔍 Extraer datos", key="all_extract_btn"):
            extracted = extract_from_text(pasted_text)
            if extracted.start_value is not None:
                st.session_state["all_start_value_input"] = format_es_number_exact(extracted.start_value)
            if extracted.end_value is not None:
                st.session_state["all_end_value_input"] = format_es_number_exact(extracted.end_value)
            if extracted.base_year is not None:
                st.session_state["all_base_year_input"] = int(extracted.base_year)
            if extracted.forecast_year is not None:
                st.session_state["all_forecast_year_input"] = int(extracted.forecast_year)
            if extracted.cagr is not None:
                st.session_state["all_cagr_input"] = format_es_number_exact(extracted.cagr)
            if extracted.currency in CURRENCY_OPTIONS:
                st.session_state["all_currency_select"] = extracted.currency
            if extracted.unit in UNIT_LABELS:
                st.session_state["all_unit_select"] = extracted.unit
            if extracted.market_name:
                st.session_state["all_market_name_input"] = extracted.market_name
            if extracted.region:
                # Free-text override field takes precedence over the fixed
                # Country dropdown -- lets a broad region like "Latinoamérica"
                # (not a single country) come through as typed text.
                st.session_state["all_country_custom"] = extracted.region
            extras = []
            if extracted.market_name:
                extras.append(f"Market: {extracted.market_name}")
            if extracted.region:
                extras.append(f"Region: {extracted.region}")
            st.success(
                f"Extraído: {extracted.currency} {extracted.start_value} ({extracted.base_year}) → "
                f"{extracted.currency} {extracted.end_value} ({extracted.forecast_year}), "
                f"CAGR {extracted.cagr}%" + (" · " + " · ".join(extras) if extras else "")
            )
            st.rerun()

    st.subheader("Datos del Mercado")
    st.caption("Estos campos alimentan Growth Style 1, Growth Style 2 y Regional Analysis.")
    _seed("all_market_name_input", "Clonación de Voz")
    _seed("all_country_select", "Global")
    _seed("all_country_custom", "")
    _seed("all_currency_select", "USD")
    _seed("all_base_year_input", 2025)
    _seed("all_forecast_year_input", 2035)
    _seed("all_unit_select", "Millones")
    c1, c2, c3 = st.columns(3)
    with c1:
        market_name = st.text_input("Market Name", key="all_market_name_input")
        country = st.selectbox("Country", COUNTRY_OPTIONS, key="all_country_select")
        custom_country = st.text_input("...o escribe un país personalizado (opcional)", key="all_country_custom")
        if custom_country.strip():
            country = custom_country.strip()
        currency = st.selectbox("Currency", CURRENCY_OPTIONS, key="all_currency_select")
    with c2:
        base_year = st.number_input("Base Year", step=1, key="all_base_year_input")
        forecast_year = st.number_input("Forecast Year", step=1, key="all_forecast_year_input")
        unit = st.selectbox("Unit", UNIT_LABELS, key="all_unit_select")
    with c3:
        start_value = es_number_input(st, "Start Value", value=2.4, key="all_start_value_input")
        end_value = es_number_input(st, "End Value", value=29.8, key="all_end_value_input")
        cagr_input = es_number_input(st, "CAGR (%)", value=25.8, key="all_cagr_input")

    if country.strip().lower() != "global":
        feature = find_country_feature(country)
        region_info = None if feature else resolve_region(country)
        if feature:
            st.success(f"✅ País reconocido: {feature['properties'].get('NAME')} — el mapa de Regional Analysis se resaltará automáticamente.")
        elif region_info:
            st.success(f"✅ Región reconocida: {region_info['display']} — el mapa de Regional Analysis resaltará todos sus países automáticamente.")
        else:
            st.warning("⚠️ País no reconocido en la base de datos del mapa mundial (solo afecta a Regional Analysis).")
    else:
        st.caption("ℹ️ Con Country = 'Global', el mapa de Regional Analysis no resaltará ningún país en particular.")

    num_years = int(forecast_year) - int(base_year)
    years = list(range(int(base_year), int(forecast_year) + 1))

    # The intermediate (non-base/forecast-year) bar heights are never data
    # the user actually supplied -- only start_value, end_value and a CAGR
    # are given, not a figure for every year in between -- so SOME curve has
    # to be derived to shape those bars, and the Start -> End implied rate
    # gives a smooth, real growth path between the two stated values. This
    # is purely a visual interpolation, though: no number from it is ever
    # shown as a labeled value (values[0]/[-1] are forced back to the
    # user's own start_value/end_value right below), so it doesn't conflict
    # with "show my data, don't recalculate it" -- that rule applies to
    # displayed figures (the CAGR card below, and the start/end labels),
    # not to an invisible chart curve.
    effective_growth_cagr = compute_cagr(start_value, end_value, num_years)
    if effective_growth_cagr is None:
        effective_growth_cagr = cagr_input
    values = generate_yearly_values(start_value, effective_growth_cagr, num_years)
    if values:
        values[0] = start_value
        values[-1] = end_value
    if len(values) != len(years):
        if len(values) < len(years):
            values += [values[-1] if values else 0] * (len(years) - len(values))
        else:
            values = values[:len(years)]
    # CAGR shown on the image (stat card) must be exactly what the user
    # typed/pasted -- NOT a value silently recalculated from start/end.
    display_cagr = cagr_input

    st.divider()
    st.subheader("Segmentación")
    st.caption("Estos campos alimentan únicamente la imagen de Segmentation.")
    with st.expander("📋 Auto Fetch — Segmentos", expanded=False):
        pasted_seg_text = st.text_area(
            "Special Paste Box",
            placeholder=(
                "The market can be segmented based on product type, application, "
                "source, distribution channel, and region."
            ),
            height=80, key="all_seg_paste_box",
        )
        if st.button("🔍 Extraer segmentos", key="all_seg_extract_btn"):
            found = extract_segments_from_text(pasted_seg_text)
            if found:
                for i in range(8):
                    if i < len(found):
                        st.session_state[f"all_seg_label_{i}"] = found[i]
                    else:
                        st.session_state.pop(f"all_seg_label_{i}", None)
                st.session_state["all_n_segments_pending"] = max(2, min(8, len(found)))
                st.success(f"Extraídos {len(found)} segmentos: {', '.join(found)}")
                st.rerun()
            else:
                st.warning("No se encontraron segmentos en el texto.")

    slider_default = st.session_state.pop("all_n_segments_pending", None) or st.session_state.get("all_n_segments", 5)
    n_segments = st.select_slider(
        "Número máximo de campos a mostrar", options=[2, 3, 4, 5, 6, 7, 8],
        value=slider_default, key="all_n_segments",
    )
    seg_labels, seg_colors = [], []
    seg_cols = st.columns(2)
    for i in range(n_segments):
        col = seg_cols[i % 2]
        with col:
            input_key = f"all_seg_label_{i}"
            if input_key not in st.session_state:
                st.session_state[input_key] = PRESET_SEGMENT_LABELS[i] if i < len(PRESET_SEGMENT_LABELS) else ""
            label = st.text_input(f"Segmento {i + 1}", key=input_key)
            color = st.color_picker(f"Color {i + 1}", value=DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)], key=f"all_seg_color_{i}")
            seg_labels.append(label)
            seg_colors.append(color)

    filled_segments = [(label.strip(), color) for label, color in zip(seg_labels, seg_colors) if label.strip()]

    st.divider()
    st.subheader("Estilo y Marca")
    st.caption("Estos campos aplican a las 4 imágenes por igual.")
    col_logo, col_web = st.columns(2)
    with col_logo:
        logo_file = st.file_uploader("Logo (optional)", type=["png", "jpg", "jpeg"], key="all_logo_upload")
    with col_web:
        website = st.text_input(
            "Website", value=st.session_state.get("settings_website", "www.informesdeexpertos.com"), key="all_website_input"
        )

    col_bg, col_font = st.columns(2)
    with col_bg:
        bg_options = ["Classic Blue", "Modern White", "Gradient", "Light", "Dark"]
        default_bg = st.session_state.get("settings_background", "Classic Blue")
        background = st.selectbox(
            "Background", bg_options, index=bg_options.index(default_bg) if default_bg in bg_options else 0,
            key="all_background_select",
        )
    with col_font:
        fonts = list_available_fonts()
        font_names = list(fonts.keys()) or ["Calibri Regular"]
        default_font_index = font_names.index("Calibri Regular") if "Calibri Regular" in font_names else 0
        font_choice = st.selectbox("Font", font_names, index=default_font_index, key="all_font_select")

    width, height = get_canvas_size()

    logo_path = None
    if logo_file is not None:
        logo_path = f"/tmp/_uploaded_logo_all_{logo_file.name}"
        with open(logo_path, "wb") as f:
            f.write(logo_file.getvalue())

    font_family = font_choice.rsplit(" ", 1)[0] if " " in font_choice else font_choice
    font_bold_path = fonts.get(f"{font_family} Bold", get_default_font_path("Bold"))
    font_regular_path = fonts.get(font_choice, get_default_font_path("Regular"))

    st.divider()
    if st.button("🎨 Generar Todas las Imágenes", type="primary", width='stretch'):
        with st.spinner("Generando las 4 imágenes..."):
            common_growth_kwargs = dict(
                market_name=market_name, country=country, currency=currency,
                base_year=int(base_year), forecast_year=int(forecast_year),
                start_value=start_value, end_value=end_value, cagr=display_cagr,
                years=years, values=values, unit=unit, website=website,
                logo_path=logo_path, background=background,
                font_regular=font_regular_path, font_bold=font_bold_path,
                width=width, height=height,
            )
            st.session_state["all_growth1_image"] = growth_style1.render(**common_growth_kwargs)
            st.session_state["all_growth2_image"] = growth_style2.render(**common_growth_kwargs)
            st.session_state["all_regional_image"] = regional_style.render(
                market_name=market_name, country=country, currency=currency,
                base_year=int(base_year), forecast_year=int(forecast_year),
                base_value=start_value, forecast_value=end_value, unit=unit,
                website=website, logo_path=logo_path, background=background,
                font_regular=font_regular_path, font_bold=font_bold_path,
                width=width, height=height,
            )
            if len(filled_segments) >= 2:
                st.session_state["all_seg_image"] = segmentation_style.render(
                    market_name=market_name,
                    segments=[l for l, _ in filled_segments],
                    colors=[c for _, c in filled_segments],
                    website=website, background=background,
                    font_regular=font_regular_path, font_bold=font_bold_path,
                    width=width, height=height,
                )
            else:
                st.session_state.pop("all_seg_image", None)
        if len(filled_segments) < 2:
            st.warning("Segmentation: escribe al menos 2 segmentos con nombre para incluir esa imagen. Las otras 3 sí se generaron.")
        else:
            st.success("¡Listas! Las 4 imágenes se muestran abajo.")

    # ---- Results: every generated image, each with its own export controls ----
    if any(key in st.session_state for key, *_ in RESULT_SECTIONS):
        st.divider()
        st.subheader("Resultados")
        name_for_files = slugify_filename(market_name)
        for state_key, title, export_prefix, filename_fn in RESULT_SECTIONS:
            if state_key not in st.session_state:
                continue
            st.markdown(f"#### {title}")
            st.image(st.session_state[state_key], caption="Vista previa", width='stretch')
            _export_block(st.session_state[state_key], export_prefix, filename_fn(name_for_files))

        # ---- Download All (ZIP) ----
        st.divider()
        st.subheader("⬇️ Descargar Todo")
        available = [(k, t, f) for k, t, _, f in RESULT_SECTIONS if k in st.session_state]
        st.caption(
            "Selecciona qué imágenes incluir. Si eliges Style 1 y Style 2 juntos, sus archivos "
            "se numeran (-1 / -2) dentro del ZIP para no sobrescribirse entre sí."
        )
        zip_fmt_col, zip_q_col = st.columns([1, 1])
        with zip_fmt_col:
            zip_fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1, key="all_zip_fmt")
        with zip_q_col:
            zip_quality = st.slider("Calidad", 50, 100, 90, key="all_zip_quality")

        selected = []
        check_cols = st.columns(len(available))
        for i, (state_key, title, filename_fn) in enumerate(available):
            with check_cols[i]:
                if st.checkbox(title, value=True, key=f"all_zip_include_{state_key}"):
                    selected.append((state_key, filename_fn))

        if selected:
            # Number filenames that collide (both Growth styles share the
            # "cuota-del-..." base) instead of silently overwriting one
            # inside the zip.
            base_names = [filename_fn(name_for_files) for _, filename_fn in selected]
            dup_counts = {}
            for b in base_names:
                dup_counts[b] = dup_counts.get(b, 0) + 1
            seen = {}
            final_names = []
            for state_key, filename_fn in selected:
                base = filename_fn(name_for_files)
                if dup_counts[base] > 1:
                    seen[base] = seen.get(base, 0) + 1
                    final_names.append(f"{base}-{seen[base]}")
                else:
                    final_names.append(base)

            ext = file_extension_for(zip_fmt)
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for (state_key, _), base_name in zip(selected, final_names):
                    data = export_image(st.session_state[state_key], fmt=zip_fmt, quality=zip_quality)
                    zf.writestr(f"{base_name}.{ext}", data)
            st.download_button(
                "⬇️ Descargar Todo (ZIP)", data=zip_buf.getvalue(),
                file_name=f"{name_for_files}-imagenes.zip", mime="application/zip",
                width='stretch', key="all_zip_download_btn", type="primary",
            )
        else:
            st.info("Selecciona al menos una imagen para incluir en el ZIP.")


if __name__ == "__main__":
    render_page()
