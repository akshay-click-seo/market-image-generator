"""
icons.py
Simple vector-style icon drawing (PIL ImageDraw) for the stat cards used in
the Market Growth template: globe (CAGR), bar-chart (market size), coins
(base value), calendar (forecast period). Drawn programmatically so no
external icon asset files are required.
"""

import math
from PIL import Image, ImageDraw


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


def icon_coins(size=100, color="#FFFFFF"):
    img = _new_icon_canvas(size)
    d = ImageDraw.Draw(img)
    r = size * 0.28
    centers = [(size * 0.38, size * 0.4), (size * 0.62, size * 0.62)]
    for cx, cy in centers:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, size // 22))
    cx, cy = centers[-1]
    d.text((cx - size * 0.06, cy - size * 0.14), "$", fill=color, font=None)
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
