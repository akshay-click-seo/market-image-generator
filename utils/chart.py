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
from PIL import Image


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
    value_fmt="{:.1f}",
    value_formatter=None,
    dpi=150,
    highlight_last=False,
    highlight_color="#173F99",
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

    # value labels on top of bars
    max_val = max(values) if values else 1
    for xi, v in zip(x, values):
        label_text = value_formatter(v) if value_formatter else value_fmt.format(v)
        ax.text(
            xi, v + max_val * 0.02, label_text,
            ha="center", va="bottom", fontsize=max(9, int(width_px / 90)),
            fontweight="bold", color=label_color,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=max(9, int(width_px / 100)), color=axis_color)
    ax.set_ylim(0, max_val * 1.18)

    ax.set_ylabel(y_label, fontsize=max(9, int(width_px / 100)), color=axis_color, fontweight="bold")
    ax.tick_params(axis="y", labelsize=max(8, int(width_px / 110)), colors=axis_color)
    ax.grid(axis="y", color=grid_color, linewidth=1, zorder=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(axis_color)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=(background == "none"))
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    return img


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
