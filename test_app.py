"""
test_app.py
Headless smoke tests using Streamlit's AppTest framework: boots the app,
navigates each page, and clicks the "Generar Imagen" button to confirm
no exceptions are raised end-to-end.
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


def test_growth_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("📈 Market Growth").run(timeout=30)
    ok1 = not at.exception
    if not ok1:
        print("[Growth nav] EXCEPTION:", at.exception)
        return False
    print("[Growth nav] OK")

    # click "Generar Imagen"
    buttons = [b for b in at.button if "Generar Imagen" in (b.label or "")]
    if not buttons:
        print("[Growth generate] Button not found")
        return False
    buttons[0].click().run(timeout=30)
    if at.exception:
        print("[Growth generate] EXCEPTION:", at.exception)
        return False
    print("[Growth generate] OK")
    return True


def test_regional_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🗺️ Regional Analysis").run(timeout=30)
    if at.exception:
        print("[Regional nav] EXCEPTION:", at.exception)
        return False
    print("[Regional nav] OK")

    buttons = [b for b in at.button if "Generar Imagen" in (b.label or "")]
    if not buttons:
        print("[Regional generate] Button not found")
        return False
    buttons[0].click().run(timeout=30)
    if at.exception:
        print("[Regional generate] EXCEPTION:", at.exception)
        return False
    print("[Regional generate] OK")
    return True


def test_segmentation_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🍩 Segmentation").run(timeout=30)
    if at.exception:
        print("[Segmentation nav] EXCEPTION:", at.exception)
        return False
    print("[Segmentation nav] OK")

    buttons = [b for b in at.button if "Generar Imagen" in (b.label or "")]
    if not buttons:
        print("[Segmentation generate] Button not found")
        return False
    buttons[0].click().run(timeout=30)
    if at.exception:
        print("[Segmentation generate] EXCEPTION:", at.exception)
        return False
    print("[Segmentation generate] OK")
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
        "growth": test_growth_page(),
        "regional": test_regional_page(),
        "segmentation": test_segmentation_page(),
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
