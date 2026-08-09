"""
backgrounds.py
Programmatic generation of canvas background styles: Classic Blue, Modern
White, Gradient, Light, Dark, and Custom (solid color or uploaded image).
"""

from PIL import Image, ImageDraw


PRESETS = {
    "Classic Blue": {"type": "solid", "color": (222, 236, 250, 255)},
    "Modern White": {"type": "solid", "color": (255, 255, 255, 255)},
    "Gradient": {"type": "gradient", "top": (222, 236, 250, 255), "bottom": (179, 209, 240, 255)},
    "Light": {"type": "solid", "color": (247, 249, 252, 255)},
    "Dark": {"type": "solid", "color": (14, 22, 40, 255)},
}


def _vertical_gradient(size, top_color, bottom_color):
    w, h = size
    base = Image.new("RGBA", size, top_color)
    top = Image.new("RGBA", size, top_color)
    bottom = Image.new("RGBA", size, bottom_color)
    mask = Image.new("L", size)
    mask_data = []
    for y in range(h):
        mask_data.extend([int(255 * (y / max(h - 1, 1)))] * w)
    mask.putdata(mask_data)
    base.paste(bottom, (0, 0), mask)
    return base


def render_background(name_or_config, size):
    """
    Render a background canvas of the given size.

    name_or_config: either a preset name (str) from PRESETS, or a dict:
        {"type": "solid", "color": (r,g,b,a)}
        {"type": "gradient", "top": (...), "bottom": (...)}
        {"type": "image", "path": "..."}   # custom uploaded background
    """
    if isinstance(name_or_config, str):
        config = PRESETS.get(name_or_config, PRESETS["Modern White"])
    else:
        config = name_or_config

    if config["type"] == "solid":
        return Image.new("RGBA", size, config["color"])
    elif config["type"] == "gradient":
        img = _vertical_gradient(size, config["top"], config["bottom"])
        return img
    elif config["type"] == "image":
        img = Image.open(config["path"]).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return img
    else:
        return Image.new("RGBA", size, (255, 255, 255, 255))


def list_preset_names():
    return list(PRESETS.keys()) + ["Custom"]
