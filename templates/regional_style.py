"""
regional_style.py
"Regional Analysis" template: world map with the selected country
highlighted + pin marker + flag badge callout, plus base/forecast value
stat cards on the right. Matches the sample "Análisis Regional" layout.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utils.backgrounds import render_background
from utils.map import render_world_map, get_country_iso2, iso2_to_flag_emoji
from utils.icons import get_icon
from utils.fonts import get_default_font_path
from utils.units import short_label
from utils.numfmt import format_es_number


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

    # ---- Title ----
    title_font = _font(font_bold, int(width * 0.028))
    title_lines = [f"Análisis Regional del Mercado de", f"{market_name} en {country}"]
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
    map_w, map_h = int(width * 0.62), int(height * 0.62)
    map_top = line_y + int(height * 0.03)
    map_img, pin_xy = render_world_map(
        width_px=map_w, height_px=map_h,
        highlight_country=country,
        base_color=MAP_BASE, highlight_color=MAP_HIGHLIGHT,
        ocean_color=(0, 0, 0, 0), border_color="#FFFFFF",
    )
    canvas.alpha_composite(map_img, (margin, int(map_top)))

    # pin marker + flag badge on the highlighted country
    if pin_xy:
        px, py = pin_xy
        px += margin
        py += map_top
        pin_r = int(width * 0.012)
        draw.ellipse([px - pin_r, py - pin_r * 2.4, px + pin_r, py], fill="#E23B3B", outline="#FFFFFF", width=3)
        draw.ellipse([px - pin_r * 0.4, py - pin_r * 1.6, px + pin_r * 0.4, py - pin_r * 0.8], fill="#FFFFFF")

        # flag + country name badge near the pin
        iso2 = get_country_iso2(country)
        flag = iso2_to_flag_emoji(iso2) if iso2 else "🏳️"
        badge_font = _font(font_bold, int(width * 0.016))
        badge_text = f"{country}"
        bb = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bb[2] - bb[0] + int(width * 0.05)
        badge_h = int(height * 0.045)
        badge_x = min(px + pin_r * 3, width - margin - map_w * 0.05 - badge_w)
        badge_y = py - badge_h - pin_r * 2
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=int(badge_h * 0.35), fill="#FFFFFF", outline=NAVY, width=2,
        )
        small_label_font = _font(font_medium, int(width * 0.011))
        draw.text((badge_x + int(width * 0.012), badge_y + int(badge_h * 0.08)),
                  "Mercado Clave", fill=GREY_TEXT, font=small_label_font)
        draw.text((badge_x + int(width * 0.012), badge_y + int(badge_h * 0.42)),
                  badge_text, fill=NAVY, font=badge_font)

    # ---- Right-side stat cards (Base year / Forecast year) ----
    card_x = margin + map_w + int(width * 0.03)
    card_w = width - card_x - margin
    card_h = int(height * 0.14)
    card_gap = int(height * 0.03)
    card_y = map_top + int(height * 0.08)

    base_display = f"{currency} {format_es_number(base_value, 2)}"
    forecast_display = f"{currency} {format_es_number(forecast_value, 2)}"
    unit_word = short_label(unit)

    cards = [
        ("bar_chart", f"{base_display} {unit_word}", f"Tamaño del Mercado en {base_year}"),
        ("globe", f"{forecast_display} {unit_word}", f"Tamaño del Mercado en {forecast_year}"),
    ]

    big_font = _font(font_bold, int(width * 0.019))
    small_font = _font(font_medium, int(width * 0.012))

    y = card_y
    for icon_name, big_text, small_text in cards:
        _draw_card(canvas, draw, card_x, y, card_w, card_h, icon_name, big_text, small_text, big_font, small_font)
        y += card_h + card_gap

    # ---- Footer ----
    footer_y = height - int(height * 0.06)
    draw.line([(0, footer_y), (width, footer_y)], fill="#DDE6F5", width=2)
    footer_font = _font(font_bold, int(width * 0.016))
    fbbox = draw.textbbox((0, 0), website, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text((center_x - fw / 2, footer_y + int(height * 0.015)), website, fill=NAVY, font=footer_font)

    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.1), int(height * 0.06)))
            canvas.alpha_composite(logo, (width - margin - logo.width, margin // 2))
        except Exception:
            pass

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
