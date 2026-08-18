"""
chart.py
Bar chart rendering engine matching the "Market Growth" sample style:
clean vertical bars, value labels on top, minimal axis, single accent color.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont


def _register_font(font_path=None):
    if font_path:
        try:
            fm.fontManager.addfont(font_path)
            return fm.FontProperties(fname=font_path).get_name()
        except Exception:
            pass
    return "DejaVu Sans"


def render_bar_chart(
    years,
    values,
    width_px=1000,
    height_px=650,
    bar_color="#0B2F7A",
    label_color="#0B2F7A",
    axis_color="#333333",
    grid_color="#D9E4F5",
    background="none",
    font_path=None,
    y_label="Market Value (USD Million)",
    y_label_color=None,
    value_fmt="{:.1f}",
    value_formatter=None,
    dpi=150,
    highlight_last=False,
    highlight_color="#173F99",
    labels_only_ends=False,
):
    """
    Render a bar chart (years on x-axis, values on y-axis) matching the
    sample dashboard style. Returns a PIL.Image (RGBA, transparent background
    unless `background` is set to a color).
    """
    font_name = _register_font(font_path)
    plt.rcParams["font.family"] = font_name

    fig_w, fig_h = width_px / dpi, height_px / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    if background == "none":
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)
    else:
        fig.patch.set_facecolor(background)
        ax.patch.set_facecolor(background)

    x = list(range(len(years)))
    colors = [bar_color] * len(values)
    if highlight_last and colors:
        colors[-1] = highlight_color

    bars = ax.bar(x, values, color=colors, width=0.55, zorder=3)

    # value labels on top of bars -- optionally only on the first and last
    # bar (matching reference style 2's minimal look) instead of every bar
    max_val = max(values) if values else 1
    last_idx = len(x) - 1
    for xi, v in zip(x, values):
        if labels_only_ends and xi not in (0, last_idx):
            continue
        label_text = value_formatter(v) if value_formatter else value_fmt.format(v)
        ax.text(
            xi, v + max_val * 0.02, label_text,
            ha="center", va="bottom", fontsize=max(8, int(width_px / 130)),
            fontweight="bold", color=label_color,
        )

    ax.set_xticks(x)
    # When there isn't enough horizontal room per category (small export
    # sizes, e.g. 800x350, or many bars), rotate the year labels so they
    # don't overlap into an unreadable smear.
    px_per_bar = width_px / max(1, len(x))
    tick_fontsize = max(7, int(width_px / 100))
    rotation = 0
    ha = "center"
    if px_per_bar < 55:
        rotation = 45
        ha = "right"
        tick_fontsize = max(6, int(tick_fontsize * 0.85))
    ax.set_xticklabels([str(y) for y in years], fontsize=tick_fontsize, color=axis_color,
                        rotation=rotation, ha=ha)
    ax.set_ylim(0, max_val * 1.18)

    # The y-axis label is a key data caption (units of the whole chart), so
    # it's colored to stand out more than the plain axis_color tick labels
    # -- its own (optionally distinct, more saturated) color instead of
    # relying on bold weight alone -- with only a mild size bump. A bigger
    # size jump was tried but pushed the rotated label past matplotlib's
    # tight-bbox estimate at small export widths (e.g. 800px), clipping it;
    # this formula matches the old size at small widths and only grows
    # noticeably at larger ones, where there's headroom to spare.
    ax.set_ylabel(
        y_label, fontsize=max(8, int(width_px / 100)),
        color=(y_label_color or axis_color), fontweight="bold", labelpad=8,
    )
    ax.tick_params(axis="y", labelsize=max(7, int(width_px / 120)), colors=axis_color)
    ax.grid(axis="y", color=grid_color, linewidth=1, zorder=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(axis_color)

    buf = io.BytesIO()
    # NOTE: deliberately no fig.tight_layout() call here -- combining it
    # with bbox_inches="tight" on save causes matplotlib to clip rotated
    # tick labels / the rotated y-axis label at small canvas sizes (the
    # two layout passes disagree on the true bounding box). bbox_inches
    # + a generous pad_inches alone reliably keeps everything on-canvas.
    fig.savefig(buf, format="png", dpi=dpi, transparent=(background == "none"),
                bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    return img


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _lerp_color(c0, c1, t):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def render_gradient_bar_chart(
    years,
    values,
    width_px=1400,
    height_px=650,
    color_top="#0B2F7A",
    color_bottom="#5FA3E0",
    axis_label_color="#1A2B4C",
    font_path=None,
    year_font_size=None,
    bar_width_ratio=0.55,
    corner_radius_ratio=0.10,
):
    """
    Pure-PIL bar chart with vertical-gradient-filled bars (dark at top,
    lighter at bottom, matching the minimal "Style 2" reference look) and
    year labels centered below each bar. No axis/gridlines and no per-bar
    value labels are drawn here -- the caller overlays its own start/end
    value callouts with connector lines using the returned bar geometry.

    Returns (PIL.Image RGBA, bar_tops) where bar_tops is a list of
    (x_center, y_top) pixel coordinates -- one per bar, in this image's own
    local coordinate space -- so the caller can position callouts/connector
    lines precisely against specific bars (typically the first and last).
    """
    top_rgb = _hex_to_rgb(color_top)
    bottom_rgb = _hex_to_rgb(color_bottom)

    n = len(values)
    max_val = max(values) if values else 1
    if max_val <= 0:
        max_val = 1

    try:
        year_font = ImageFont.truetype(font_path, year_font_size or max(14, int(width_px / 55))) if font_path else None
    except Exception:
        year_font = None
    if year_font is None:
        year_font = ImageFont.load_default()

    label_h = year_font.size + int(height_px * 0.035)
    plot_h = height_px - label_h
    plot_w = width_px

    canvas = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    slot_w = plot_w / n
    bar_w = slot_w * bar_width_ratio
    bar_tops = []

    for i, (year, val) in enumerate(zip(years, values)):
        cx = slot_w * i + slot_w / 2
        bar_h = max(2, (val / max_val) * plot_h * 0.96)
        x0, x1 = cx - bar_w / 2, cx + bar_w / 2
        y1 = plot_h
        y0 = plot_h - bar_h
        radius = min(bar_w * corner_radius_ratio, bar_h * 0.5, bar_w / 2)

        # vertical gradient fill, row by row, clipped to a rounded-top rect
        bar_img = Image.new("RGBA", (int(bar_w) + 1, int(bar_h) + 1), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_img)
        bh = bar_img.height
        for row in range(bh):
            t = row / max(1, bh - 1)
            color = _lerp_color(top_rgb, bottom_rgb, t)
            bar_draw.line([(0, row), (bar_img.width, row)], fill=color + (255,))
        mask = Image.new("L", bar_img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, bar_img.width - 1, bar_img.height - 1], radius=int(radius), fill=255)
        canvas.paste(bar_img, (int(x0), int(y0)), mask)

        # year label, centered below the bar
        year_text = str(year)
        ybbox = draw.textbbox((0, 0), year_text, font=year_font)
        yw = ybbox[2] - ybbox[0]
        draw.text((cx - yw / 2, plot_h + int(height_px * 0.015)), year_text,
                   fill=axis_label_color, font=year_font)

        bar_tops.append((cx, y0))

    return canvas, bar_tops
def render_donut_chart(
    labels,
    values=None,
    width_px=900,
    height_px=900,
    colors=None,
    hole_size=0.45,
    font_path=None,
    dpi=150,
):
    """
    Render a donut/ring chart matching the "Segmentation" sample style.
    If values is None, segments are rendered equally sized.
    Returns a PIL.Image (RGBA, transparent background).
    """
    font_name = _register_font(font_path)
    plt.rcParams["font.family"] = font_name

    n = len(labels)
    if values is None:
        values = [1] * n

    default_palette = ["#0B2F7A", "#159A9C", "#7A3FD1", "#E8791A", "#4C8C2B", "#C0392B"]
    if colors is None:
        colors = [default_palette[i % len(default_palette)] for i in range(n)]

    fig_w, fig_h = width_px / dpi, height_px / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=90,
        wedgeprops=dict(width=1 - hole_size, edgecolor="white", linewidth=3),
    )
    ax.set(aspect="equal")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    return img, colors
