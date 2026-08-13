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
from utils.branding import resolve_logo_path, logo_variant_for_background


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

    # Right-side info panel's horizontal bounds are needed up front so the
    # header logo can be sized to span this same width (matched below).
    panel_x = int(width * 0.735)
    panel_w = width - panel_x - margin

    # ---- Header ----
    # Top-right: the "Informes de Expertos" logo, resized to span the full
    # width of the right-side stat panel below it (not just a small
    # thumbnail), so it visually anchors that column. Uses a custom
    # uploaded logo image for this specific generation if one was
    # provided, otherwise falls back to the bundled default logo asset. A
    # text wordmark is drawn only if no logo image can be loaded at all,
    # as a last-resort fallback.
    brand_x = width - margin
    resolved_logo_path = resolve_logo_path(logo_path, variant=logo_variant_for_background(background))
    logo_drawn = False
    if resolved_logo_path:
        try:
            logo = Image.open(resolved_logo_path).convert("RGBA")
            max_logo_h = int(height * 0.16)
            logo_target_w = panel_w
            scale = logo_target_w / logo.width
            logo_h = int(logo.height * scale)
            if logo_h > max_logo_h:
                scale = max_logo_h / logo.height
                logo_target_w = int(logo.width * scale)
                logo_h = max_logo_h
            logo = logo.resize((logo_target_w, logo_h), Image.LANCZOS)
            logo_x = width - margin - logo.width
            canvas.alpha_composite(logo, (logo_x, int(height * 0.012)))
            brand_x = logo_x
            logo_drawn = True
        except Exception:
            pass
    if not logo_drawn:
        wordmark_color = "#FFFFFF" if logo_variant_for_background(background) == "white" else "#111111"
        wordmark_line1 = "informes"
        wordmark_line2 = "de expertos"
        wm_font1 = _font(font_bold, int(width * 0.021))
        wm_font2 = _font(font_bold, int(width * 0.021))
        b1 = draw.textbbox((0, 0), wordmark_line1, font=wm_font1)
        b2 = draw.textbbox((0, 0), wordmark_line2, font=wm_font2)
        w1, w2 = b1[2] - b1[0], b2[2] - b2[0]
        wm_w = max(w1, w2)
        wm_x = width - margin - wm_w
        wm_y = margin + int(height * 0.01)
        draw.text((wm_x + (wm_w - w1) / 2, wm_y), wordmark_line1, fill=wordmark_color, font=wm_font1)
        draw.text((wm_x + (wm_w - w2) / 2, wm_y + wm_font1.size + 2), wordmark_line2, fill=wordmark_color, font=wm_font2)
        brand_x = wm_x

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

    # ---- Right-side info panel geometry (computed before the chart so the
    # chart's height can be sized to reach down to the panel's actual
    # bottom edge -- i.e. the x-axis row lines up with the bottom of the
    # 3rd/last stat card instead of ending well above it). ----
    panel_top = max(int(height * 0.15), underline_y + int(height * 0.04))
    panel_bottom = height - int(height * 0.09)  # leave room for footer
    panel_pad = int(width * 0.01)

    card_x = panel_x + panel_pad
    card_w = panel_w - 2 * panel_pad
    card_gap = int(height * 0.02)
    card_h = int(height * 0.145)

    cagr_display = format_es_percent(cagr, 1)
    end_display = format_es_number(end_value, 1)
    start_display = format_es_number(start_value, 1)
    unit_label_full = short_label(unit)

    # Three stat cards -- CAGR, ending market size, starting market size --
    # matching the reference layout (the "Período de Pronóstico" 4th card
    # is intentionally omitted per explicit request).
    cards = [
        {
            "icon": "globe",
            "lines": [(f"CAGR {base_year+1} – {forecast_year}", TEXT_DARK, "small"),
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
    ]

    column_h = len(cards) * card_h + (len(cards) - 1) * card_gap
    panel_inner_h = column_h + 2 * panel_pad
    panel_h = min(panel_bottom - panel_top, max(panel_inner_h, int(height * 0.6)))
    panel_y = panel_top + max(0, (panel_bottom - panel_top - panel_h) // 2)
    panel_bottom_edge = panel_y + panel_h

    # ---- Chart area (left ~72%) ----
    chart_w = int(width * 0.68)
    chart_top = panel_top
    footer_top = height - int(height * 0.075)
    # Request a height tall enough that, after matplotlib's bbox_inches="tight"
    # crop (which shrinks the rendered image below the requested height_px --
    # empirically by roughly 12-15%), the chart's actual composited bottom
    # edge (x-axis row) lands at the panel's own bottom edge, instead of
    # ending well above the last stat card. Capped so it still can't overlap
    # the footer at small canvas sizes.
    target_bottom = min(panel_bottom_edge, footer_top - int(height * 0.02))
    chart_h = int((target_bottom - chart_top) * 1.15)
    chart_h = min(chart_h, footer_top - chart_top - int(height * 0.02))
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

    # ---- Right-side info panel ----
    # A tall rounded outer panel with a thick navy border; four separate
    # white cards are stacked vertically INSIDE it (not floating loose on
    # the canvas), matching the reference design. (panel_x / panel_w /
    # panel_y / panel_h were already computed above, before the chart, so
    # the chart's height could be matched to the panel's bottom edge.)

    # Outer container: white fill, thick navy border, rounded corners.
    outer_border_w = max(3, int(width * 0.0035))
    draw.rounded_rectangle(
        [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
        radius=int(panel_w * 0.06), fill=CARD_BG, outline=NAVY, width=outer_border_w,
    )

    column_top = panel_y + max(panel_pad, (panel_h - column_h) // 2)

    big_font = _font(font_bold, int(width * 0.021))
    small_font = _font(font_medium, int(width * 0.013))

    # The four cards inside the panel use a thin light-blue border (not the
    # thick navy one) since the outer panel already provides the strong
    # boundary -- avoids a "double border" look.
    y = column_top
    for card in cards:
        _draw_stat_card(
            canvas, draw, card_x, y, card_w, card_h, card["icon"], card["lines"], big_font, small_font, font_bold,
            divider=card.get("divider", False), border_color="#DCE6F5", border_w=max(1, int(card_h * 0.02)),
        )
        y += card_h + card_gap

    # ---- Decorative wave shape, bottom-left corner ----
    _draw_corner_wave(canvas, width, height)

    return canvas.convert("RGB")


def _draw_corner_wave(canvas, width, height):
    """Subtle abstract light-blue curved wave shape in the bottom-left
    corner, purely decorative (matches the reference design)."""
    wave_w = int(width * 0.22)
    wave_h = int(height * 0.16)
    wave_layer = Image.new("RGBA", (wave_w, wave_h), (0, 0, 0, 0))
    wdraw = ImageDraw.Draw(wave_layer)

    # Two overlapping soft curves, layered light-blue, for a gentle
    # abstract-wave look without any hard edges.
    wdraw.ellipse([-wave_w * 0.5, wave_h * 0.25, wave_w * 0.9, wave_h * 2.1],
                  fill=(179, 209, 240, 90))
    wdraw.ellipse([-wave_w * 0.65, wave_h * 0.55, wave_w * 0.65, wave_h * 2.1],
                  fill=(140, 181, 227, 90))

    canvas.alpha_composite(wave_layer, (0, height - wave_h))


def _draw_stat_card(canvas, draw, x, y, w, h, icon_name, lines, big_font, small_font, font_bold_path,
                     divider=False, border_color=None, border_w=None):
    radius = int(h * 0.18)
    if border_color is None:
        border_color = NAVY
    if border_w is None:
        border_w = max(2, int(h * 0.035))
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=CARD_BG, outline=border_color, width=border_w)

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
