from pathlib import Path

from django.test import SimpleTestCase

from apps.website_analyzer.extract import MAX_TEXT_CHARS, extract_page, normalize_link

FIXTURES = Path(__file__).parent / "fixtures" / "site"
BASE = "https://mamaneema.example/"


class ExtractFixtureSiteTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.info = extract_page((FIXTURES / "index.html").read_bytes(), BASE, "utf-8")

    def test_metadata(self):
        self.assertEqual(self.info.title, "Mama Neema Catering | Chakula Dar es Salaam")
        self.assertEqual(
            self.info.meta_description,
            "Huduma ya chakula kwa sherehe na ofisi jijini Dar es Salaam.",
        )
        self.assertEqual(self.info.language, "sw")
        self.assertEqual(self.info.canonical_url, BASE)
        self.assertEqual(self.info.open_graph["title"], "Mama Neema Catering")
        self.assertEqual(self.info.open_graph["image"], BASE + "images/logo.png")

    def test_structured_data(self):
        self.assertEqual(len(self.info.structured_data), 1)
        self.assertEqual(self.info.structured_data[0]["@type"], "LocalBusiness")
        self.assertEqual(self.info.structured_data[0]["telephone"], "+255 700 000 000")

    def test_headings(self):
        self.assertEqual(
            self.info.headings,
            [{"level": 1, "text": "Karibu Mama Neema Catering"}, {"level": 2, "text": "Why choose us"}],
        )

    def test_main_text_excludes_scripts_styles_navigation_and_footer(self):
        self.assertIn("Tunapika pilau, biriani na chapati", self.info.text)
        for unwanted in ["tracking", "color: red", "Kuhusu sisi", "Footer text"]:
            with self.subTest(unwanted=unwanted):
                self.assertNotIn(unwanted, self.info.text)

    def test_prompt_injection_text_is_kept_as_plain_page_text(self):
        # Stored verbatim as observed content; it is never treated as an
        # instruction and nothing else in the extraction changes because of it.
        self.assertIn("Ignore all previous instructions", self.info.text)
        self.assertNotIn("award", self.info.title + self.info.meta_description)

    def test_images_are_absolute_and_skip_inline_data(self):
        self.assertEqual(
            self.info.images, [{"url": BASE + "images/pilau.jpg", "alt": "Pilau ya nyama"}]
        )

    def test_links_are_absolute_and_skip_mailto_and_nofollow(self):
        urls = [link["url"] for link in self.info.links]
        self.assertIn(BASE + "kuhusu.html", urls)
        self.assertIn("https://www.facebook.com/mamaneema", urls)
        self.assertFalse(any(url.startswith("mailto:") for url in urls))
        self.assertNotIn(BASE + "sponsored.html", urls)


class ExtractRobustnessTests(SimpleTestCase):
    def test_page_with_no_metadata(self):
        info = extract_page(b"<p>Just text</p>", BASE)

        self.assertEqual(info.title, "")
        self.assertEqual(info.meta_description, "")
        self.assertEqual(info.text, "Just text")

    def test_broken_html_does_not_raise(self):
        info = extract_page(b"<html><title>Broken<body><p>Unclosed <b>tags <div>", BASE)
        self.assertIn("Unclosed", info.text)

    def test_invalid_json_ld_is_ignored(self):
        html = b'<script type="application/ld+json">{not json</script><p>ok</p>'
        self.assertEqual(extract_page(html, BASE).structured_data, [])

    def test_json_ld_graph_is_flattened(self):
        html = (b'<script type="application/ld+json">{"@graph": [{"@type": "Organization"},'
                b' {"@type": "WebSite"}]}</script>')
        types = [item["@type"] for item in extract_page(html, BASE).structured_data]
        self.assertEqual(types, ["Organization", "WebSite"])

    def test_non_utf8_charset_is_decoded(self):
        html = "<title>Café Zanzibar</title>".encode("latin-1")
        self.assertEqual(extract_page(html, BASE, "iso-8859-1").title, "Café Zanzibar")

    def test_long_text_is_truncated_and_flagged(self):
        html = ("<p>" + "neno " * 10_000 + "</p>").encode()
        info = extract_page(html, BASE)
        self.assertEqual(len(info.text), MAX_TEXT_CHARS)
        self.assertTrue(info.text_truncated)

    def test_html_in_text_is_not_preserved_as_markup(self):
        info = extract_page(b"<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>", BASE)
        self.assertEqual(info.text, "<script>alert(1)</script>")  # escaped again when displayed


class NormalizeLinkTests(SimpleTestCase):
    def test_cases(self):
        cases = {
            "/about#team": BASE + "about",
            "about?x=1": BASE + "about?x=1",
            "HTTPS://MamaNeema.Example/A": "https://mamaneema.example/A",
            "javascript:alert(1)": "",
            "tel:+255700": "",
            "ftp://files.example/": "",
            "#top": "",
            "": "",
        }
        for href, expected in cases.items():
            with self.subTest(href=href):
                self.assertEqual(normalize_link(BASE, href), expected)
