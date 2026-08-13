"""
segmentation_style.py
"Segmentation" template: donut/ring chart in the center with 2-6 colored
segments, each connected via a line to a labeled callout box arranged
around the ring. Matches the sample "Segmentación del Mercado" layout.
"""

import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utils.backgrounds import render_background
from utils.fonts import get_default_font_path
from utils.branding import resolve_logo_path


NAVY = "#0B2F7A"
TEXT_DARK = "#1A2B4C"
DEFAULT_PALETTE = ["#0B2F7A", "#159A9C", "#7A3FD1", "#E8791A", "#4C8C2B", "#C0392B"]


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def render(
    market_name,
    segments,
    website="www.example.com",
    logo_path=None,
    background="Gradient",
    font_regular=None,
    font_bold=None,
    colors=None,
    width=1536,
    height=1130,
):
    """
    Compose the Segmentation donut dashboard image. The donut always renders
    exactly len(segments) slices -- pass only the segments you want shown.

    Args:
        market_name: str, used in the title
        segments: list of 2-8 label strings, e.g. ["Por Tipo de Producto", "Por Aplicación", ...]
        colors: optional list of hex colors, one per segment

    Returns PIL.Image (RGB).
    """
    if not (2 <= len(segments) <= 8):
        raise ValueError("segments must contain between 2 and 8 labels")

    font_regular = font_regular or get_default_font_path("Regular")
    font_bold = font_bold or get_default_font_path("Bold")

    colors = colors or [DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)] for i in range(len(segments))]

    canvas = render_background(background, (width, height)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.03)
    center_x = width / 2

    # ---- Title bar ----
    title_h = int(height * 0.11)
    draw.rectangle([0, 0, width, title_h], fill=NAVY)
    title_font = _font(font_bold, int(width * 0.028))
    title = f"Segmentación del Mercado de {market_name}"
    tbbox = draw.textbbox((0, 0), title, font=title_font)
    tw = tbbox[2] - tbbox[0]
    if tw > width * 0.94:
        title_font = _font(font_bold, int(width * 0.021))
        tbbox = draw.textbbox((0, 0), title, font=title_font)
        tw = tbbox[2] - tbbox[0]
    draw.text((center_x - tw / 2, title_h / 2 - title_font.size / 2), title, fill="#FFFFFF", font=title_font)

    # ---- Donut chart (center) ----
    donut_d = int(min(width, height - title_h) * 0.42)
    donut_cx, donut_cy = center_x, title_h + (height - title_h) * 0.52
    n = len(segments)
    angle_per = 360.0 / n
    start_angle = -90

    hole_ratio = 0.42
    ring_bbox = [donut_cx - donut_d / 2, donut_cy - donut_d / 2, donut_cx + donut_d / 2, donut_cy + donut_d / 2]
    hole_r = donut_d / 2 * hole_ratio
    hole_bbox = [donut_cx - hole_r, donut_cy - hole_r, donut_cx + hole_r, donut_cy + hole_r]

    mid_angles = []
    for i in range(n):
        a0 = start_angle + i * angle_per
        a1 = a0 + angle_per
        draw.pieslice(ring_bbox, a0, a1, fill=colors[i])
        mid_angles.append((a0 + a1) / 2)

    # cut the hole (donut effect) + white separators
    bg_sample = canvas.getpixel((5, height - 5))
    draw.ellipse(hole_bbox, fill=bg_sample)
    for i in range(n):
        a0 = math.radians(start_angle + i * angle_per)
        x0, y0 = donut_cx + hole_r * math.cos(a0), donut_cy + hole_r * math.sin(a0)
        x1, y1 = donut_cx + (donut_d / 2) * math.cos(a0), donut_cy + (donut_d / 2) * math.sin(a0)
        draw.line([(x0, y0), (x1, y1)], fill=bg_sample, width=max(3, int(width * 0.006)))

    # ---- Callout boxes around the ring, connected via lines ----
    label_font = _font(font_bold, int(width * 0.015))
    box_h = int(height * 0.075)
    ring_outer_r = donut_d / 2

    for i, (label, angle_deg) in enumerate(zip(segments, mid_angles)):
        rad = math.radians(angle_deg)
        edge_x = donut_cx + ring_outer_r * math.cos(rad)
        edge_y = donut_cy + ring_outer_r * math.sin(rad)

        connector_len = width * 0.09
        elbow_x = donut_cx + (ring_outer_r + connector_len) * math.cos(rad)
        elbow_y = donut_cy + (ring_outer_r + connector_len) * math.sin(rad)

        going_right = math.cos(rad) >= 0
        box_w = int(width * 0.19)
        box_x = elbow_x if going_right else elbow_x - box_w
        box_y = elbow_y - box_h / 2

        # keep boxes within canvas bounds
        box_x = max(margin, min(box_x, width - margin - box_w))
        box_y = max(title_h + 10, min(box_y, height - box_h - int(height * 0.08)))

        anchor_x = box_x if going_right else box_x + box_w
        draw.line([(edge_x, edge_y), (elbow_x, elbow_y)], fill=colors[i], width=3)
        draw.line([(elbow_x, elbow_y), (anchor_x, box_y + box_h / 2)], fill=colors[i], width=3)
        draw.ellipse([edge_x - 5, edge_y - 5, edge_x + 5, edge_y + 5], fill=colors[i])

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=int(box_h * 0.25), fill=colors[i],
        )
        label_up = label.upper()
        lbbox = draw.textbbox((0, 0), label_up, font=label_font)
        lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
        if lw > box_w * 0.88:
            # shrink font to fit
            size = label_font.size
            f = label_font
            while lw > box_w * 0.88 and size > 10:
                size -= 1
                f = _font(font_bold, size)
                lbbox = draw.textbbox((0, 0), label_up, font=f)
                lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
            label_font_used = f
        else:
            label_font_used = label_font
        draw.text((box_x + (box_w - lw) / 2, box_y + (box_h - lh) / 2 - lbbox[1]), label_up,
                   fill="#FFFFFF", font=label_font_used)

    # ---- Footer ----
    footer_y = height - int(height * 0.05)
    draw.line([(0, footer_y), (width, footer_y)], fill="#DDE6F5", width=2)
    footer_font = _font(font_bold, int(width * 0.017))
    footer_text = f"🌐  {website}" if False else website
    fbbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text((center_x - fw / 2, footer_y + int(height * 0.012)), footer_text, fill=NAVY, font=footer_font)

    # This template's logo sits on the solid navy title bar, so the
    # bundled default logo must use its white variant here to stay
    # readable (a custom user-uploaded logo is used as-is, unchanged).
    resolved_logo_path = resolve_logo_path(logo_path, variant="white")
    if resolved_logo_path:
        try:
            logo = Image.open(resolved_logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.1), int(title_h * 0.6)), Image.LANCZOS)
            canvas.alpha_composite(logo, (width - margin - logo.width, int((title_h - logo.height) / 2)))
        except Exception:
            pass

    return canvas.convert("RGB")
