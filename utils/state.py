"""
state.py
Shared Streamlit session-state defaults for Settings (background, fonts,
logo, image size) used across all generator pages.
"""

import streamlit as st

from utils.backgrounds import list_preset_names
from utils.export import SIZE_PRESETS


DEFAULTS = {
    "settings_background": "Classic Blue",
    "settings_custom_bg_color": "#DEECFA",
    "settings_font_name": "Calibri Regular",
    "settings_logo_path": None,
    "settings_website": "www.informesdeexpertos.com",
    "settings_size_preset": "1600 x 900 (Widescreen)",
    "settings_custom_width": 1600,
    "settings_custom_height": 900,
    "settings_export_format": "PNG",
    "settings_export_quality": 90,
}


def init_state():
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_canvas_size():
    """Resolve the current width/height from Settings (preset or custom)."""
    preset = st.session_state.get("settings_size_preset", "Custom")
    if preset == "Custom":
        return st.session_state.get("settings_custom_width", 1600), st.session_state.get("settings_custom_height", 900)
    return SIZE_PRESETS.get(preset, (1600, 900))
