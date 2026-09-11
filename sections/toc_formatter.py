"""
toc_formatter.py
"TOC Formatter" page: embeds the standalone TOC Formatter Tool (originally
its own separate Streamlit app, at github.com/akshay-click-seo/toc-formatter-
tool) as its own menu item here. The tool's own parsing/rendering logic
(toc_tool/formatter.py + toc_tool/docx_io.py, copied over unmodified apart
from one renamed internal import) is used exactly as-is -- this file only
adapts the UI layer to fit as ONE PAGE inside this app's existing
single-sidebar-navigated shell, since the original tool was a full standalone
app of its own (its own st.set_page_config, its own sidebar):
  - st.set_page_config is dropped (this app already calls it once, in its
    own app.py).
  - The tool's own sidebar controls (Mode / Output format / numbering-style
    help) are moved into the page body instead, so they don't stack
    underneath this app's own navigation sidebar.
  - The original tool's `.stApp` dark-theme override is dropped -- applying
    it here would flip this whole app's chrome (including the shared
    sidebar) to dark while on just this one page. The monospace preview
    card's own dark styling is kept, since that's just a code/text-preview
    look, independent of the surrounding page's theme.
Everything else -- single-file mode, batch mode, txt/md/json export, and the
numbering-detection engine itself -- behaves exactly as in the standalone
tool.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from toc_tool import docx_io


FORMAT_LABELS = {
    "txt": "📄 Plain Text (.txt)",
    "md": "📝 Markdown (.md)",
    "json": "📊 JSON (.json)",
}

_PREVIEW_CSS = """
<style>
.toc-preview {
    background-color: #161a23;
    border: 1px solid #2a2f3a;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.92rem;
    white-space: pre-wrap;
    color: #e6e6e6;
    max-height: 620px;
    overflow-y: auto;
}
</style>
"""


def _render_single_file(fmt):
    uploaded = st.file_uploader("Sube un archivo .docx", type=["docx"], key="toc_single_upload")

    if uploaded is None:
        st.info("👆 Sube un archivo .docx para comenzar.")
        return

    try:
        with st.spinner("Leyendo y formateando TOC..."):
            entries, rendered = docx_io.docx_to_result(uploaded, fmt=fmt)
    except Exception as exc:
        st.error(f"No se pudo procesar este archivo: {exc}")
        return

    if not entries:
        st.warning(
            "No se detectaron líneas numeradas/tipo TOC en este documento. "
            "Asegúrate de que el archivo contenga una sección de Tabla de Contenidos."
        )
        return

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Vista Previa")
        st.markdown(f'<div class="toc-preview">{rendered}</div>', unsafe_allow_html=True)
    with col2:
        st.subheader("Resumen")
        st.metric("Entradas detectadas", len(entries))
        st.metric("Profundidad máxima", max(e.level for e in entries))
        st.dataframe(
            [{"Nivel": e.level, "Número": e.number, "Título": e.title} for e in entries],
            width="stretch",
            height=420,
        )

    ext = {"txt": "txt", "md": "md", "json": "json"}[fmt]
    base_name = uploaded.name.rsplit(".", 1)[0]
    st.download_button(
        label=f"⬇️ Descargar {ext.upper()}",
        data=rendered,
        file_name=f"{base_name}_formatted.{ext}",
        mime="text/plain",
        width="stretch",
    )


def _render_batch(fmt):
    st.subheader("Procesamiento por Lotes")
    st.caption("Sube hasta ~1000 archivos DOCX. Conviértelos todos en un clic y descarga un solo ZIP.")

    uploaded_files = st.file_uploader(
        "Sube varios archivos .docx", type=["docx"], accept_multiple_files=True, key="toc_batch_upload",
    )

    if not uploaded_files:
        st.info("👆 Sube varios archivos .docx para comenzar.")
        return

    st.write(f"**{len(uploaded_files)}** archivo(s) listo(s).")
    convert_clicked = st.button("🚀 Convertir Todos", type="primary", width="stretch")

    if not convert_clicked:
        return

    progress_bar = st.progress(0, text="Iniciando conversión por lotes...")
    status_placeholder = st.empty()

    def _on_progress(done, total, current_name):
        progress_bar.progress(done / total, text=f"Procesando {done}/{total}: {current_name}")

    results = docx_io.batch_process(uploaded_files, fmt=fmt, progress_callback=_on_progress)
    progress_bar.progress(1.0, text="¡Listo!")

    n_ok = sum(1 for r in results if not r["error"])
    n_err = len(results) - n_ok
    status_placeholder.success(f"✅ {n_ok} archivo(s) convertido(s) con éxito.")
    if n_err:
        st.error(f"⚠️ {n_err} archivo(s) fallaron:")
        for r in results:
            if r["error"]:
                st.write(f"- **{r['filename']}**: {r['error']}")

    with st.expander("Vista previa de resultados individuales"):
        for r in results:
            if r["error"]:
                continue
            st.markdown(f"**{r['output_name']}**")
            st.markdown(f'<div class="toc-preview">{r["rendered"]}</div>', unsafe_allow_html=True)

    zip_bytes = docx_io.results_to_zip_bytes(results)
    st.download_button(
        label="⬇️ Descargar Todo como ZIP",
        data=zip_bytes,
        file_name="toc_formatted_batch.zip",
        mime="application/zip",
        width="stretch",
    )


def render_page():
    st.title("📑 TOC Formatter")
    st.caption(
        "Sube archivos DOCX, detecta automáticamente la numeración (estilo antiguo o "
        "nuevo), y exporta una Tabla de Contenidos limpia y consistentemente indentada."
    )
    st.markdown(_PREVIEW_CSS, unsafe_allow_html=True)

    col_mode, col_fmt = st.columns([2, 1])
    with col_mode:
        mode = st.radio(
            "Modo", ["Single File", "Batch Processing"], index=0, horizontal=True, key="toc_mode",
        )
    with col_fmt:
        fmt = st.selectbox(
            "Formato de salida", options=list(FORMAT_LABELS.keys()),
            format_func=lambda k: FORMAT_LABELS[k], key="toc_fmt",
        )
    with st.expander("Estilos de numeración soportados"):
        st.markdown(
            "- Decimal moderno: `1.` `1.1.` `5.4.1.3.1.`\n"
            "- Esquema legado: `A.` `a.` `i.` `1.`\n"
            "- Se convierte automáticamente a numeración decimal limpia, siempre."
        )
    st.divider()

    if mode == "Single File":
        _render_single_file(fmt)
    else:
        _render_batch(fmt)
