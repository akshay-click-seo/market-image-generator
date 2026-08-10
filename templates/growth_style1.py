"""
growth_style1.py
"Market Growth - Style 1" template: full bar chart on the left, title bar
at top with logo, right-side stat card column (CAGR / Final Value / Base
Value / Forecast Period), website footer. Matches sample image 1 layout
(Voice Cloning market dashboard).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utils.chart import render_bar_chart
from utils.backgrounds import render_background
from utils.icons import get_icon
from utils.fonts import get_default_font_path
from utils.units import short_label


NAVY = "#0B2F7A"
NAVY_DARK = "#0A2560"
TEXT_DARK = "#1A2B4C"
GREY_TEXT = "#5B6B8C"
CARD_BG = "#FFFFFF"


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
    start_value,
    end_value,
    cagr,
    years,
    values,
    unit="Millones",
    website="www.example.com",
    logo_path=None,
    background="Classic Blue",
    font_regular=None,
    font_bold=None,
    width=1700,
    height=960,
):
    """Compose the full Style-1 Market Growth dashboard image. Returns PIL.Image (RGB)."""
    font_regular = font_regular or get_default_font_path("Regular")
    font_bold = font_bold or get_default_font_path("Bold")
    font_medium = get_default_font_path("Medium") or font_regular

    canvas = render_background(background, (width, height)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = int(width * 0.03)

    # ---- Header ----
    # Reserve top-right space for an optional logo only; no hardcoded brand text.
    brand_x = width - margin
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.12), int(height * 0.08)))
            logo_x = width - margin - logo.width
            canvas.alpha_composite(logo, (logo_x, margin + int(height * 0.05)))
            brand_x = logo_x
        except Exception:
            pass

    title = f"Tamaño del Mercado de {market_name} y Pronóstico de CAGR ({base_year}–{forecast_year})"
    title_font = _font(font_bold, int(width * 0.021))
    title_max_w = brand_x - margin - int(width * 0.02)
    title_lines = _wrap_text(draw, title, title_font, title_max_w)
    ty = margin
    for line in title_lines:
        draw.text((margin, ty), line, fill=NAVY, font=title_font)
        ty += title_font.size + int(height * 0.008)
    # underline
    underline_y = max(ty + int(height * 0.005), margin + int(width * 0.045))
    draw.line([(margin, underline_y), (int(width * 0.62), underline_y)], fill=NAVY, width=3)

    # ---- Chart area (left ~72%) ----
    chart_w = int(width * 0.68)
    chart_top = max(int(height * 0.15), underline_y + int(height * 0.04))
    chart_h = int(height * 0.98) - chart_top - int(height * 0.06)
    value_fmt = "{:.1f}"
    unit_label_full = short_label(unit)
    bar_img = render_bar_chart(
        years, values,
        width_px=chart_w, height_px=chart_h,
        bar_color=NAVY, label_color=NAVY, axis_color=TEXT_DARK,
        background="none", font_path=font_bold,
        y_label=f"Valor de Mercado en {unit_label_full} de USD",
        value_fmt=value_fmt,
    )
    canvas.alpha_composite(bar_img, (margin, chart_top))

    # website footer (left)
    footer_font = _font(font_bold, int(width * 0.017))
    draw.text((margin, height - int(height * 0.06)), website, fill=NAVY, font=footer_font)

    # ---- Right-side stat card column ----
    card_x = int(width * 0.735)
    card_w = width - card_x - margin
    card_gap = int(height * 0.025)
    card_h = int((height - chart_top - 3 * card_gap) / 4)

    cagr_display = f"{cagr:.1f}%".replace(".", ",")
    end_display = f"{end_value:.1f}".replace(".", ",")
    start_display = f"{start_value:.1f}".replace(".", ",")

    cards = [
        {
            "icon": "globe",
            "lines": [(f"CAGR {forecast_year - 1 if False else base_year+1} – {forecast_year}", GREY_TEXT, "small"),
                      (cagr_display, NAVY, "big")],
        },
        {
            "icon": "bar_chart",
            "lines": [(f"{currency} {end_display} {unit_label_full}", NAVY, "big"),
                      (f"Tamaño del Mercado, {forecast_year}", GREY_TEXT, "small")],
        },
        {
            "icon": "coins",
            "lines": [(f"{currency} {start_display} {unit_label_full}", NAVY, "big"),
                      (f"Tamaño del Mercado, {base_year}", GREY_TEXT, "small")],
        },
        {
            "icon": "calendar",
            "lines": [("Período de Pronóstico", GREY_TEXT, "small"),
                      (f"{base_year} – {forecast_year}", NAVY, "big")],
        },
    ]

    big_font = _font(font_bold, int(width * 0.021))
    small_font = _font(font_medium, int(width * 0.013))

    y = chart_top
    for card in cards:
        _draw_stat_card(canvas, draw, card_x, y, card_w, card_h, card["icon"], card["lines"], big_font, small_font, font_bold)
        y += card_h + card_gap

    return canvas.convert("RGB")


def _draw_rounded_card(draw, xy, radius, fill=None, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_stat_card(canvas, draw, x, y, w, h, icon_name, lines, big_font, small_font, font_bold_path):
    radius = int(h * 0.18)
    _draw_rounded_card(draw, [x, y, x + w, y + h], radius, fill=CARD_BG, outline="#DCE6F5", width=2)

    icon_size = int(h * 0.55)
    icon_pad = int(h * 0.22)
    icon_circle_d = int(h * 0.62)
    icon_cx = x + icon_pad + icon_circle_d // 2
    icon_cy = y + h // 2
    draw.ellipse(
        [icon_cx - icon_circle_d // 2, icon_cy - icon_circle_d // 2,
         icon_cx + icon_circle_d // 2, icon_cy + icon_circle_d // 2],
        fill=NAVY,
    )
    icon_img = get_icon(icon_name, size=int(icon_circle_d * 0.6), color="#FFFFFF")
    canvas.alpha_composite(icon_img, (icon_cx - icon_img.width // 2, icon_cy - icon_img.height // 2))

    text_x = x + icon_pad + icon_circle_d + int(w * 0.06)
    text_max_w = x + w - int(w * 0.05) - text_x

    resolved = []
    total_text_h = 0
    for text, color, size in lines:
        base_font = big_font if size == "big" else small_font
        font, text = _shrink_to_fit(draw, text, base_font, font_bold_path, text_max_w)
        resolved.append((text, color, font))
        total_text_h += font.size + 6

    ty = y + (h - total_text_h) // 2
    for text, color, font in resolved:
        draw.text((text_x, ty), text, fill=color, font=font)
        ty += font.size + 6


def _shrink_to_fit(draw, text, font, font_path, max_w, min_size=11):
    """Shrink the font size until the text fits max_w; only truncates as a last resort."""
    size = font.size
    current = font
    while size > min_size:
        bbox = draw.textbbox((0, 0), text, font=current)
        if bbox[2] - bbox[0] <= max_w:
            return current, text
        size -= 1
        current = _font(font_path, size)
    # last resort: truncate with ellipsis at min size
    while len(text) > 3:
        text = text[:-1]
        bbox = draw.textbbox((0, 0), text + "…", font=current)
        if bbox[2] - bbox[0] <= max_w:
            return current, text + "…"
    return current, text


def _wrap_text(draw, text, font, max_w):
    """Word-wrap text to fit within max_w, returning a list of lines."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
