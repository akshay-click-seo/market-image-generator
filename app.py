"""
app.py
Market Image Generator — main Streamlit application shell.

Navigation: Dashboard / Market Growth / Regional Analysis / Segmentation /
Settings / Export. Run with:  streamlit run app.py
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.state import init_state, get_canvas_size
from utils.fonts import list_available_fonts, save_custom_font
from utils.backgrounds import list_preset_names
from utils.export import SIZE_PRESETS, export_image, file_extension_for


st.set_page_config(
    page_title="Market Image Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()


def sidebar_nav():
    st.sidebar.title("📊 Market Image Generator")
    st.sidebar.caption("Automatiza tus dashboards de mercado estilo Informes de Expertos")
    page = st.sidebar.radio(
        "Navegación",
        ["🏠 Dashboard", "📈 Market Growth", "🗺️ Regional Analysis", "🍩 Segmentation", "⚙️ Settings", "📤 Export"],
    )
    st.sidebar.divider()
    st.sidebar.caption("v1.0 · Regex-based auto-extraction · Sin dependencias de red")
    return page


def page_dashboard():
    st.title("🏠 Dashboard")
    st.write(
        "Bienvenido al **Market Image Generator** — una herramienta para crear imágenes de "
        "reportes de mercado (tamaño de mercado, análisis regional, segmentación) en el "
        "estilo visual de Informes de Expertos / IMARC."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📈 Market Growth")
        st.write("Gráfico de barras con CAGR, tarjetas de estadísticas, dos estilos disponibles.")
        if st.button("Ir a Market Growth →", width='stretch'):
            st.session_state["_nav_override"] = "📈 Market Growth"
            st.rerun()
    with col2:
        st.subheader("🗺️ Regional Analysis")
        st.write("Mapa mundial con país destacado automáticamente, bandera y pin.")
        if st.button("Ir a Regional Analysis →", width='stretch'):
            st.session_state["_nav_override"] = "🗺️ Regional Analysis"
            st.rerun()
    with col3:
        st.subheader("🍩 Segmentation")
        st.write("Gráfico de dona con 2 a 6 segmentos, colores y líneas conectoras automáticas.")
        if st.button("Ir a Segmentation →", width='stretch'):
            st.session_state["_nav_override"] = "🍩 Segmentation"
            st.rerun()

    st.divider()
    st.subheader("Cómo funciona el Auto Fetch")
    st.write(
        "Pega un párrafo de un reporte (estilo IMARC / Informes de Expertos) en el cuadro de "
        "'Auto Fetch' dentro de Market Growth, y la herramienta extraerá automáticamente el "
        "año base, año de pronóstico, valores de mercado, CAGR y moneda usando expresiones "
        "regulares — sin necesidad de conexión a internet o IA externa."
    )
    st.code(
        "The market reached USD 145 Million in 2025 and is expected to reach USD 367.3 "
        "Million by 2035 growing at a CAGR of 9.74% during 2026-2035.",
        language="text",
    )


def page_settings():
    st.title("⚙️ Settings")

    st.subheader("Background")
    bg_names = list_preset_names()
    current_bg = st.session_state.get("settings_background", "Classic Blue")
    idx = bg_names.index(current_bg) if current_bg in bg_names else 0
    st.session_state["settings_background"] = st.selectbox("Estilo de fondo por defecto", bg_names, index=idx)

    st.subheader("Fonts")
    fonts = list_available_fonts()
    st.write("Fuentes disponibles actualmente:")
    st.write(", ".join(fonts.keys()) if fonts else "Ninguna")

    uploaded_font = st.file_uploader("Subir fuente personalizada (TTF/OTF)", type=["ttf", "otf"])
    if uploaded_font is not None:
        path = save_custom_font(uploaded_font.getvalue(), uploaded_font.name)
        st.success(f"Fuente guardada: {os.path.basename(path)}")

    st.subheader("Logo & Website")
    st.session_state["settings_website"] = st.text_input(
        "Website por defecto", value=st.session_state.get("settings_website", "www.informesdeexpertos.com")
    )

    st.subheader("Image Size")
    size_names = list(SIZE_PRESETS.keys()) + ["Custom"]
    current_size = st.session_state.get("settings_size_preset", "1600 x 900 (Widescreen)")
    idx2 = size_names.index(current_size) if current_size in size_names else 0
    st.session_state["settings_size_preset"] = st.selectbox("Tamaño de imagen", size_names, index=idx2)

    if st.session_state["settings_size_preset"] == "Custom":
        c1, c2 = st.columns(2)
        with c1:
            st.session_state["settings_custom_width"] = st.number_input(
                "Width", value=int(st.session_state.get("settings_custom_width", 1600)), step=50
            )
        with c2:
            st.session_state["settings_custom_height"] = st.number_input(
                "Height", value=int(st.session_state.get("settings_custom_height", 900)), step=50
            )

    w, h = get_canvas_size()
    st.info(f"Tamaño de lienzo actual: **{w} × {h} px**")


def page_export():
    st.title("📤 Export")
    st.write("Exporta la última imagen generada en cualquiera de las páginas (Market Growth, Regional Analysis, Segmentation).")

    options = {}
    if "growth_last_image" in st.session_state:
        options["Market Growth"] = st.session_state["growth_last_image"]
    if "regional_last_image" in st.session_state:
        options["Regional Analysis"] = st.session_state["regional_last_image"]
    if "seg_last_image" in st.session_state:
        options["Segmentation"] = st.session_state["seg_last_image"]

    if not options:
        st.warning("Aún no has generado ninguna imagen. Ve a una de las páginas de generación primero.")
        return

    choice = st.selectbox("Selecciona la imagen a exportar", list(options.keys()))
    img = options[choice]
    st.image(img, width='stretch')

    col1, col2, col3 = st.columns(3)
    with col1:
        fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1)
    with col2:
        quality = st.slider("Calidad", 50, 100, 90)
    data = export_image(img, fmt=fmt, quality=quality)
    ext = file_extension_for(fmt)
    with col3:
        st.download_button(
            "⬇️ Descargar", data=data, file_name=f"{choice.lower().replace(' ', '_')}.{ext}",
            mime=f"image/{ext}" if fmt != "PDF" else "application/pdf",
            width='stretch',
        )


def main():
    default_page = st.session_state.pop("_nav_override", None)
    page = sidebar_nav() if default_page is None else default_page

    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📈 Market Growth":
        from sections import growth
        growth.render_page()
    elif page == "🗺️ Regional Analysis":
        from sections import regional
        regional.render_page()
    elif page == "🍩 Segmentation":
        from sections import segmentation
        segmentation.render_page()
    elif page == "⚙️ Settings":
        page_settings()
    elif page == "📤 Export":
        page_export()


if __name__ == "__main__":
    main()
