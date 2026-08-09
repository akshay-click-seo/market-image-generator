"""
growth_style2.py
"Market Growth - Style 2" template: minimal layout with a left CAGR card,
a faint world-map watermark in the background, top-left/right value
callouts pointing to the first/last bars, and a bottom footer. Matches
sample image 2 (Plant-Based Protein Market in Mexico) layout.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utils.chart import render_bar_chart
from utils.backgrounds import render_background
from utils.map import render_world_map
from utils.fonts import get_default_font_path


NAVY = "#0B2F7A"
TEXT_DARK = "#1A2B4C"
GREY_TEXT = "#5B6B8C"


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
    unit="Million",
    website="www.example.com",
    logo_path=None,
    background="Modern White",
    font_regular=None,
    font_bold=None,
    width=1700,
    height=1120,
):
    """Compose the Style-2 Market Growth dashboard image. Returns PIL.Image (RGB)."""
    font_regular = font_regular or get_default_font_path("Regular")
    font_bold = font_bold or get_default_font_path("Bold")
    font_medium = get_default_font_path("Medium") or font_regular

    canvas = render_background(background, (width, height)).convert("RGBA")

    # faint world map watermark in the background, top-right area
    try:
        map_img, _ = render_world_map(
            width_px=int(width * 0.6), height_px=int(height * 0.55),
            base_color="#EDF2FA", ocean_color=(0, 0, 0, 0), border_color="#FFFFFF",
        )
        canvas.alpha_composite(map_img, (int(width * 0.38), int(height * 0.08)))
    except Exception:
        pass

    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.03)

    # ---- Title ----
    title = f"Mercado de {market_name} en {country}"
    title_font = _font(font_bold, int(width * 0.026))
    center_x = width / 2
    tbbox = draw.textbbox((0, 0), title, font=title_font)
    tw = tbbox[2] - tbbox[0]
    draw.text((center_x - tw / 2, margin * 0.7), title, fill=NAVY, font=title_font)
    draw.line([(margin, margin * 0.7 + title_font.size + 14), (width - margin, margin * 0.7 + title_font.size + 14)],
              fill=NAVY, width=2)

    subtitle_font = _font(font_medium, int(width * 0.015))
    subtitle = f"Tamaño del Mercado ({currency} {'Mil Millones' if unit == 'Billion' else 'Millones'})"
    sbbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw = sbbox[2] - sbbox[0]
    draw.text((center_x - sw / 2, margin * 0.7 + title_font.size + 30), subtitle, fill=GREY_TEXT, font=subtitle_font)

    # ---- CAGR card (top-left) ----
    cagr_display = f"{cagr:.2f}%".replace(".", ",")
    card_w, card_h = int(width * 0.24), int(height * 0.16)
    card_x, card_y = margin, int(height * 0.18)
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                            radius=int(card_h * 0.14), outline=NAVY, width=3, fill="#FFFFFF")
    cagr_num_font = _font(font_bold, int(width * 0.032))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.14), cagr_display, fill=NAVY, font=cagr_num_font)
    cagr_label_font = _font(font_bold, int(width * 0.014))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.58), "CAGR", fill=TEXT_DARK, font=cagr_label_font)
    period_font = _font(font_medium, int(width * 0.013))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.78),
              f"({base_year + 1}-{forecast_year})", fill=GREY_TEXT, font=period_font)

    # ---- Start / End value callouts (placed below the card/map row) ----
    callout_font_val = _font(font_bold, int(width * 0.02))
    callout_font_label = _font(font_medium, int(width * 0.012))

    start_display = f"{currency} {start_value:.2f}".replace(".", ",")
    end_display = f"{currency} {end_value:.2f}".replace(".", ",")
    unit_word = "Millones" if unit != "Billion" else "Mil Millones"

    callout_y = int(height * 0.40)

    # ---- Bar chart (bottom, full width) ----
    chart_w = int(width * 0.9)
    chart_x = margin
    chart_top = callout_y + int(height * 0.075)
    chart_h = int(height * 0.98) - chart_top - int(height * 0.06)
    value_fmt = "{:.2f}" if max(values) < 1000 else "{:.0f}"
    bar_img = render_bar_chart(
        years, values,
        width_px=chart_w, height_px=chart_h,
        bar_color=NAVY, label_color=NAVY, axis_color=TEXT_DARK,
        background="none", font_path=font_bold,
        y_label="",
        value_fmt=value_fmt,
    )
    canvas.alpha_composite(bar_img, (chart_x, chart_top))

    # start value callout, above first bar
    draw.text((chart_x + int(chart_w * 0.02), callout_y), start_display, fill=NAVY, font=callout_font_val)
    draw.text((chart_x + int(chart_w * 0.02), callout_y + callout_font_val.size + 4),
              unit_word, fill=TEXT_DARK, font=callout_font_label)

    # end value callout, above last bar
    end_bbox = draw.textbbox((0, 0), end_display, font=callout_font_val)
    ew = end_bbox[2] - end_bbox[0]
    draw.text((chart_x + chart_w - ew - int(chart_w * 0.02), callout_y), end_display, fill=NAVY, font=callout_font_val)
    unit_bbox = draw.textbbox((0, 0), unit_word, font=callout_font_label)
    uw = unit_bbox[2] - unit_bbox[0]
    draw.text((chart_x + chart_w - uw - int(chart_w * 0.02), callout_y + callout_font_val.size + 4),
              unit_word, fill=TEXT_DARK, font=callout_font_label)

    # ---- Footer ----
    footer_font = _font(font_bold, int(width * 0.016))
    draw.line([(0, height - int(height * 0.06)), (width, height - int(height * 0.06))], fill="#DDE6F5", width=2)
    fbbox = draw.textbbox((0, 0), website, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text((center_x - fw / 2, height - int(height * 0.045)), website, fill=NAVY, font=footer_font)

    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.1), int(height * 0.06)))
            canvas.alpha_composite(logo, (width - margin - logo.width, margin // 2))
        except Exception:
            pass

    return canvas.convert("RGB")
