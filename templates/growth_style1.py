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
from utils.numfmt import format_es_number, format_es_percent


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

    # Base title is just the market name; when a specific country/region is
    # given (i.e. not the generic "Global" default) it's appended as
    # "... en {country}" instead of showing the CAGR/year-range in the title.
    title = f"Tamaño del Mercado de {market_name}"
    if country and country.strip().lower() not in ("", "global"):
        title += f" en {country.strip()}"
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
    footer_top = height - int(height * 0.075)
    # Reserve a bit more clearance above the footer -- with bbox_inches="tight"
    # the chart image's actual rendered height can slightly exceed the
    # requested height_px (rotated tick labels add extra height), so ask
    # for less than the full remaining space to keep it from overlapping
    # the website footer text at small canvas sizes.
    chart_h = footer_top - chart_top - int(height * 0.07)
    unit_label_full = short_label(unit)
    bar_img = render_bar_chart(
        years, values,
        width_px=chart_w, height_px=chart_h,
        bar_color=NAVY, label_color=NAVY, axis_color=TEXT_DARK,
        background="none", font_path=font_bold,
        y_label=f"Valor de Mercado en {unit_label_full} de USD",
        value_formatter=lambda v: format_es_number(v, 1),
        labels_only_ends=True,
    )
    canvas.alpha_composite(bar_img, (margin, chart_top))

    # website footer (centered, matching the other templates)
    footer_font = _font(font_bold, int(width * 0.017))
    fbbox = draw.textbbox((0, 0), website, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text(((width - fw) / 2, footer_top), website, fill=NAVY, font=footer_font)

    # ---- Right-side stat card column ----
    card_x = int(width * 0.735)
    card_w = width - card_x - margin
    card_gap = int(height * 0.025)
    # Fixed, comfortable card height (not stretched to fill all available
    # space down to the bottom) -- the column is then vertically centered
    # within the space between the header and the footer.
    card_h = int(height * 0.145)
    column_available_top = chart_top
    column_available_bottom = height - int(height * 0.09)  # leave room for footer
    column_h = 4 * card_h + 3 * card_gap
    column_top = column_available_top + max(
        0, (column_available_bottom - column_available_top - column_h) // 2
    )

    cagr_display = format_es_percent(cagr, 1)
    end_display = format_es_number(end_value, 1)
    start_display = format_es_number(start_value, 1)

    cards = [
        {
            "icon": "globe",
            "lines": [(f"CAGR {forecast_year - 1 if False else base_year+1} – {forecast_year}", TEXT_DARK, "small"),
                      (cagr_display, NAVY, "big")],
            "divider": True,
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
            "lines": [("Período de Pronóstico", TEXT_DARK, "small"),
                      (f"{base_year} – {forecast_year}", NAVY, "big")],
            "divider": True,
        },
    ]

    big_font = _font(font_bold, int(width * 0.021))
    small_font = _font(font_medium, int(width * 0.013))

    # Four separate cards, each its own rounded white box with a navy
    # border, stacked with a visible gap between them (matching the
    # reference) -- not one shared container. Vertically centered in the
    # column instead of stretched to the bottom.
    y = column_top
    for card in cards:
        _draw_stat_card(
            canvas, draw, card_x, y, card_w, card_h, card["icon"], card["lines"], big_font, small_font, font_bold,
            divider=card.get("divider", False),
        )
        y += card_h + card_gap

    return canvas.convert("RGB")


def _draw_stat_card(canvas, draw, x, y, w, h, icon_name, lines, big_font, small_font, font_bold_path,
                     divider=False):
    radius = int(h * 0.18)
    border_w = max(2, int(h * 0.035))
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=CARD_BG, outline=NAVY, width=border_w)

    icon_circle_d = int(h * 0.62)
    icon_pad = int(h * 0.22)
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
    min_font_size = max(7, int(h * 0.09))

    # Resolve each line to (possibly multi-line) wrapped text instead of
    # truncating with an ellipsis -- long values like "EUR 2.035,0 Millones"
    # on a narrow card (small export sizes such as 800x350) need to wrap
    # onto a second line rather than getting cut off.
    resolved = []
    total_text_h = 0
    line_gap = max(2, int(h * 0.02))
    for text, color, size in lines:
        base_font = big_font if size == "big" else small_font
        font, wrapped_lines = _wrap_to_fit(draw, text, base_font, font_bold_path, text_max_w, min_font_size)
        resolved.append((wrapped_lines, color, font, size))
        total_text_h += len(wrapped_lines) * (font.size + line_gap)
    if divider:
        total_text_h += 8

    ty = y + max(0, (h - total_text_h) // 2)
    for wrapped_lines, color, font, size in resolved:
        for line_text in wrapped_lines:
            draw.text((text_x, ty), line_text, fill=color, font=font)
            ty += font.size + line_gap
        if divider and size == "small":
            # thin dotted separator between the small label and the big
            # value below it, matching the reference's CAGR/Period cards
            dash_y = ty + 2
            dash_x = text_x
            end_x = x + w - int(w * 0.06)
            while dash_x < end_x:
                draw.line([(dash_x, dash_y), (min(dash_x + 4, end_x), dash_y)], fill="#B9C6E3", width=2)
                dash_x += 8
            ty += 8


def _wrap_to_fit(draw, text, font, font_path, max_w, min_size=11, max_lines=2):
    """Shrink the font size (down to `min_size`) and, if it still doesn't
    fit on one line, word-wrap onto up to `max_lines` lines. Returns
    (font, [line1, line2, ...]) -- never truncates with an ellipsis, so
    small-canvas exports show the full value instead of cut-off text."""
    size = font.size
    current = font
    while size > min_size:
        bbox = draw.textbbox((0, 0), text, font=current)
        if bbox[2] - bbox[0] <= max_w:
            return current, [text]
        size -= 1
        current = _font(font_path, size)

    # Doesn't fit on one line even at min_size -- word-wrap at min_size.
    words = text.split(" ")
    lines = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=current)
        if bbox[2] - bbox[0] <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
        if len(lines) >= max_lines - 1:
            break
    remaining_idx = len(" ".join(lines).split(" ")) if lines else 0
    if line:
        lines.append(line)
    # append any leftover words to the last line (avoid silently dropping
    # words if wrapping stopped early due to max_lines)
    consumed = sum(len(l.split(" ")) for l in lines)
    if consumed < len(words):
        leftover = " ".join(words[consumed:])
        lines[-1] = f"{lines[-1]} {leftover}".strip()
        # re-shrink the last line's font if the merged leftover overflows
        while size > min_size - 4:
            bbox = draw.textbbox((0, 0), lines[-1], font=current)
            if bbox[2] - bbox[0] <= max_w:
                break
            size -= 1
            current = _font(font_path, size)
    return current, lines[:max_lines]


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
