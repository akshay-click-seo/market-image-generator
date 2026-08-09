"""
pages/segmentation.py
Streamlit page: "Segmentation" donut chart image generator.
Segment count selector (2-6) + segment name inputs + auto colors/labels/
connector lines + live preview + export.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.export import export_image, file_extension_for
from utils.fonts import list_available_fonts, get_default_font_path
from utils.state import init_state, get_canvas_size
from templates import segmentation_style
from templates.segmentation_style import DEFAULT_PALETTE


PRESET_LABELS = [
    "Por Tipo de Producto", "Por Aplicación", "Por Fuente",
    "Por Canal de Distribución", "Por Región", "Por Usuario Final",
]


def render_page():
    init_state()
    st.header("🍩 Segmentation Image")
    st.caption("Genera un gráfico de dona con la segmentación del mercado.")

    market_name = st.text_input("Market Name", value=st.session_state.get("seg_market_name", "Proteína de Origen Vegetal en México"))

    n_segments = st.select_slider("Número de segmentos", options=[2, 3, 4, 5, 6], value=5)

    st.subheader("Segmentos")
    labels = []
    colors = []
    cols = st.columns(2)
    for i in range(n_segments):
        col = cols[i % 2]
        with col:
            default_label = PRESET_LABELS[i] if i < len(PRESET_LABELS) else f"Segmento {i + 1}"
            label = st.text_input(f"Segmento {i + 1}", value=default_label, key=f"seg_label_{i}")
            color = st.color_picker(f"Color {i + 1}", value=DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)], key=f"seg_color_{i}")
            labels.append(label)
            colors.append(color)

    col_logo, col_web = st.columns(2)
    with col_logo:
        logo_file = st.file_uploader("Logo (optional)", type=["png", "jpg", "jpeg"])
    with col_web:
        website = st.text_input("Website", value=st.session_state.get("settings_website", "www.informesdeexpertos.com"))

    background = st.selectbox("Background", ["Gradient", "Classic Blue", "Modern White", "Light", "Dark"])
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
        img = segmentation_style.render(
            market_name=market_name,
            segments=labels,
            colors=colors,
            website=website,
            logo_path=logo_path,
            background=background,
            font_regular=font_regular_path,
            font_bold=font_bold_path,
            width=width,
            height=height,
        )
        st.session_state["seg_last_image"] = img
        st.session_state["seg_market_name"] = market_name

    if "seg_last_image" in st.session_state:
        img = st.session_state["seg_last_image"]
        st.image(img, caption="Vista previa", width='stretch')

        st.subheader("Export")
        col_fmt, col_q, col_dl = st.columns([1, 1, 1])
        with col_fmt:
            fmt = st.selectbox("Formato", ["PNG", "WEBP", "JPG", "PDF"], index=1, key="seg_fmt")
        with col_q:
            quality = st.slider("Calidad", 50, 100, 90, key="seg_quality")
        data = export_image(img, fmt=fmt, quality=quality)
        ext = file_extension_for(fmt)
        with col_dl:
            st.download_button(
                "⬇️ Descargar", data=data, file_name=f"segmentation_{market_name.replace(' ', '_')}.{ext}",
                mime=f"image/{ext}" if fmt != "PDF" else "application/pdf",
                width='stretch',
            )


if __name__ == "__main__":
    render_page()
