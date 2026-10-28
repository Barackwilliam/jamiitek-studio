"""Rendering marketing posters with Pillow, without any AI service.

Layout: the chosen photo fills the canvas (or a brand-colour gradient when
there is none), a dark gradient keeps text readable, the logo sits on a
white plate in the top corner, and the headline, supporting text and a
call-to-action button sit at the bottom. Text shrinks to fit. Fonts are
DejaVu Sans, bundled with its licence (apps/creative_assets/fonts).
"""

import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_DIR = Path(__file__).resolve().parent / "fonts"
REGULAR_FONT = FONT_DIR / "DejaVuSans.ttf"
BOLD_FONT = FONT_DIR / "DejaVuSans-Bold.ttf"
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def hex_to_rgb(value):
    if not HEX_COLOR.match(value or ""):
        raise ValueError("colour must look like #1a2b3c")
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def relative_luminance(rgb):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_text_color(background):
    """Black or white, whichever contrasts more with the background."""
    white, black = (255, 255, 255), (17, 17, 17)
    return white if contrast_ratio(background, white) >= contrast_ratio(background, black) else black


def _wrap(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def fit_text(draw, text, font_path, max_width, start_size, min_size, max_lines):
    size = start_size
    while True:
        font = ImageFont.truetype(str(font_path), size)
        lines = _wrap(draw, text, font, max_width)
        too_wide = any(draw.textlength(line, font=font) > max_width for line in lines)
        if (len(lines) <= max_lines and not too_wide) or size <= min_size:
            return font, lines[:max_lines]
        size -= 2


def photo_or_gradient(size, brand_rgb, photo):
    width, height = size
    if photo is not None:
        return ImageOps.fit(photo.convert("RGB"), size, method=Image.Resampling.LANCZOS)
    top = tuple(min(255, int(c * 1.15) + 20) for c in brand_rgb)
    bottom = tuple(int(c * 0.45) for c in brand_rgb)
    gradient = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(1, height - 1)
        gradient.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return gradient.resize(size)


def _shade(size, text_top):
    """Darken from just above the text to the bottom so white text stays readable.

    At the first line of text the shade is about 70% black, which keeps white
    text above a 4.5:1 contrast ratio even on a white photo.
    """
    width, height = size
    fade_start = max(0, text_top - int(min(size) * 0.18))
    mask = Image.new("L", (1, height), 0)
    for y in range(fade_start, height):
        if y < text_top:
            alpha = 180 * (y - fade_start) / max(1, text_top - fade_start)
        else:
            alpha = 180 + 45 * (y - text_top) / max(1, height - text_top)
        mask.putpixel((0, y), int(alpha))
    return mask.resize(size)


def render_poster(*, size, headline, subtext="", call_to_action="", brand_color="#0b6e4f",
                  photo_bytes=None, logo_bytes=None):
    """Return the poster as JPEG bytes."""
    width, height = size
    brand_rgb = hex_to_rgb(brand_color)
    photo = Image.open(io.BytesIO(photo_bytes)) if photo_bytes else None
    canvas = photo_or_gradient(size, brand_rgb, photo)

    draw = ImageDraw.Draw(canvas)
    margin = int(min(width, height) * 0.07)
    text_width = width - 2 * margin
    short_side = min(width, height)

    # Measure the text block from the bottom up before drawing anything.
    y = height - margin
    cta = None
    if call_to_action:
        font, lines = fit_text(draw, call_to_action, BOLD_FONT, text_width * 0.9,
                                int(short_side * 0.042), int(short_side * 0.028), 2)
        line_height = int(font.size * 1.25)
        pad_x, pad_y = int(font.size * 0.9), int(font.size * 0.55)
        box_width = int(max(draw.textlength(line, font=font) for line in lines)) + 2 * pad_x
        box_height = line_height * len(lines) + 2 * pad_y
        y -= box_height
        cta = (y, box_width, box_height, font, lines, line_height, pad_x, pad_y)
        y -= int(short_side * 0.04)

    sub = None
    if subtext:
        font, lines = fit_text(draw, subtext, REGULAR_FONT, text_width,
                                int(short_side * 0.04), int(short_side * 0.028), 3)
        line_height = int(font.size * 1.3)
        y -= line_height * len(lines)
        sub = (y, font, lines, line_height)
        y -= int(short_side * 0.03)

    head_font, head_lines = fit_text(draw, headline, BOLD_FONT, text_width,
                                      int(short_side * 0.085), int(short_side * 0.045), 3)
    head_line_height = int(head_font.size * 1.15)
    y -= head_line_height * len(head_lines)
    head_y = y
    bar_height = max(6, int(short_side * 0.012))
    bar_y = head_y - int(short_side * 0.03) - bar_height

    canvas = Image.composite(Image.new("RGB", size, (0, 0, 0)), canvas, _shade(size, bar_y))
    draw = ImageDraw.Draw(canvas)

    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        logo.thumbnail((int(width * 0.24), int(height * 0.12)))
        padding = int(short_side * 0.02)
        plate = Image.new("RGBA", (logo.width + 2 * padding, logo.height + 2 * padding), (255, 255, 255, 235))
        plate.alpha_composite(logo, (padding, padding))
        rounded = Image.new("L", plate.size, 0)
        ImageDraw.Draw(rounded).rounded_rectangle((0, 0, *plate.size), radius=padding, fill=255)
        canvas.paste(plate, (margin, margin), rounded)

    draw.rectangle((margin, bar_y, margin + int(short_side * 0.16), bar_y + bar_height), fill=brand_rgb)
    for i, line in enumerate(head_lines):
        draw.text((margin, head_y + i * head_line_height), line, font=head_font, fill=(255, 255, 255))
    if sub:
        sub_y, font, lines, line_height = sub
        for i, line in enumerate(lines):
            draw.text((margin, sub_y + i * line_height), line, font=font, fill=(235, 235, 235))
    if cta:
        cta_y, box_width, box_height, font, lines, line_height, pad_x, pad_y = cta
        draw.rounded_rectangle(
            (margin, cta_y, margin + box_width, cta_y + box_height),
            radius=box_height // 2 if len(lines) == 1 else pad_y, fill=brand_rgb,
        )
        color = readable_text_color(brand_rgb)
        for i, line in enumerate(lines):
            draw.text((margin + pad_x, cta_y + pad_y + i * line_height), line, font=font, fill=color)

    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", quality=90, optimize=True, progressive=True)
    return buffer.getvalue()
