"""
flags.py
Country flag image lookup + circular badge cropping, used by the Regional
Analysis template to render an actual flag (matching the reference design's
circular flag badge) instead of plain text.

Uses the `flagpy` package (bundled flag images, no network calls at
runtime) with a fuzzy name matcher so free-typed country names ("USA",
"South Korea", "Mexico", ...) resolve to the right flag even when they
don't exactly match flagpy's canonical country list.
"""

import re
import unicodedata
from functools import lru_cache

from PIL import Image, ImageDraw

try:
    import flagpy
    _FLAGPY_AVAILABLE = True
except Exception:
    _FLAGPY_AVAILABLE = False


def _strip_accents(s):
    normalized = unicodedata.normalize("NFKD", s)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _normalize(name):
    name = _strip_accents(name.lower().strip())
    name = re.sub(r"^the\s+", "", name)
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


# Common abbreviations / short forms users are likely to type directly,
# which don't share enough characters with flagpy's canonical name for the
# substring matcher below to find on its own.
_ALIAS_TO_CANONICAL = {
    "usa": "united states",
    "us": "united states",
    "u s a": "united states",
    "uk": "united kingdom",
    "uae": "united arab emirates",
    "drc": "democratic republic of the congo",
    "south korea": "south korea",
    "n korea": "north korea",
    "s korea": "south korea",
    "czechia": "czech republic",
    "ivory coast": "ivory coast",
}


@lru_cache(maxsize=1)
def _country_list():
    if not _FLAGPY_AVAILABLE:
        return []
    return flagpy.get_country_list()


@lru_cache(maxsize=1)
def _normalized_lookup():
    return {_normalize(c): c for c in _country_list()}


def _best_flagpy_name(*candidate_names):
    """Fuzzy-match any of the given candidate strings (country name, ISO
    code, alternate spellings, ...) against flagpy's country list."""
    if not _FLAGPY_AVAILABLE:
        return None
    lookup = _normalized_lookup()
    norm_candidates = [_normalize(c) for c in candidate_names if c]
    # expand with known abbreviation aliases (e.g. "usa" -> "united states")
    norm_candidates += [_ALIAS_TO_CANONICAL[c] for c in norm_candidates if c in _ALIAS_TO_CANONICAL]

    # 1. exact normalized match
    for cand in norm_candidates:
        if cand in lookup:
            return lookup[cand]

    # 2. substring match either direction
    for cand in norm_candidates:
        if not cand:
            continue
        for norm_name, orig_name in lookup.items():
            if cand in norm_name or norm_name in cand:
                return orig_name

    return None


def _circular_crop(img, size):
    """Resize `img` to fill a `size`x`size` circle and mask it circular."""
    img = img.convert("RGBA")
    # scale to cover the square, center-crop
    src_w, src_h = img.size
    scale = max(size / src_w, size / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - size) // 2
    top = (new_h - size) // 2
    img = img.crop((left, top, left + size, top + size))

    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def get_flag_badge(country_name, size=120, border_color="#FFFFFF", border_width=4,
                    iso2=None, extra_candidates=None):
    """
    Return a circular flag badge (PIL RGBA image, `size`x`size`) for the
    given country, with a solid ring border -- matching the reference
    Regional Analysis design. Falls back to a plain navy circle with the
    ISO2 initials (or '?') if no flag can be resolved, so this never raises.
    """
    candidates = [country_name] + list(extra_candidates or [])
    match = _best_flagpy_name(*candidates)

    badge = None
    if match and _FLAGPY_AVAILABLE:
        try:
            flag_img = flagpy.get_flag_img(match)
            badge = _circular_crop(flag_img, size)
        except Exception:
            badge = None

    if badge is None:
        # Fallback: plain circle with initials so the layout never breaks.
        badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(badge)
        d.ellipse([0, 0, size, size], fill="#0B2F7A")
        initials = (iso2 or (country_name[:2] if country_name else "?")).upper()
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
        except Exception:
            font = None
        bbox = d.textbbox((0, 0), initials, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((size - tw) / 2, (size - th) / 2), initials, fill="#FFFFFF", font=font)

    # ring border
    if border_width > 0:
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.alpha_composite(badge)
        d = ImageDraw.Draw(canvas)
        d.ellipse(
            [border_width / 2, border_width / 2, size - border_width / 2, size - border_width / 2],
            outline=border_color, width=border_width,
        )
        return canvas
    return badge
