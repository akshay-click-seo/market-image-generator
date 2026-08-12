"""
icons.py
Simple vector-style icon drawing (PIL ImageDraw) for the stat cards used in
the Market Growth template: globe (CAGR), bar-chart (market size), coins
(base value), calendar (forecast period). Drawn programmatically so no
external icon asset files are required.
"""

import math
from PIL import Image, ImageDraw, ImageFont

from utils.fonts import get_default_font_path


def _new_icon_canvas(size):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def icon_globe(size=100, color="#FFFFFF"):
    img = _new_icon_canvas(size)
    d = ImageDraw.Draw(img)
    pad = size * 0.08
    d.ellipse([pad, pad, size - pad, size - pad], outline=color, width=max(2, size // 18))
    # latitude lines
    cy = size / 2
    for frac in (0.35, 0.65):
        y = size * frac
        half_w = math.sqrt(max(0, (size / 2 - pad) ** 2 - (y - cy) ** 2))
        d.line([(size / 2 - half_w, y), (size / 2 + half_w, y)], fill=color, width=max(1, size // 40))
    # longitude ellipses
    d.ellipse([size * 0.32, pad, size * 0.68, size - pad], outline=color, width=max(1, size // 40))
    d.line([(size / 2, pad), (size / 2, size - pad)], fill=color, width=max(1, size // 40))
    return img


def icon_bar_chart(size=100, color="#FFFFFF"):
    img = _new_icon_canvas(size)
    d = ImageDraw.Draw(img)
    base_y = size * 0.82
    bar_w = size * 0.14
    gap = size * 0.08
    heights = [0.35, 0.55, 0.75, 0.45]
    x = size * 0.12
    for h in heights:
        top = base_y - size * h
        d.rounded_rectangle([x, top, x + bar_w, base_y], radius=size * 0.02, fill=color)
        x += bar_w + gap
    d.line([(size * 0.08, base_y), (size * 0.92, base_y)], fill=color, width=max(2, size // 30))
    return img


def icon_coins(size=100, color="#FFFFFF", bg_color="#0B2F7A"):
    """A stack of coins (viewed from the side, like a coin roll) with a
    small circular '$' badge overlapping at the bottom-right -- matches the
    reference "Base Value" card icon. `bg_color` is used to draw thin gap
    lines between the stacked coin discs (this icon is always composited
    onto a solid-color circle, so the gaps "cut through" to that color)."""
    img = _new_icon_canvas(size)
    d = ImageDraw.Draw(img)

    # coin stack: 3 stacked discs (ellipses), upper-left of the icon
    stack_cx = size * 0.42
    stack_w = size * 0.5
    disc_h = size * 0.22
    top_y = size * 0.24
    n_discs = 3
    for i in range(n_discs):
        cy = top_y + i * (disc_h * 0.6)
        d.ellipse([stack_cx - stack_w / 2, cy, stack_cx + stack_w / 2, cy + disc_h],
                  fill=color)
    # gap lines to separate each disc visually
    for i in range(1, n_discs):
        cy = top_y + i * (disc_h * 0.6)
        d.line([(stack_cx - stack_w / 2 + size * 0.02, cy), (stack_cx + stack_w / 2 - size * 0.02, cy)],
               fill=bg_color, width=max(2, int(size * 0.025)))

    # '$' badge, overlapping the bottom-right of the stack
    badge_r = size * 0.24
    badge_cx, badge_cy = size * 0.62, size * 0.68
    d.ellipse([badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
               fill=bg_color, outline=color, width=max(2, int(size * 0.03)))
    try:
        font_path = get_default_font_path("Bold")
        font = ImageFont.truetype(font_path, int(size * 0.26)) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    text = "$"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((badge_cx - tw / 2 - bbox[0], badge_cy - th / 2 - bbox[1]), text, fill=color, font=font)
    return img


def icon_calendar(size=100, color="#FFFFFF"):
    img = _new_icon_canvas(size)
    d = ImageDraw.Draw(img)
    pad = size * 0.14
    top = size * 0.22
    d.rounded_rectangle([pad, top, size - pad, size - pad * 0.6], radius=size * 0.04, outline=color, width=max(2, size // 25))
    d.line([(pad, top + size * 0.14), (size - pad, top + size * 0.14)], fill=color, width=max(2, size // 30))
    # rings
    d.line([(size * 0.3, top - size * 0.08), (size * 0.3, top + size * 0.05)], fill=color, width=max(2, size // 25))
    d.line([(size * 0.7, top - size * 0.08), (size * 0.7, top + size * 0.05)], fill=color, width=max(2, size // 25))
    return img


ICON_REGISTRY = {
    "globe": icon_globe,
    "bar_chart": icon_bar_chart,
    "coins": icon_coins,
    "calendar": icon_calendar,
}


def get_icon(name, size=100, color="#FFFFFF"):
    fn = ICON_REGISTRY.get(name, icon_globe)
    return fn(size=size, color=color)
