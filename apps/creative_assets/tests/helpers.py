import io

from PIL import Image


def image_bytes(fmt="JPEG", size=(800, 600), color=(200, 120, 40), mode="RGB", **save_kwargs):
    image = Image.new(mode, size, color)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()
