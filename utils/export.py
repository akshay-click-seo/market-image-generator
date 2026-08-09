"""
export.py
Multi-format export of the final composed PIL.Image: PNG, WEBP, JPG, PDF.
Supports custom width x height (canvas is expected to already be built at
the target size by the calling template) and quality 50-100%.
"""

import io
import os


SIZE_PRESETS = {
    "800 x 350 (Banner)": (800, 350),
    "1200 x 630 (Social / OG)": (1200, 630),
    "1600 x 900 (Widescreen)": (1600, 900),
    "2400 x 1350 (HD Widescreen)": (2400, 1350),
    "3000 x 1688 (4K-ready)": (3000, 1688),
}


def export_image(image, fmt="PNG", quality=90, dest_path=None):
    """
    Export a PIL.Image to the requested format.

    Args:
        image: PIL.Image (RGBA or RGB)
        fmt: one of "PNG", "WEBP", "JPG"/"JPEG", "PDF"
        quality: 50-100, applies to WEBP/JPG/PDF-image-compression
        dest_path: if given, also writes to this path on disk

    Returns:
        bytes of the exported file
    """
    fmt = fmt.upper()
    if fmt == "JPG":
        fmt = "JPEG"

    buf = io.BytesIO()
    img = image

    if fmt in ("JPEG", "PDF"):
        # flatten transparency onto white background
        if img.mode in ("RGBA", "LA"):
            bg = img.convert("RGB")
            white = _flatten_on_white(img)
            img = white
        else:
            img = img.convert("RGB")

    save_kwargs = {}
    if fmt == "PNG":
        save_kwargs["optimize"] = True
    elif fmt == "WEBP":
        save_kwargs["quality"] = int(quality)
    elif fmt == "JPEG":
        save_kwargs["quality"] = int(quality)
        save_kwargs["optimize"] = True
    elif fmt == "PDF":
        save_kwargs["resolution"] = 150.0

    img.save(buf, format=fmt, **save_kwargs)
    data = buf.getvalue()

    if dest_path:
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)

    return data


def _flatten_on_white(img):
    from PIL import Image
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
    return background


def file_extension_for(fmt):
    fmt = fmt.upper()
    return {"PNG": "png", "WEBP": "webp", "JPG": "jpg", "JPEG": "jpg", "PDF": "pdf"}.get(fmt, "png")
