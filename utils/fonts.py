"""
fonts.py
Font management: bundled default fonts (Poppins family, matching the
sample dashboard typography) + custom TTF upload support.

Google Font "live download" is intentionally NOT implemented (network
dependency) -- instead we ship the Poppins family directly under
assets/fonts/ so the tool works fully offline out of the box. Users can
still drop in any TTF via the Settings page (custom upload).
"""

import os
import shutil

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
CUSTOM_FONTS_DIR = os.path.join(ASSETS_DIR, "fonts", "custom")
os.makedirs(CUSTOM_FONTS_DIR, exist_ok=True)

BUNDLED_FONTS = {
    "Poppins Regular": "Poppins-Regular.ttf",
    "Poppins Medium": "Poppins-Medium.ttf",
    "Poppins Bold": "Poppins-Bold.ttf",
}


def list_available_fonts():
    """Return a dict of {display_name: absolute_path} for all usable fonts
    (bundled + any custom-uploaded TTFs)."""
    fonts = {}
    for name, filename in BUNDLED_FONTS.items():
        path = os.path.join(FONTS_DIR, filename)
        if os.path.exists(path):
            fonts[name] = path

    if os.path.isdir(CUSTOM_FONTS_DIR):
        for fname in sorted(os.listdir(CUSTOM_FONTS_DIR)):
            if fname.lower().endswith((".ttf", ".otf")):
                display = os.path.splitext(fname)[0].replace("_", " ")
                fonts[f"{display} (custom)"] = os.path.join(CUSTOM_FONTS_DIR, fname)

    return fonts


def save_custom_font(uploaded_file_bytes, filename):
    """Persist an uploaded TTF/OTF font file into the custom fonts dir.
    Returns the saved file's absolute path."""
    safe_name = os.path.basename(filename)
    dest = os.path.join(CUSTOM_FONTS_DIR, safe_name)
    with open(dest, "wb") as f:
        f.write(uploaded_file_bytes)
    return dest


def get_default_font_path(weight="Regular"):
    """Convenience getter for the default bundled font at a given weight
    ('Regular', 'Medium', 'Bold')."""
    key = f"Poppins {weight}"
    fonts = list_available_fonts()
    return fonts.get(key, fonts.get("Poppins Regular"))
