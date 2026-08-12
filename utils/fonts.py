"""
fonts.py
Font management: bundled default fonts (Calibri family, matching the
required dashboard typography) + custom TTF upload support.

"Calibri" here is Carlito (Google's open-source, metrics-compatible
replacement for Microsoft's Calibri -- same character widths/spacing/
overall look, but freely redistributable, since actual Calibri is a
proprietary Microsoft font that can't legally be bundled in this repo).
The bundled files are simply named Calibri-*.ttf so the rest of the app
(and the font picker) can refer to "Calibri" directly.

Google Font "live download" is intentionally NOT implemented (network
dependency) -- instead we ship the font family directly under
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
    "Calibri Regular": "Calibri-Regular.ttf",
    "Calibri Medium": "Calibri-Regular.ttf",
    "Calibri Bold": "Calibri-Bold.ttf",
    "Calibri Italic": "Calibri-Italic.ttf",
    "Poppins Regular": "Poppins-Regular.ttf",
    "Poppins Medium": "Poppins-Medium.ttf",
    "Poppins Bold": "Poppins-Bold.ttf",
}

# The single default typeface used across every generated image, at every
# canvas size, unless a page/template explicitly overrides it. Keeping this
# as one constant (rather than scattering "Poppins"/"Calibri" literals
# through each template) is what guarantees the growth graph -- and every
# other image type -- renders in the same font regardless of dimensions.
DEFAULT_FONT_FAMILY = "Calibri"


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
    ('Regular', 'Medium', 'Bold'). This is the ONE place that decides the
    app-wide default typeface -- every template calls this (directly or via
    a `font_regular`/`font_bold` param that defaults to it), so changing
    DEFAULT_FONT_FAMILY here changes every generated image, at every
    output dimension, consistently."""
    fonts = list_available_fonts()
    key = f"{DEFAULT_FONT_FAMILY} {weight}"
    fallback_key = f"{DEFAULT_FONT_FAMILY} Regular"
    return fonts.get(key, fonts.get(fallback_key, fonts.get("Poppins Regular")))
