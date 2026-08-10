"""
pages/regional.py
Streamlit page: "Regional Analysis" image generator.
Manual fields (country, market name, base/forecast value) + auto flag/pin/
highlight on world map + live preview + export.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.map import find_country_feature
from utils.export import export_image, file_extension_for
from utils.fonts import list_available_fonts, get_default_font_path
from utils.state import init_state, get_canvas_size
from utils.units import UNIT_LABELS
from templates import regional_style


COUNTRY_OPTIONS = [
    "México", "United States", "Brazil", "India", "China", "Germany", "United Kingdom",
    "France", "Japan", "South Korea", "Canada", "Australia", "Spain", "Italy",
    "Indonesia", "Saudi Arabia", "South Africa", "Argentina", "Nigeria", "Egypt",
]


def render_page():
    init_state()
    st.header("🗺️ Regional Analysis Image")
    st.caption("Genera una imagen de análisis regional con mapa mundial y país destacado.")

    st.subheader("Campos Manuales")
    c1, c2 = st.columns(2)
    with c1:
        market_name = st.text_input("Market Name", value=st.session_state.get("regional_market_name", "Proteína de Origen Vegetal"))
        country = st.selectbox("Country", COUNTRY_OPTIONS, index=0)
        custom_country = st.text_input("...o escribe un país personalizado (opcional)", value="")
        if custom_country.strip():
            country = custom_country.strip()
    with c2:
        currency = st.selectbox("Currency", ["USD", "EUR", "INR", "GBP", "JPY", "CNY"])
        base_year = st.number_input("Base Year", value=2025, step=1)
        forecast_year = st.number_input("Forecast Year", value=2035, step=1)

    c3, c4 = st.columns(2)
    with c3:
        base_value = st.number_input("Base Value", value=145.0, format="%.2f")
    with c4:
        forecast_value = st.number_input("Forecast Value", value=223.5, format="%.2f")

    unit = st.selectbox("Unit", UNIT_LABELS, index=UNIT_LABELS.index("Millones"))

    # ---- Auto: flag / pin / highlight preview ----
    feature = find_country_feature(country)
    if feature:
        props = feature["properties"]
        st.success(f"✅ País reconocido: {props.get('NAME')} (ISO {props.get('ISO_A2')}) — el mapa se resaltará automáticamente.")
    else:
        st.warning("⚠️ País no reconocido en la base de datos del mapa mundial. Verifica el nombre.")

    col_logo, col_web = st.columns(2)
    with col_logo:
        logo_file = st.file_uploader("Logo (optional)", type=["png", "jpg", "jpeg"])
    with col_web:
        website = st.text_input("Website", value=st.session_state.get("settings_website", "www.informesdeexpertos.com"))

    background = st.selectbox("Background", ["Light", "Classic Blue", "Modern White", "Gradient", "Dark"])
    fonts = list_available_fonts()
    font_bold_path = fonts.get("Poppins Bold", get_default_font_path("Bold"))
    font_regular_path = fonts.get("Poppins Regular", get_default_font_path("Regular"))

    width, height = get_canvas_size()

    logo_path = None
    if logo_file is not None:
        logo_path = f"/tmp/_uploaded_logo_{logo_file.name}"
        with open(logo_path, "wb") as f:
            f.write(logo_file.getvalue())

    if st.button("🎨 Generar Imagen", type="primary", width='stretch'):
        img = regional_style.render(
            market_name=market_name,
            country=country,
            currency=currency,
            base_year=int(base_year),
            forecast_year=int(forecast_year),
            base_value=base_value,
            forecast_value=forecast_value,
            unit=unit,
            website=website,
            logo_path=logo_path,
            background=background,
            font_regular=font_regular_path,
            font_bold=font_bold_path,
            width=width,
            height=height,
        )
        st.session_state["regional_last_image"] = img
        st.session_state["regional_market_name"] = market_name

    if "regional_last_image" in st.session_state:
        img = st.session_state["regional_last_image"]
        st.image(img, caption="Vista previa", width='stretch')

        st.subheader("Export")
        col_fmt, col_q, col_dl = st.columns([1, 1, 1])
        with col_fmt:
            fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1, key="regional_fmt")
        with col_q:
            quality = st.slider("Calidad", 50, 100, 90, key="regional_quality")
        data = export_image(img, fmt=fmt, quality=quality)
        ext = file_extension_for(fmt)
        with col_dl:
            st.download_button(
                "⬇️ Descargar", data=data, file_name=f"regional_{market_name.replace(' ', '_')}.{ext}",
                mime=f"image/{ext}" if fmt != "PDF" else "application/pdf",
                width='stretch',
            )


if __name__ == "__main__":
    render_page()
