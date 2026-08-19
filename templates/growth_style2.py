"""
growth_style2.py
"Market Growth - Style 2" template: minimal layout with a left CAGR card,
a faint world-map watermark in the background, top-left/right value
callouts pointing to the first/last bars, and a bottom footer. Matches
sample image 2 (Plant-Based Protein Market in Mexico) layout.
"""

import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utils.chart import render_gradient_bar_chart
from utils.backgrounds import render_background
from utils.map import render_dotted_world_map
from utils.fonts import get_default_font_path
from utils.units import short_label
from utils.numfmt import format_money_parts, format_es_number_exact, format_es_percent
from utils.branding import resolve_logo_path, logo_variant_for_background


NAVY = "#0B2F7A"
BAR_TOP = "#0B2F7A"
BAR_BOTTOM = "#5FA3E0"
TEXT_DARK = "#1A2B4C"
GREY_TEXT = "#5B6B8C"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw, text, font, max_w):
    """Word-wrap text to fit within max_w, returning a list of lines (each
    line still needs centering by the caller)."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > max_w and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [text]


def _dotted_line(draw, xy0, xy1, fill, width=2, dot_gap=9):
    """Draw a dotted line from xy0 to xy1 (small round dots at regular
    intervals), matching the reference callout-to-bar connector style."""
    x0, y0 = xy0
    x1, y1 = xy1
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    steps = max(1, int(length / dot_gap))
    for i in range(steps + 1):
        t = i / steps
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        r = width / 2
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


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

    # faint STIPPLED/DOTTED world map watermark in the background, top-right
    # area (dots forming the landmass silhouettes, not solid fills) --
    # matches the reference design spec exactly.
    try:
        map_w, map_h = int(width * 0.62), int(height * 0.56)
        dot_spacing = max(4, int(width * 0.0055))
        map_img = render_dotted_world_map(
            width_px=map_w, height_px=map_h,
            dot_color="#C7D8F2", ocean_color=(0, 0, 0, 0),
            dot_spacing=dot_spacing, dot_radius=dot_spacing * 0.16,
        )
        canvas.alpha_composite(map_img, (int(width * 0.36), int(height * 0.06)))
    except Exception:
        pass

    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.03)
    center_x = width / 2

    # ---- Header logo (top-right) -- placed BEFORE the title so the
    # title's available width can be computed to avoid overlapping it. ----
    logo_left_x = width - margin
    resolved_logo_path = resolve_logo_path(logo_path, variant=logo_variant_for_background(background))
    if resolved_logo_path:
        try:
            logo = Image.open(resolved_logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.1), int(height * 0.06)), Image.LANCZOS)
            logo_x = width - margin - logo.width
            canvas.alpha_composite(logo, (logo_x, margin // 2))
            logo_left_x = logo_x
        except Exception:
            pass

    # ---- Title ----
    # Title is centered on the canvas, but a long market name must never be
    # allowed to run into the logo box on the right (or off the left edge)
    # -- constrain to a symmetric width around center_x sized by whichever
    # side is tighter (left margin vs. the logo), shrink the font if it's
    # still too wide, and finally wrap onto a 2nd line as a last resort.
    title_text = f"Tamaño del {market_name}"
    title_font = _font(font_bold, int(width * 0.026))
    title_pad = int(width * 0.015)
    max_title_w = 2 * min(center_x - margin, logo_left_x - title_pad - center_x)
    tbbox = draw.textbbox((0, 0), title_text, font=title_font)
    if tbbox[2] - tbbox[0] > max_title_w:
        title_font = _font(font_bold, int(width * 0.02))
        tbbox = draw.textbbox((0, 0), title_text, font=title_font)
    if tbbox[2] - tbbox[0] > max_title_w:
        title_lines = _wrap_text(draw, title_text, title_font, max_title_w)
    else:
        title_lines = [title_text]

    ty = margin * 0.7
    for line in title_lines:
        lbbox = draw.textbbox((0, 0), line, font=title_font)
        lw = lbbox[2] - lbbox[0]
        draw.text((center_x - lw / 2, ty), line, fill=NAVY, font=title_font)
        ty += title_font.size + int(height * 0.008)
    underline_y = ty + 6
    draw.line([(margin, underline_y), (width - margin, underline_y)], fill=NAVY, width=2)

    # Subtitle shows just the currency/unit -- the "Tamaño del Mercado"
    # wording is already in the main title above it, so repeating it here
    # would be redundant.
    subtitle_font = _font(font_medium, int(width * 0.015))
    subtitle = format_money_parts(currency, short_label(unit))
    sbbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw = sbbox[2] - sbbox[0]
    subtitle_y = underline_y + 16
    draw.text((center_x - sw / 2, subtitle_y), subtitle, fill=GREY_TEXT, font=subtitle_font)

    # ---- CAGR card (top-left) ----
    # CAGR is a DERIVED value (computed upstream from start/end via a
    # compounding formula), not something the user typed/pasted directly --
    # it essentially never comes out to a clean number, so it's kept at a
    # fixed, readable precision (unlike start/end, which are the user's own
    # exact figures and must never be rounded).
    cagr_display = format_es_percent(cagr, 2)
    card_w, card_h = int(width * 0.24), int(height * 0.16)
    # Normally a fixed fraction of height, but nudged down if a wrapped
    # (2-line) title pushed the subtitle lower than usual, so the card
    # never overlaps it.
    card_y = max(int(height * 0.18), int(subtitle_y + subtitle_font.size + int(height * 0.02)))
    card_x = margin
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                            radius=int(card_h * 0.14), outline=NAVY, width=3, fill="#FFFFFF")
    cagr_num_font = _font(font_bold, int(width * 0.032))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.14), cagr_display, fill=NAVY, font=cagr_num_font)
    cagr_label_font = _font(font_bold, int(width * 0.014))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.58), "CAGR", fill=TEXT_DARK, font=cagr_label_font)
    period_font = _font(font_medium, int(width * 0.013))
    draw.text((card_x + card_w * 0.08, card_y + card_h * 0.78),
              f"({base_year + 1}-{forecast_year})", fill=GREY_TEXT, font=period_font)

    # ---- Start / End value callouts (placed above the chart, connected to
    # the first/last bar with a dotted line) ----
    callout_font_val = _font(font_bold, int(width * 0.02))
    callout_font_label = _font(font_medium, int(width * 0.012))

    start_display = format_money_parts(currency, format_es_number_exact(start_value))
    end_display = format_money_parts(currency, format_es_number_exact(end_value))
    unit_word = short_label(unit)

    callout_y = int(height * 0.40)
    callout_text_h = callout_font_val.size + callout_font_label.size + 8

    # ---- Bar chart (bottom, full width), gradient-filled bars ----
    chart_w = int(width * 0.9)
    chart_x = margin
    chart_top = callout_y + callout_text_h + int(height * 0.05)
    chart_h = int(height * 0.98) - chart_top - int(height * 0.06)
    bar_img, bar_tops = render_gradient_bar_chart(
        years, values,
        width_px=chart_w, height_px=chart_h,
        color_top=BAR_TOP, color_bottom=BAR_BOTTOM,
        axis_label_color=TEXT_DARK, font_path=font_bold,
    )
    canvas.alpha_composite(bar_img, (chart_x, chart_top))

    first_bar_x, first_bar_y = bar_tops[0]
    last_bar_x, last_bar_y = bar_tops[-1]
    first_bar_x, first_bar_y = chart_x + first_bar_x, chart_top + first_bar_y
    last_bar_x, last_bar_y = chart_x + last_bar_x, chart_top + last_bar_y

    marker_r = max(3, int(width * 0.0035))

    # start value callout, above first (shortest) bar, dotted line down to
    # its top, ending in a small solid circular marker at the bar. The
    # first bar is short, so anchoring this label at the same fixed
    # callout_y as the end label (which sits right above the tall last
    # bar) left a long, disproportionate dotted line here -- instead keep
    # a short, fixed gap between this label and the actual bar top.
    start_x = chart_x + int(chart_w * 0.02)
    # Move the label DOWN (larger y) so it sits just above the short first
    # bar instead of at the same height as the end-of-chart label -- but
    # never past callout_y (that's still the ceiling other elements, like
    # the CAGR card, are laid out against).
    closest_start_callout_y = first_bar_y - callout_text_h - int(height * 0.05)
    start_callout_y = max(callout_y, closest_start_callout_y)
    draw.text((start_x, start_callout_y), start_display, fill=NAVY, font=callout_font_val)
    draw.text((start_x, start_callout_y + callout_font_val.size + 4), unit_word, fill=TEXT_DARK, font=callout_font_label)
    start_marker_xy = (first_bar_x, first_bar_y - 6)
    _dotted_line(draw, (start_x + 4, start_callout_y + callout_text_h + 6), start_marker_xy, fill=NAVY, width=4)
    draw.ellipse([start_marker_xy[0] - marker_r, start_marker_xy[1] - marker_r,
                  start_marker_xy[0] + marker_r, start_marker_xy[1] + marker_r], fill=NAVY)

    # end value callout, above last (tallest) bar, dotted line down to its
    # top, ending in a small solid circular marker at the bar
    end_bbox = draw.textbbox((0, 0), end_display, font=callout_font_val)
    ew = end_bbox[2] - end_bbox[0]
    end_x = chart_x + chart_w - ew - int(chart_w * 0.02)
    draw.text((end_x, callout_y), end_display, fill=NAVY, font=callout_font_val)
    unit_bbox = draw.textbbox((0, 0), unit_word, font=callout_font_label)
    uw = unit_bbox[2] - unit_bbox[0]
    draw.text((end_x, callout_y + callout_font_val.size + 4), unit_word, fill=TEXT_DARK, font=callout_font_label)
    end_marker_xy = (last_bar_x, last_bar_y - 6)
    _dotted_line(draw, (end_x + ew - 4, callout_y + callout_text_h + 6), end_marker_xy, fill=NAVY, width=4)
    draw.ellipse([end_marker_xy[0] - marker_r, end_marker_xy[1] - marker_r,
                  end_marker_xy[0] + marker_r, end_marker_xy[1] + marker_r], fill=NAVY)

    # ---- Footer ----
    footer_font = _font(font_bold, int(width * 0.016))
    draw.line([(0, height - int(height * 0.06)), (width, height - int(height * 0.06))], fill="#DDE6F5", width=2)
    fbbox = draw.textbbox((0, 0), website, font=footer_font)
    fw = fbbox[2] - fbbox[0]
    draw.text((center_x - fw / 2, height - int(height * 0.045)), website, fill=NAVY, font=footer_font)

    # (Logo already drawn in the header, top-right corner -- see above.)

    return canvas.convert("RGB")
