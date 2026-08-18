"""
sections/generate_all.py
Streamlit page: "Generate All" -- the market's core data (name, country,
currency, years, values, CAGR) plus segmentation info is entered ONCE on a
single page, and with a single click all four dashboard image templates
(Market Growth Style 1, Market Growth Style 2, Regional Analysis,
Segmentation) are generated together, each shown with its own export
controls right below it.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser import extract_from_text, generate_yearly_values, compute_cagr, extract_segments_from_text
from utils.export import export_image, file_extension_for
from utils.fonts import list_available_fonts, get_default_font_path
from utils.state import init_state, get_canvas_size
from utils.units import UNIT_LABELS
from utils.numfmt import es_number_input
from utils.map import find_country_feature
from templates import growth_style1, growth_style2, regional_style, segmentation_style
from templates.segmentation_style import DEFAULT_PALETTE


COUNTRY_OPTIONS = [
    "Global", "México", "United States", "Brazil", "India", "China", "Germany", "United Kingdom",
    "France", "Japan", "South Korea", "Canada", "Australia", "Spain", "Italy",
    "Indonesia", "Saudi Arabia", "South Africa", "Argentina", "Nigeria", "Egypt",
]

PRESET_SEGMENT_LABELS = [
    "Por Tipo de Producto", "Por Aplicación", "Por Fuente",
    "Por Canal de Distribución", "Por Región", "Por Usuario Final",
]

RESULT_SECTIONS = [
    ("all_growth1_image", "📈 Market Growth — Style 1", "all_g1", "growth_style1"),
    ("all_growth2_image", "📈 Market Growth — Style 2", "all_g2", "growth_style2"),
    ("all_regional_image", "🗺️ Regional Analysis", "all_reg", "regional"),
    ("all_seg_image", "🍩 Segmentation", "all_seg", "segmentation"),
]


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
            st.session_state["all_start_value"] = extracted.start_value or 0.0
            st.session_state["all_end_value"] = extracted.end_value or 0.0
            st.session_state["all_base_year"] = extracted.base_year or 2025
            st.session_state["all_forecast_year"] = extracted.forecast_year or 2035
            st.session_state["all_cagr"] = extracted.cagr or 0.0
            st.session_state["all_currency"] = extracted.currency or "USD"
            st.session_state["all_unit"] = extracted.unit or "Millones"
            st.success(
                f"Extraído: {extracted.currency} {extracted.start_value} ({extracted.base_year}) → "
                f"{extracted.currency} {extracted.end_value} ({extracted.forecast_year}), "
                f"CAGR {extracted.cagr}%"
            )

    st.subheader("Datos del Mercado")
    st.caption("Estos campos alimentan Growth Style 1, Growth Style 2 y Regional Analysis.")
    c1, c2, c3 = st.columns(3)
    with c1:
        market_name = st.text_input(
            "Market Name", value=st.session_state.get("all_market_name", "Clonación de Voz"), key="all_market_name_input"
        )
        default_country = st.session_state.get("all_country", "Global")
        country_idx = COUNTRY_OPTIONS.index(default_country) if default_country in COUNTRY_OPTIONS else 0
        country = st.selectbox("Country", COUNTRY_OPTIONS, index=country_idx, key="all_country_select")
        custom_country = st.text_input("...o escribe un país personalizado (opcional)", value="", key="all_country_custom")
        if custom_country.strip():
            country = custom_country.strip()
        currency = st.selectbox(
            "Currency", ["USD", "EUR", "INR", "GBP", "JPY", "CNY"],
            index=["USD", "EUR", "INR", "GBP", "JPY", "CNY"].index(st.session_state.get("all_currency", "USD")),
            key="all_currency_select",
        )
    with c2:
        base_year = st.number_input("Base Year", value=int(st.session_state.get("all_base_year", 2025)), step=1, key="all_base_year_input")
        forecast_year = st.number_input("Forecast Year", value=int(st.session_state.get("all_forecast_year", 2035)), step=1, key="all_forecast_year_input")
        default_unit = st.session_state.get("all_unit", "Millones")
        unit_index = UNIT_LABELS.index(default_unit) if default_unit in UNIT_LABELS else UNIT_LABELS.index("Millones")
        unit = st.selectbox("Unit", UNIT_LABELS, index=unit_index, key="all_unit_select")
    with c3:
        start_value = es_number_input(st, "Start Value", value=float(st.session_state.get("all_start_value", 2.4)), key="all_start_value_input")
        end_value = es_number_input(st, "End Value", value=float(st.session_state.get("all_end_value", 29.8)), key="all_end_value_input")
        cagr_input = es_number_input(st, "CAGR (%)", value=float(st.session_state.get("all_cagr", 25.8)), key="all_cagr_input")

    if country.strip().lower() != "global":
        feature = find_country_feature(country)
        if feature:
            st.success(f"✅ País reconocido: {feature['properties'].get('NAME')} — el mapa de Regional Analysis se resaltará automáticamente.")
        else:
            st.warning("⚠️ País no reconocido en la base de datos del mapa mundial (solo afecta a Regional Analysis).")
    else:
        st.caption("ℹ️ Con Country = 'Global', el mapa de Regional Analysis no resaltará ningún país en particular.")

    num_years = int(forecast_year) - int(base_year)
    years = list(range(int(base_year), int(forecast_year) + 1))

    # Prefer the CAGR implied by Start -> End so the bar-by-bar curve always
    # traces a real growth path between the two stated values (same logic
    # as the original Market Growth page).
    effective_growth_cagr = compute_cagr(start_value, end_value, num_years)
    if effective_growth_cagr is None:
        effective_growth_cagr = cagr_input
    values = generate_yearly_values(start_value, effective_growth_cagr, num_years)
    if values:
        values[-1] = end_value
    if len(values) != len(years):
        if len(values) < len(years):
            values += [values[-1] if values else 0] * (len(years) - len(values))
        else:
            values = values[:len(years)]
    computed_cagr = compute_cagr(start_value, end_value, num_years) or cagr_input

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
        st.session_state["all_market_name"] = market_name
        st.session_state["all_country"] = country
        st.session_state["all_currency"] = currency
        st.session_state["all_base_year"] = int(base_year)
        st.session_state["all_forecast_year"] = int(forecast_year)
        st.session_state["all_start_value"] = start_value
        st.session_state["all_end_value"] = end_value
        st.session_state["all_cagr"] = cagr_input
        st.session_state["all_unit"] = unit

        with st.spinner("Generando las 4 imágenes..."):
            common_growth_kwargs = dict(
                market_name=market_name, country=country, currency=currency,
                base_year=int(base_year), forecast_year=int(forecast_year),
                start_value=start_value, end_value=end_value, cagr=computed_cagr,
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
        name_for_files = st.session_state.get("all_market_name", market_name).replace(" ", "_")
        for state_key, title, export_prefix, filename_prefix in RESULT_SECTIONS:
            if state_key not in st.session_state:
                continue
            st.markdown(f"#### {title}")
            st.image(st.session_state[state_key], caption="Vista previa", width='stretch')
            _export_block(st.session_state[state_key], export_prefix, f"{filename_prefix}_{name_for_files}")


if __name__ == "__main__":
    render_page()
