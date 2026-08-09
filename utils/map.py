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


def find_country_feature(country_name_or_iso):
    """Find a country's GeoJSON feature by name, ISO_A2 or ISO_A3 code (case-insensitive)."""
    data = _load_geojson()
    q = country_name_or_iso.strip().lower()
    best = None
    for feat in data["features"]:
        p = feat["properties"]
        candidates = [
            p.get("NAME", ""), p.get("NAME_LONG", ""), p.get("ADMIN", ""),
            p.get("NAME_EN", ""), p.get("BRK_NAME", ""), p.get("SOVEREIGNT", ""),
            p.get("ISO_A2", ""), p.get("ISO_A3", ""), p.get("ISO_A2_EH", ""), p.get("ISO_A3_EH", ""),
        ]
        candidates = [c.lower() for c in candidates if c]
        if q in candidates:
            return feat
        # partial fallback
        if best is None:
            for c in candidates:
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
):
    """
    Render a flat world map PNG (PIL.Image, RGBA) with an optional highlighted
    country. Returns (image, pin_xy_px) where pin_xy_px is the pixel location
    (x, y) of the highlighted country's centroid within the returned image,
    or None if no country was highlighted / found.
    """
    cache_key = hashlib.md5(
        f"{width_px}x{height_px}-{highlight_country}-{base_color}-{highlight_color}-{ocean_color}".encode()
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

    patches = []
    highlight_patches = []
    for feat in data["features"]:
        is_target = target_feature is not None and feat is target_feature
        for ring in _iter_polygons(feat["geometry"]):
            poly = MplPolygon(np.array(ring), closed=True)
            if is_target:
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

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=ocean_color)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    img = img.resize((width_px, height_px), Image.LANCZOS)

    pin_xy = None
    if target_feature is not None:
        lon, lat = country_centroid(target_feature)
        # Convert data coords -> pixel coords using the axes limits set above
        x0, x1 = -170, 190
        y0, y1 = -58, 85
        px = (lon - x0) / (x1 - x0) * width_px
        py = (1 - (lat - y0) / (y1 - y0)) * height_px
        pin_xy = (px, py)

    return img, pin_xy


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
