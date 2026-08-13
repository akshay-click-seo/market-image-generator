"""
branding.py
Default "Informes de Expertos" logo asset used across every generated
image, at every output dimension, unless the user uploads a custom logo
for that specific image.

Two pre-processed variants are bundled, both transparent-background RGBA
PNGs (white background removed from the original file):
  - informes_de_expertos.png       -- near-black (#111111) wordmark, for
                                       light/white/pale-blue backgrounds.
  - informes_de_expertos_white.png -- white wordmark, for dark backgrounds
                                       (e.g. the Segmentation template's
                                       solid navy header strip) where the
                                       dark variant would be unreadable.
"""

import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
DEFAULT_LOGO_PATH = os.path.join(ASSETS_DIR, "logo", "informes_de_expertos.png")
DEFAULT_LOGO_WHITE_PATH = os.path.join(ASSETS_DIR, "logo", "informes_de_expertos_white.png")


def get_default_logo_path(variant="dark"):
    """Return the bundled default logo's absolute path for the given
    variant ('dark' for the near-black wordmark, 'white' for the
    white-on-dark wordmark), or None if that asset is missing for some
    reason (callers should treat that the same as "no logo" rather than
    erroring)."""
    path = DEFAULT_LOGO_WHITE_PATH if variant == "white" else DEFAULT_LOGO_PATH
    return path if os.path.exists(path) else None


def resolve_logo_path(logo_path, variant="dark"):
    """Given a template's `logo_path` argument (None unless the user
    uploaded a custom logo for this image), return the path that should
    actually be drawn: the custom logo if provided, otherwise the bundled
    default logo (matching `variant`), otherwise None."""
    if logo_path and os.path.exists(logo_path):
        return logo_path
    return get_default_logo_path(variant)


# Background preset names (from utils/backgrounds.py PRESETS) whose canvas
# is dark enough that the near-black default logo wordmark would be
# unreadable -- these need the white variant instead.
_DARK_BACKGROUND_NAMES = {"Dark"}


def logo_variant_for_background(background):
    """Pick 'white' or 'dark' for the bundled default logo based on the
    template's chosen background preset name. Only meaningful for the
    bundled default logo -- a custom user-uploaded logo is always used
    as-is regardless of this."""
    if isinstance(background, str) and background in _DARK_BACKGROUND_NAMES:
        return "white"
    return "dark"
