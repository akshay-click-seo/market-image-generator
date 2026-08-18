"""
test_app.py
Headless smoke tests using Streamlit's AppTest framework: boots the app,
navigates each page, and clicks the "Generar Todas las Imágenes" button to
confirm all 4 templates render end-to-end with no exceptions.
"""

from streamlit.testing.v1 import AppTest


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
