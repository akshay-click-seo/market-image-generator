"""
pages/growth.py
Streamlit page: "Market Growth" image generator.
Manual fields + Auto-Fetch paste box (regex extraction) + Style 1/Style 2
toggle + auto-calculate-from-CAGR or custom yearly values + live preview
+ export.
"""

import os
import sys
import io

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser import extract_from_text, generate_yearly_values, compute_cagr
from utils.export import export_image, file_extension_for
from utils.fonts import list_available_fonts, get_default_font_path
from utils.state import init_state, get_canvas_size
from utils.units import UNIT_LABELS
from utils.numfmt import es_number_input
from templates import growth_style1, growth_style2


def render_page():
    init_state()
    st.header("📈 Market Growth Image")
    st.caption("Genera una imagen de tamaño de mercado y pronóstico de CAGR, estilo Informes de Expertos.")

    template_choice = st.radio("Template", ["Style 1 (Bar chart + stat cards)", "Style 2 (Minimal + world map)"], horizontal=True)

    with st.expander("📋 Auto Fetch — Pega un párrafo de reporte (IMARC / IDE)", expanded=True):
        pasted_text = st.text_area(
            "Special Paste Box",
            placeholder=(
                "The market reached USD 145 Million in 2025 and is expected to reach "
                "USD 367.3 Million by 2035 growing at a CAGR of 9.74% during 2026-2035."
            ),
            height=100,
        )
        col_a, col_b = st.columns([1, 3])
        with col_a:
            do_extract = st.button("🔍 Extraer datos", width='stretch')

        if do_extract and pasted_text.strip():
            extracted = extract_from_text(pasted_text)
            st.session_state["growth_start_value"] = extracted.start_value or 0.0
            st.session_state["growth_end_value"] = extracted.end_value or 0.0
            st.session_state["growth_base_year"] = extracted.base_year or 2025
            st.session_state["growth_forecast_year"] = extracted.forecast_year or 2035
            st.session_state["growth_cagr"] = extracted.cagr or 0.0
            st.session_state["growth_currency"] = extracted.currency or "USD"
            st.session_state["growth_unit"] = extracted.unit or "Millones"
            st.success(
                f"Extraído: {extracted.currency} {extracted.start_value} ({extracted.base_year}) → "
                f"{extracted.currency} {extracted.end_value} ({extracted.forecast_year}), "
                f"CAGR {extracted.cagr}%, {extracted.forecast_period}"
            )

    st.subheader("Campos Manuales")
    c1, c2, c3 = st.columns(3)
    with c1:
        market_name = st.text_input("Market Name", value=st.session_state.get("growth_market_name", "Clonación de Voz"))
        country = st.text_input("Country", value=st.session_state.get("growth_country", "Global"))
        currency = st.selectbox("Currency", ["USD", "EUR", "INR", "GBP", "JPY", "CNY"],
                                 index=["USD", "EUR", "INR", "GBP", "JPY", "CNY"].index(st.session_state.get("growth_currency", "USD")))
    with c2:
        base_year = st.number_input("Base Year", value=int(st.session_state.get("growth_base_year", 2025)), step=1)
        forecast_year = st.number_input("Forecast Year", value=int(st.session_state.get("growth_forecast_year", 2036)), step=1)
        default_unit = st.session_state.get("growth_unit", "Millones")
        unit_index = UNIT_LABELS.index(default_unit) if default_unit in UNIT_LABELS else UNIT_LABELS.index("Millones")
        unit = st.selectbox("Unit", UNIT_LABELS, index=unit_index)
    with c3:
        start_value = es_number_input(st, "Start Value", value=float(st.session_state.get("growth_start_value", 2.4)))
        end_value = es_number_input(st, "End Value", value=float(st.session_state.get("growth_end_value", 29.8)))
        cagr_input = es_number_input(st, "CAGR (%)", value=float(st.session_state.get("growth_cagr", 25.8)))

    col_logo, col_web = st.columns(2)
    with col_logo:
        logo_file = st.file_uploader("Logo (optional)", type=["png", "jpg", "jpeg"])
    with col_web:
        website = st.text_input("Website", value=st.session_state.get("settings_website", "www.informesdeexpertos.com"))

    st.subheader("Gráfico")
    graph_mode = st.radio("Modo de valores anuales", ["Auto Calculate Bars using CAGR", "Custom yearly values"], horizontal=True)

    num_years = int(forecast_year) - int(base_year)
    years = list(range(int(base_year), int(forecast_year) + 1))

    if graph_mode == "Auto Calculate Bars using CAGR":
        values = generate_yearly_values(start_value, cagr_input, num_years)
        if values:
            values[-1] = end_value  # ensure the final bar matches the stated end value
    else:
        default_csv = ", ".join(str(v) for v in generate_yearly_values(start_value, cagr_input, num_years))
        custom_csv = st.text_input(f"Valores anuales separados por coma ({len(years)} años: {years[0]}-{years[-1]})", value=default_csv)
        try:
            values = [float(v.strip()) for v in custom_csv.split(",")]
        except ValueError:
            st.error("No se pudieron interpretar los valores. Usa números separados por coma.")
            values = generate_yearly_values(start_value, cagr_input, num_years)

    if len(values) != len(years):
        st.warning(f"Se esperaban {len(years)} valores pero se recibieron {len(values)}. Ajustando automáticamente.")
        if len(values) < len(years):
            values += [values[-1] if values else 0] * (len(years) - len(values))
        else:
            values = values[:len(years)]

    computed_cagr = compute_cagr(start_value, end_value, num_years) or cagr_input

    # ---- Settings shortcuts (background / font) ----
    st.subheader("Estilo")
    col_bg, col_font = st.columns(2)
    with col_bg:
        background = st.selectbox(
            "Background", ["Classic Blue", "Modern White", "Gradient", "Light", "Dark"],
            index=["Classic Blue", "Modern White", "Gradient", "Light", "Dark"].index(
                st.session_state.get("settings_background", "Classic Blue")
                if st.session_state.get("settings_background", "Classic Blue") in ["Classic Blue", "Modern White", "Gradient", "Light", "Dark"]
                else "Classic Blue"
            ),
        )
    with col_font:
        fonts = list_available_fonts()
        font_names = list(fonts.keys()) or ["Poppins Regular"]
        font_choice = st.selectbox("Font", font_names, index=0)

    width, height = get_canvas_size()

    logo_path = None
    if logo_file is not None:
        logo_path = f"/tmp/_uploaded_logo_{logo_file.name}"
        with open(logo_path, "wb") as f:
            f.write(logo_file.getvalue())

    font_bold_path = fonts.get("Poppins Bold", get_default_font_path("Bold"))
    font_regular_path = fonts.get(font_choice, get_default_font_path("Regular"))

    if st.button("🎨 Generar Imagen", type="primary", width='stretch'):
        renderer = growth_style1 if template_choice.startswith("Style 1") else growth_style2
        img = renderer.render(
            market_name=market_name,
            country=country,
            currency=currency,
            base_year=int(base_year),
            forecast_year=int(forecast_year),
            start_value=start_value,
            end_value=end_value,
            cagr=computed_cagr,
            years=years,
            values=values,
            unit=unit,
            website=website,
            logo_path=logo_path,
            background=background,
            font_regular=font_regular_path,
            font_bold=font_bold_path,
            width=width,
            height=height,
        )
        st.session_state["growth_last_image"] = img
        st.session_state["growth_market_name"] = market_name
        st.session_state["growth_country"] = country

    if "growth_last_image" in st.session_state:
        img = st.session_state["growth_last_image"]
        st.image(img, caption="Vista previa", width='stretch')

        st.subheader("Export")
        col_fmt, col_q, col_dl = st.columns([1, 1, 1])
        with col_fmt:
            fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1)
        with col_q:
            quality = st.slider("Calidad", 50, 100, 90)
        data = export_image(img, fmt=fmt, quality=quality)
        ext = file_extension_for(fmt)
        with col_dl:
            st.download_button(
                "⬇️ Descargar", data=data, file_name=f"market_growth_{market_name.replace(' ', '_')}.{ext}",
                mime=f"image/{ext}" if fmt != "PDF" else "application/pdf",
                width='stretch',
            )


if __name__ == "__main__":
    render_page()
