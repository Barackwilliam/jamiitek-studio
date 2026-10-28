import io

from django.test import SimpleTestCase
from PIL import Image

from apps.creative_assets.images import InvalidImage, process_image
from apps.creative_assets.posters import contrast_ratio, readable_text_color, render_poster

from .helpers import image_bytes

LIMIT = 8 * 1024 * 1024


class ProcessImageTests(SimpleTestCase):
    def test_accepts_common_formats(self):
        for fmt in ["JPEG", "PNG", "WEBP", "GIF"]:
            with self.subTest(fmt=fmt):
                processed = process_image(image_bytes(fmt), LIMIT)
                self.assertEqual((processed.width, processed.height), (800, 600))
                self.assertEqual(processed.extension, "jpg")
                thumb = Image.open(io.BytesIO(processed.thumbnail))
                self.assertLessEqual(max(thumb.size), 480)

    def test_transparency_is_kept_as_png(self):
        processed = process_image(image_bytes("PNG", mode="RGBA", color=(0, 0, 0, 0)), LIMIT)
        self.assertEqual(processed.extension, "png")
        self.assertEqual(Image.open(io.BytesIO(processed.content)).mode, "RGBA")

    def test_metadata_is_removed_and_orientation_applied(self):
        exif = Image.Exif()
        exif[0x0112] = 6                 # orientation: rotate 90 degrees
        exif[0x010F] = "SecretCam"       # camera make
        exif.get_ifd(0x8825)[2] = (6.0, 48.0, 0.0)   # GPS latitude
        data = image_bytes("JPEG", size=(800, 400), exif=exif.tobytes())

        processed = process_image(data, LIMIT)

        result = Image.open(io.BytesIO(processed.content))
        self.assertEqual(result.size, (400, 800))
        self.assertEqual(len(result.getexif()), 0)
        self.assertNotIn(b"SecretCam", processed.content)

    def test_large_images_are_scaled_down(self):
        processed = process_image(image_bytes("JPEG", size=(5000, 2500)), LIMIT)
        self.assertEqual((processed.width, processed.height), (2400, 1200))

    def test_rejected_files(self):
        valid_jpeg = image_bytes("JPEG")
        cases = {
            "empty": b"",
            "text pretending to be an image": b"hello, I am not a picture",
            "html": b"<html><script>alert(1)</script></html>",
            "svg": b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            "truncated jpeg": valid_jpeg[: len(valid_jpeg) // 3],
            "bmp format": image_bytes("BMP"),
            "too small": image_bytes("PNG", size=(50, 50)),
            "too wide": image_bytes("PNG", size=(11000, 120), mode="1", color=0),
            "decompression bomb": image_bytes("PNG", size=(9500, 9500), mode="1", color=0),
        }
        for name, data in cases.items():
            with self.subTest(name), self.assertRaises(InvalidImage) as ctx:
                process_image(data, LIMIT)
            self.assertTrue(ctx.exception.message)

    def test_byte_limit(self):
        with self.assertRaises(InvalidImage):
            process_image(image_bytes("PNG"), max_bytes=100)


class PosterTests(SimpleTestCase):
    def render(self, **kwargs):
        options = {"size": (1080, 1080), "headline": "Karibu Mama Neema Catering"}
        options.update(kwargs)
        return Image.open(io.BytesIO(render_poster(**options)))

    def test_all_formats_render_at_exact_size(self):
        for size in [(1080, 1080), (1080, 1920), (1920, 1080)]:
            with self.subTest(size=size):
                poster = self.render(size=size, subtext="Pilau na biriani", call_to_action="Piga 0712 345 678",
                                     photo_bytes=image_bytes("JPEG", size=(1600, 900)),
                                     logo_bytes=image_bytes("PNG", size=(400, 200), mode="RGBA", color=(0, 90, 60, 255)))
                self.assertEqual(poster.size, size)
                self.assertEqual(poster.format, "JPEG")

    def test_very_long_text_still_renders(self):
        poster = self.render(headline="Neno " * 60, subtext="Maelezo " * 50, call_to_action="Wasiliana " * 15)
        self.assertEqual(poster.size, (1080, 1080))

    def test_text_area_stays_readable_on_a_white_photo(self):
        poster = self.render(photo_bytes=image_bytes("JPEG", color=(255, 255, 255))).convert("RGB")
        # Bottom-left margin beside the text has the same shading as behind it.
        brightest = max(poster.crop((0, 760, 30, 1080)).get_flattened_data(), key=sum)
        self.assertGreaterEqual(contrast_ratio((255, 255, 255), brightest), 4.5)

    def test_button_text_colour_contrasts_with_brand_colour(self):
        for color in [(245, 217, 10), (11, 110, 79), (255, 255, 255), (0, 0, 0), (200, 30, 30)]:
            with self.subTest(color=color):
                self.assertGreaterEqual(contrast_ratio(color, readable_text_color(color)), 4.5)

    def test_invalid_colour_is_rejected(self):
        with self.assertRaises(ValueError):
            render_poster(size=(1080, 1080), headline="x", brand_color="red; drop table")
