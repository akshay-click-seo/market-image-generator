"""
regional_style.py
"Regional Analysis" template: world map with the selected country
highlighted + pin marker + flag badge callout, plus base/forecast value
stat cards on the right. Matches the sample "Análisis Regional" layout.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math

from PIL import Image, ImageDraw, ImageFont
from utils.backgrounds import render_background
from utils.map import render_world_map, get_country_iso2, resolve_region
from utils.flags import get_flag_badge
from utils.icons import get_icon
from utils.fonts import get_default_font_path
from utils.units import short_label
from utils.numfmt import format_es_number
from utils.branding import resolve_logo_path, logo_variant_for_background


NAVY = "#0B2F7A"
TEXT_DARK = "#1A2B4C"
GREY_TEXT = "#5B6B8C"
MAP_BASE = "#AFCBEC"
MAP_HIGHLIGHT = "#0B2F7A"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _dashed_line(draw, xy0, xy1, fill, width=2, dash=8, gap=6):
    """Draw a dashed straight line from xy0 to xy1 (PIL has no native dash support)."""
    x0, y0 = xy0
    x1, y1 = xy1
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    dx, dy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    drawing = True
    while pos < length:
        seg = dash if drawing else gap
        seg_end = min(pos + seg, length)
        if drawing:
            draw.line(
                [(x0 + dx * pos, y0 + dy * pos), (x0 + dx * seg_end, y0 + dy * seg_end)],
                fill=fill, width=width,
            )
        pos = seg_end
        drawing = not drawing


def render(
    market_name,
    country,
    currency,
    base_year,
    forecast_year,
    base_value,
    forecast_value,
    unit="Millones",
    website="www.example.com",
    logo_path=None,
    background="Light",
    font_regular=None,
    font_bold=None,
    width=1700,
    height=980,
):
    """Compose the Regional Analysis dashboard image. Returns PIL.Image (RGB)."""
    font_regular = font_regular or get_default_font_path("Regular")
    font_bold = font_bold or get_default_font_path("Bold")
    font_medium = get_default_font_path("Medium") or font_regular

    canvas = render_background(background, (width, height)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.03)

    # If `country` is actually a market-research region (e.g. "Latinoamérica",
    # "Latin America", "APAC") rather than a single country, resolve it to its
    # full member-country list up front -- this drives both the map highlight
    # below (shading every country in the region, not just showing unhighlighted
    # free text) and the title/label text (using the canonical display name).
    region_info = resolve_region(country)
    display_country = region_info["display"] if region_info else country

    # ---- Header: logo (top-right corner) ----
    # Sized/positioned the same way as Growth Style 1's header logo -- top
    # right corner, above the title -- now that the right-side column no
    # longer holds stat cards.
    brand_x = width - margin
    resolved_logo_path = resolve_logo_path(logo_path, variant=logo_variant_for_background(background))
    logo_img = None
    if resolved_logo_path:
        try:
            logo_img = Image.open(resolved_logo_path).convert("RGBA")
            max_logo_h = int(height * 0.09)
            max_logo_w = int(width * 0.22)
            scale = min(max_logo_w / logo_img.width, max_logo_h / logo_img.height)
            logo_img = logo_img.resize(
                (max(1, int(logo_img.width * scale)), max(1, int(logo_img.height * scale))), Image.LANCZOS
            )
            logo_x = width - margin - logo_img.width
            canvas.alpha_composite(logo_img, (logo_x, int(margin * 0.5)))
            brand_x = logo_x
        except Exception:
            logo_img = None

    # ---- Title ----
    title_font = _font(font_bold, int(width * 0.028))
    title_lines = [f"Análisis Regional del Mercado de", f"{market_name} en {display_country}"]
    center_x = width / 2
    ty = margin * 0.7
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw / 2, ty), line, fill=NAVY, font=title_font)
        ty += title_font.size + 10

    line_y = ty + 8
    draw.line([(margin, line_y), (width - margin, line_y)], fill=NAVY, width=2)

    # ---- World map with highlighted country ----
    # Widened/enlarged to use most of the canvas now that the right-side
    # stat-card column is gone (the logo moved up to the header corner
    # instead).
    map_w, map_h = int(width * 0.94), int(height * 0.72)
    map_top = line_y + int(height * 0.03)
    if region_info:
        map_img, pin_xy = render_world_map(
            width_px=map_w, height_px=map_h,
            highlight_countries=region_info["countries"],
            base_color=MAP_BASE, highlight_color=MAP_HIGHLIGHT,
            ocean_color=(0, 0, 0, 0), border_color="#FFFFFF",
        )
    else:
        map_img, pin_xy = render_world_map(
            width_px=map_w, height_px=map_h,
            highlight_country=country,
            base_color=MAP_BASE, highlight_color=MAP_HIGHLIGHT,
            ocean_color=(0, 0, 0, 0), border_color="#FFFFFF",
        )
    canvas.alpha_composite(map_img, (margin, int(map_top)))

    # pin marker + circular flag badge (dashed-line callout) on the highlighted country
    if pin_xy:
        px, py = pin_xy
        px += margin
        py += map_top
        pin_r = int(width * 0.012)
        draw.ellipse([px - pin_r, py - pin_r * 2.4, px + pin_r, py], fill="#E23B3B", outline="#FFFFFF", width=3)
        draw.ellipse([px - pin_r * 0.4, py - pin_r * 1.6, px + pin_r * 0.4, py - pin_r * 0.8], fill="#FFFFFF")
        pin_top_x, pin_top_y = px, py - pin_r * 2.4

        # circular flag badge, connected to the pin via a dashed line.
        # Measure the label pill's width up front so the whole badge+label
        # group can be kept inside the map bounds together (prevents the
        # pill from being clamped independently and overlapping the badge).
        iso2 = None if region_info else get_country_iso2(country)
        badge_size = int(width * 0.052)
        badge_font = _font(font_bold, int(width * 0.017))
        badge_text = f"{display_country}"
        bb = draw.textbbox((0, 0), badge_text, font=badge_font)
        label_w = bb[2] - bb[0] + int(width * 0.045)
        label_h = int(height * 0.038)
        label_gap = int(width * 0.01)

        # Offset is proportional to the MAP's own size (not the full canvas)
        # and kept small so the badge lands just beside the pin -- a large
        # offset can overshoot a compact country/continent (e.g. South
        # America) across open ocean into an unrelated, unhighlighted area.
        group_w = badge_size + label_gap + label_w
        map_right_bound = margin + map_w - int(map_w * 0.02)
        badge_cx = px + int(map_w * 0.075)
        badge_cx = min(badge_cx, map_right_bound - group_w + badge_size / 2)
        badge_cx = max(badge_cx, margin + badge_size / 2)
        badge_cy = pin_top_y - int(map_h * 0.11)
        badge_cy = max(badge_cy, int(map_top) + badge_size / 2 + int(height * 0.01))

        _dashed_line(draw, (pin_top_x, pin_top_y), (badge_cx, badge_cy), fill="#FFFFFF", width=3, dash=7, gap=5)

        if region_info:
            # A whole region has no single national flag -- draw a plain
            # navy circle with a globe icon instead (same visual language as
            # the stat-card icon circles used elsewhere in the app).
            draw.ellipse(
                [badge_cx - badge_size / 2, badge_cy - badge_size / 2, badge_cx + badge_size / 2, badge_cy + badge_size / 2],
                fill=NAVY, outline="#FFFFFF", width=max(3, int(badge_size * 0.045)),
            )
            globe_icon = get_icon("globe", size=int(badge_size * 0.6), color="#FFFFFF")
            canvas.alpha_composite(globe_icon, (int(badge_cx - globe_icon.width / 2), int(badge_cy - globe_icon.height / 2)))
        else:
            flag_badge = get_flag_badge(country, size=badge_size, border_color="#FFFFFF", border_width=max(3, int(badge_size * 0.045)), iso2=iso2)
            canvas.alpha_composite(flag_badge, (int(badge_cx - badge_size / 2), int(badge_cy - badge_size / 2)))
        # thin navy outline ring on top of the white border for definition
        draw.ellipse(
            [badge_cx - badge_size / 2, badge_cy - badge_size / 2, badge_cx + badge_size / 2, badge_cy + badge_size / 2],
            outline=NAVY, width=2,
        )

        # pill-shaped label box to the right of the flag badge
        label_x = badge_cx + badge_size / 2 + label_gap
        label_y = badge_cy - label_h / 2

        connector_x0 = badge_cx + badge_size / 2 - int(width * 0.012)
        draw.line([(connector_x0, badge_cy), (label_x, badge_cy)], fill=NAVY, width=2)
        draw.rounded_rectangle(
            [label_x, label_y, label_x + label_w, label_y + label_h],
            radius=int(label_h * 0.5), fill="#FFFFFF", outline=NAVY, width=2,
        )
        text_pad_x = int(width * 0.016)
        tbbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        text_h = tbbox[3] - tbbox[1]
        text_y = label_y + (label_h - text_h) / 2 - tbbox[1]
        draw.text((label_x + text_pad_x, text_y), badge_text, fill=NAVY, font=badge_font)

    unit_word = short_label(unit)

    # ---- Footer ----
    footer_y = height - int(height * 0.06)
    draw.line([(0, footer_y), (width, footer_y)], fill="#DDE6F5", width=2)
    footer_font = _font(font_bold, int(width * 0.016))
    fbbox = draw.textbbox((0, 0), website, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text((center_x - fw / 2, footer_y + int(height * 0.015)), website, fill=NAVY, font=footer_font)

    # (Logo already drawn in the header, top-right corner -- see above.)

    return canvas.convert("RGB")


def _draw_card(canvas, draw, x, y, w, h, icon_name, big_text, small_text, big_font, small_font):
    x, y, w, h = int(x), int(y), int(w), int(h)
    radius = int(h * 0.16)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill="#FFFFFF", outline="#DCE6F5", width=2)

    icon_d = int(h * 0.62)
    icon_pad = int(h * 0.19)
    icon_cx = x + icon_pad + icon_d // 2
    icon_cy = y + h // 2
    draw.ellipse([icon_cx - icon_d // 2, icon_cy - icon_d // 2, icon_cx + icon_d // 2, icon_cy + icon_d // 2], fill=NAVY)
    icon_img = get_icon(icon_name, size=int(icon_d * 0.6), color="#FFFFFF")
    canvas.alpha_composite(icon_img, (icon_cx - icon_img.width // 2, icon_cy - icon_img.height // 2))

    text_x = x + icon_pad + icon_d + int(w * 0.06)
    total_h = big_font.size + small_font.size + 8
    ty = y + (h - total_h) // 2
    draw.text((text_x, ty), big_text, fill=NAVY, font=big_font)
    ty += big_font.size + 8
    draw.text((text_x, ty), small_text, fill=GREY_TEXT, font=small_font)
