"""
test_app.py
Headless smoke tests using Streamlit's AppTest framework: boots the app,
navigates each page, and clicks the "Generar Todas las Imágenes" button to
confirm all 4 templates render end-to-end with no exceptions.
"""

import io

from streamlit.testing.v1 import AppTest


def _build_sample_toc_docx() -> bytes:
    """Build a tiny in-memory .docx with a plain-text numbered TOC, so the
    TOC Formatter page can be exercised end-to-end (upload -> parse ->
    render) without needing a real report file on disk."""
    from docx import Document

    doc = Document()
    for line in [
        "1. Executive Summary",
        "2. Market Overview",
        "2.1. Market Definition",
        "2.2. Market Segmentation",
        "3. Competitive Landscape",
    ]:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def run_and_check(label, at):
    at.run(timeout=30)
    if at.exception:
        print(f"[{label}] EXCEPTION:", at.exception[0].message if hasattr(at.exception[0], 'message') else at.exception)
        for e in at.exception:
            print("   ", e)
        return False
    print(f"[{label}] OK - no exceptions")
    return True


def test_dashboard():
    at = AppTest.from_file("app.py")
    ok = run_and_check("Dashboard (default)", at)
    return ok


def test_generate_all_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🎨 Generar Imágenes").run(timeout=30)
    if at.exception:
        print("[Generate All nav] EXCEPTION:", at.exception)
        return False
    print("[Generate All nav] OK")

    buttons = [b for b in at.button if "Generar Todas las Imágenes" in (b.label or "")]
    if not buttons:
        print("[Generate All] Button not found")
        return False
    buttons[0].click().run(timeout=30)
    if at.exception:
        print("[Generate All] EXCEPTION:", at.exception)
        return False
    print("[Generate All] OK")

    # All 4 images should be present in session state after one click
    # (the default segment presets are pre-filled, so Segmentation also
    # has enough segments to render without extra input).
    expected_keys = ["all_growth1_image", "all_growth2_image", "all_regional_image", "all_seg_image"]
    missing = [k for k in expected_keys if k not in at.session_state]
    if missing:
        print(f"[Generate All] Missing generated images in session_state: {missing}")
        return False
    print("[Generate All] All 4 images generated OK")
    return True


def test_rd_description_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("📝 RD Description").run(timeout=30)
    if at.exception:
        print("[RD Description nav] EXCEPTION:", at.exception)
        return False
    print("[RD Description nav] OK")
    return True


def test_toc_formatter_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("📑 TOC Formatter").run(timeout=30)
    if at.exception:
        print("[TOC Formatter nav] EXCEPTION:", at.exception)
        return False
    print("[TOC Formatter nav] OK")

    # Functional check: actually upload a sample .docx and confirm it parses
    # and renders a TOC preview with no exceptions (not just that the page
    # loads) -- the whole point of this tool.
    docx_bytes = _build_sample_toc_docx()
    at.file_uploader(key="toc_single_upload").set_value(
        ("sample_toc.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    ).run(timeout=30)
    if at.exception:
        print("[TOC Formatter upload] EXCEPTION:", at.exception)
        return False
    markdown_html = " ".join(m.value for m in at.markdown)
    if "toc-preview" not in markdown_html or "Market Overview" not in markdown_html:
        print("[TOC Formatter upload] Expected TOC preview not found in rendered output")
        return False
    print("[TOC Formatter upload] OK - parsed and rendered sample TOC")
    return True


def test_settings_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("⚙️ Settings").run(timeout=30)
    if at.exception:
        print("[Settings nav] EXCEPTION:", at.exception)
        return False
    print("[Settings nav] OK")
    return True


def test_export_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("📤 Export").run(timeout=30)
    if at.exception:
        print("[Export nav] EXCEPTION:", at.exception)
        return False
    print("[Export nav] OK")
    return True


if __name__ == "__main__":
    results = {
        "dashboard": test_dashboard(),
        "generate_all": test_generate_all_page(),
        "rd_description": test_rd_description_page(),
        "toc_formatter": test_toc_formatter_page(),
        "settings": test_settings_page(),
        "export": test_export_page(),
    }
    print("\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    if all(results.values()):
        print("\nALL TESTS PASSED")
    else:
        print("\nSOME TESTS FAILED")
        exit(1)
