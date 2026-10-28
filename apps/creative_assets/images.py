"""Validating and re-encoding images from users and websites.

A file's name, extension and declared type are never trusted. Pillow must
recognize it as an allowed format, its size and pixel count are limited to
prevent decompression bombs, and it is re-encoded into a fresh JPEG or PNG.
Re-encoding removes metadata such as GPS location and anything hidden in the
original file.
"""

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
MAX_PIXELS = 40_000_000
MAX_SIDE = 10_000
MIN_SIDE = 100
STORED_MAX_SIDE = 2400
THUMBNAIL_SIDE = 480

# Pillow refuses images above twice this pixel count (DecompressionBombError);
# set once for the process rather than per call, which would not be thread-safe.
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class InvalidImage(ValueError):
    """`message` is safe to show users."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    extension: str
    width: int
    height: int
    thumbnail: bytes
    original_format: str


def _encode(image, has_alpha):
    buffer = io.BytesIO()
    if has_alpha:
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "png"
    image.convert("RGB").save(buffer, format="JPEG", quality=88, optimize=True, progressive=True)
    return buffer.getvalue(), "jpg"


def process_image(data, max_bytes):
    """Return a ProcessedImage or raise InvalidImage."""
    if not data:
        raise InvalidImage("The file is empty.")
    if len(data) > max_bytes:
        raise InvalidImage(f"The image is larger than {max_bytes // (1024 * 1024)} MB.")

    try:
        with Image.open(io.BytesIO(data)) as probe:
            image_format = probe.format
            probe.verify()
        image = Image.open(io.BytesIO(data))
        if image.format not in ALLOWED_FORMATS or image_format not in ALLOWED_FORMATS:
            raise InvalidImage("Only JPEG, PNG, WebP and GIF images are supported.")
        width, height = image.size
        if width > MAX_SIDE or height > MAX_SIDE or width * height > MAX_PIXELS:
            raise InvalidImage("The image dimensions are too large.")
        image.seek(0)  # first frame of animated images
        image.load()
    except InvalidImage:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError):
        raise InvalidImage("This file is not a supported image, or it is too large.")
    except (OSError, SyntaxError, ValueError, EOFError):
        raise InvalidImage("The image is damaged or incomplete.")

    image = ImageOps.exif_transpose(image)
    if min(image.size) < MIN_SIDE:
        raise InvalidImage(f"The image is too small (at least {MIN_SIDE} × {MIN_SIDE} pixels).")

    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    image = image.convert("RGBA" if has_alpha else "RGB")
    image.thumbnail((STORED_MAX_SIDE, STORED_MAX_SIDE))
    content, extension = _encode(image, has_alpha)

    thumbnail = image.copy()
    thumbnail.thumbnail((THUMBNAIL_SIDE, THUMBNAIL_SIDE))
    thumbnail_bytes, _ext = _encode(thumbnail, has_alpha)

    return ProcessedImage(
        content=content, extension=extension, width=image.width, height=image.height,
        thumbnail=thumbnail_bytes, original_format=image_format,
    )
