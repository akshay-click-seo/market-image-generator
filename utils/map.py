"""
map.py
World map rendering + country highlight/pin overlay utilities.

Approach: Render a static world map (equirectangular / PlateCarree projection)
from a bundled Natural Earth GeoJSON using matplotlib, then optionally
highlight a specific country in dark blue and drop a pin marker + label
box on it -- matching the "Regional Analysis" sample style.

The rendered map is cached to disk as PNG so repeated exports are fast.
"""

import json
import os
import hashlib
import io
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np
from PIL import Image

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
GEOJSON_PATH = os.path.join(ASSETS_DIR, "world_countries.geojson")
CACHE_DIR = os.path.join(ASSETS_DIR, "_map_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_GEOJSON_CACHE = None


def _load_geojson():
    global _GEOJSON_CACHE
    if _GEOJSON_CACHE is None:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            _GEOJSON_CACHE = json.load(f)
    return _GEOJSON_CACHE


def _strip_accents(s):
    """Normalize accented characters to their plain-ASCII equivalent, e.g.
    'México' -> 'mexico', so accented user input matches the (unaccented)
    GeoJSON NAME fields."""
    normalized = unicodedata.normalize("NFKD", s)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def find_country_feature(country_name_or_iso):
    """Find a country's GeoJSON feature by name, ISO_A2 or ISO_A3 code
    (case-insensitive, accent-insensitive)."""
    data = _load_geojson()
    q = _strip_accents(country_name_or_iso.strip().lower())
    best = None
    for feat in data["features"]:
        p = feat["properties"]
        candidates = [
            p.get("NAME", ""), p.get("NAME_LONG", ""), p.get("ADMIN", ""),
            p.get("NAME_EN", ""), p.get("BRK_NAME", ""), p.get("SOVEREIGNT", ""),
            p.get("ISO_A2", ""), p.get("ISO_A3", ""), p.get("ISO_A2_EH", ""), p.get("ISO_A3_EH", ""),
        ]
        candidates = [_strip_accents(c.lower()) for c in candidates if c]
        if q in candidates:
            return feat
        # partial fallback -- only for candidates long enough that a
        # substring match is meaningful (avoids e.g. Colombia's 2-letter
        # ISO code "CO" false-matching inside an unrelated query like
        # "mexico", which happens to contain the letters "c" and "o").
        if best is None:
            for c in candidates:
                if len(c) < 4:
                    continue
                if q and (q in c or c in q):
                    best = feat
                    break
    return best


def _iter_polygons(geometry):
    """Yield lists of (lon, lat) rings for Polygon / MultiPolygon geometries."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    if gtype == "Polygon":
        for ring in coords:
            yield ring
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                yield ring


def country_centroid(feature):
    """Rough centroid (lon, lat) of a country's largest ring, for pin placement."""
    best_ring = None
    best_area = -1
    for ring in _iter_polygons(feature["geometry"]):
        arr = np.array(ring)
        # shoelace area (unsigned) as a size proxy
        x, y = arr[:, 0], arr[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        if area > best_area:
            best_area = area
            best_ring = arr
    lon = best_ring[:, 0].mean()
    lat = best_ring[:, 1].mean()
    return float(lon), float(lat)


def render_world_map(
    width_px=1200,
    height_px=800,
    highlight_country=None,
    base_color="#AFCBEC",
    highlight_color="#0B2F7A",
    ocean_color="#FFFFFF",
    border_color="#FFFFFF",
    dpi=150,
    highlight_continent=True,
):
    """
    Render a flat world map PNG (PIL.Image, RGBA) with an optional highlighted
    country. Returns (image, pin_xy_px) where pin_xy_px is the pixel location
    (x, y) of the highlighted country's centroid within the returned image,
    or None if no country was highlighted / found.

    When `highlight_continent` is True (default) and a country is found, the
    entire continent it belongs to is filled with `highlight_color` (matching
    the reference "Regional Analysis" style, e.g. all of North America shown
    dark navy when the target country is Mexico) with the target country's
    pin placed precisely on it. Set False to highlight only the exact
    country polygon instead.
    """
    cache_key = hashlib.md5(
        f"{width_px}x{height_px}-{highlight_country}-{base_color}-{highlight_color}-{ocean_color}-{highlight_continent}".encode()
    ).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")

    data = _load_geojson()

    fig_w, fig_h = width_px / dpi, height_px / dpi
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(ocean_color)
    fig.patch.set_facecolor(ocean_color)

    target_feature = None
    if highlight_country:
        target_feature = find_country_feature(highlight_country)

    target_continent = None
    if target_feature is not None and highlight_continent:
        target_continent = target_feature["properties"].get("CONTINENT")

    patches = []
    highlight_patches = []
    for feat in data["features"]:
        is_target = target_feature is not None and feat is target_feature
        is_highlighted = is_target or (
            target_continent is not None and feat["properties"].get("CONTINENT") == target_continent
        )
        for ring in _iter_polygons(feat["geometry"]):
            poly = MplPolygon(np.array(ring), closed=True)
            if is_highlighted:
                highlight_patches.append(poly)
            else:
                patches.append(poly)

    ax.add_collection(PatchCollection(
        patches, facecolor=base_color, edgecolor=border_color, linewidths=0.6
    ))
    if highlight_patches:
        ax.add_collection(PatchCollection(
            highlight_patches, facecolor=highlight_color, edgecolor=border_color, linewidths=0.8, zorder=5
        ))

    ax.set_xlim(-170, 190)
    ax.set_ylim(-58, 85)
    ax.set_aspect(1.35)
    ax.axis("off")

    # Compute the pin's pixel position via matplotlib's own data->display
    # transform (ax.transData) BEFORE closing the figure, rather than a
    # hand-rolled linear formula across the full width_px/height_px. With
    # set_aspect() applied, the axes box is letterboxed/shrunk within the
    # figure to preserve the aspect ratio -- for aspect ratios far from the
    # default, this shifts the data horizontally within the figure by a
    # large margin, which a naive full-width linear formula ignores
    # entirely (it assumes the data spans edge-to-edge). transData reflects
    # the actual box matplotlib drew into, so it stays correct regardless
    # of how much letterboxing set_aspect introduces.
    pin_xy_raw = None
    if target_feature is not None:
        lon, lat = country_centroid(target_feature)
        fig.canvas.draw()  # ensure the transform reflects final layout
        disp_x, disp_y = ax.transData.transform((lon, lat))
        # transData uses a bottom-left origin; convert to top-left (image/PIL
        # convention) using the actual figure pixel height at save-time.
        fig_h_px = fig.get_size_inches()[1] * fig.dpi
        pin_xy_raw = (disp_x, fig_h_px - disp_y)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=ocean_color)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    raw_w, raw_h = img.size
    img = img.resize((width_px, height_px), Image.LANCZOS)

    pin_xy = None
    if pin_xy_raw is not None:
        # Scale the pin position from the pre-resize raw image's pixel
        # space into the final width_px/height_px space (the two can
        # differ by a pixel or two from dpi rounding).
        px = pin_xy_raw[0] / raw_w * width_px
        py = pin_xy_raw[1] / raw_h * height_px
        pin_xy = (px, py)

    return img, pin_xy


def render_dotted_world_map(
    width_px=1200,
    height_px=800,
    dot_color="#C7D8F2",
    ocean_color=(0, 0, 0, 0),
    dpi=150,
    dot_spacing=7,
    dot_radius=1.3,
):
    """
    Render a world map as a subtle stippled/dotted silhouette (dots arranged
    in the shape of each landmass, no solid fills or borders) -- matches the
    "Market Growth Style 2" background watermark spec: a very low-opacity
    dotted world map behind the chart. This is intentionally a separate
    function from render_world_map (which does solid country/continent
    fills for Regional Analysis) so that template is unaffected.

    Implementation: rasterize the solid land silhouette at high resolution
    to use purely as an alpha mask, then sample that mask on a regular grid
    and draw a small dot at every grid point that falls on land -- a classic
    halftone/stipple technique.
    """
    data = _load_geojson()

    # Render the solid silhouette larger than the target size (supersampled)
    # so the land/ocean mask has enough resolution to sample a fine dot grid
    # against, then we throw away the solid image itself.
    ss = 2
    mask_w, mask_h = width_px * ss, height_px * ss
    fig_w, fig_h = mask_w / dpi, mask_h / dpi
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor((0, 0, 0, 0))
    fig.patch.set_facecolor((0, 0, 0, 0))

    patches = []
    for feat in data["features"]:
        for ring in _iter_polygons(feat["geometry"]):
            patches.append(MplPolygon(np.array(ring), closed=True))
    ax.add_collection(PatchCollection(patches, facecolor="#000000", edgecolor="none"))

    ax.set_xlim(-170, 190)
    ax.set_ylim(-58, 85)
    ax.set_aspect(1.35)
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True)
    plt.close(fig)
    buf.seek(0)
    mask_img = Image.open(buf).convert("RGBA")
    mask_img = mask_img.resize((mask_w, mask_h), Image.LANCZOS)
    alpha = mask_img.split()[-1]  # land = opaque, ocean = transparent

    # Build the dotted output by sampling the mask on a regular grid.
    out = Image.new("RGBA", (width_px, height_px), ocean_color)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(out)
    alpha_px = alpha.load()
    r = dot_radius
    y = dot_spacing / 2
    row = 0
    while y < height_px:
        # offset alternating rows for a more natural, less grid-like stipple
        x_offset = (dot_spacing / 2) if (row % 2) else 0
        x = x_offset + dot_spacing / 2
        while x < width_px:
            mx, my = int(x * ss), int(y * ss)
            if 0 <= mx < mask_w and 0 <= my < mask_h and alpha_px[mx, my] > 80:
                draw.ellipse([x - r, y - r, x + r, y + r], fill=dot_color)
            x += dot_spacing
        y += dot_spacing
        row += 1

    return out


ISO2_TO_FLAG_EMOJI_BASE = 0x1F1E6
ISO2_A_ORD = ord('A')


def iso2_to_flag_emoji(iso2):
    """Convert an ISO 3166-1 alpha-2 code to a flag emoji (used as a lightweight
    fallback if no flag image asset is available)."""
    if not iso2 or len(iso2) != 2:
        return "🏳️"
    iso2 = iso2.upper()
    try:
        return "".join(chr(ISO2_TO_FLAG_EMOJI_BASE + (ord(c) - ISO2_A_ORD)) for c in iso2)
    except Exception:
        return "🏳️"


def get_country_iso2(country_name_or_iso):
    feat = find_country_feature(country_name_or_iso)
    if feat is None:
        return None
    return feat["properties"].get("ISO_A2") or feat["properties"].get("ISO_A2_EH")
