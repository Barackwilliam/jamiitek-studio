"""Drawing the still layers of each scene with Pillow.

Each scene has a background (a photo filling the frame, or a brand-colour
gradient) that FFmpeg slowly zooms, and a transparent text layer drawn on
top: the on-screen text near the top and the caption (the narration text)
at the bottom, each on a dark band so it stays readable over any photo.
"""

import io

from PIL import Image, ImageDraw

from apps.creative_assets.posters import (
    BOLD_FONT,
    REGULAR_FONT,
    photo_or_gradient,
    fit_text,
    hex_to_rgb,
    readable_text_color,
)

BAND_ALPHA = 165  # dark band behind text: white text stays above 4.5:1 on any photo


def background_layer(size, brand_color, photo_bytes=None):
    photo = Image.open(io.BytesIO(photo_bytes)) if photo_bytes else None
    return photo_or_gradient(size, hex_to_rgb(brand_color), photo)


def _band_text(layer, draw, lines, font, line_height, top, margin, fill=(255, 255, 255)):
    width = layer.width
    pad = int(font.size * 0.5)
    block_height = line_height * len(lines)
    draw.rectangle((0, top - pad, width, top + block_height + pad), fill=(0, 0, 0, BAND_ALPHA))
    for i, line in enumerate(lines):
        text_width = draw.textlength(line, font=font)
        draw.text(((width - text_width) / 2, top + i * line_height), line, font=font, fill=fill)


def text_layer(size, on_screen_text="", caption=""):
    """Transparent RGBA layer with the scene's texts."""
    width, height = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    short = min(size)
    margin = int(short * 0.07)
    if on_screen_text:
        font, lines = fit_text(draw, on_screen_text, BOLD_FONT, width - 2 * margin,
                                int(short * 0.085), int(short * 0.05), 3)
        line_height = int(font.size * 1.2)
        _band_text(layer, draw, lines, font, line_height, int(height * 0.12), margin)
    if caption:
        font, lines = fit_text(draw, caption, REGULAR_FONT, width - 2 * margin,
                                int(short * 0.05), int(short * 0.032), 3)
        line_height = int(font.size * 1.3)
        top = height - margin - line_height * len(lines)
        _band_text(layer, draw, lines, font, line_height, top, margin)
    return layer


def end_card(size, brand_color, call_to_action="", logo_bytes=None):
    """A closing frame: logo and call to action on the brand colour."""
    width, height = size
    brand = hex_to_rgb(brand_color)
    card = Image.new("RGB", size, brand)
    draw = ImageDraw.Draw(card)
    short = min(size)
    y = height // 2
    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        logo.thumbnail((int(width * 0.5), int(height * 0.22)))
        pad = int(short * 0.025)
        plate = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (255, 255, 255, 255))
        plate.alpha_composite(logo, (pad, pad))
        top = int(height * 0.5) - plate.height - int(short * 0.04)
        card.paste(plate, ((width - plate.width) // 2, max(int(short * 0.05), top)), plate)
    if call_to_action:
        font, lines = fit_text(draw, call_to_action, BOLD_FONT, width * 0.84,
                                int(short * 0.07), int(short * 0.04), 3)
        line_height = int(font.size * 1.25)
        color = readable_text_color(brand)
        for i, line in enumerate(lines):
            text_width = draw.textlength(line, font=font)
            draw.text(((width - text_width) / 2, y + i * line_height), line, font=font, fill=color)
    return card
