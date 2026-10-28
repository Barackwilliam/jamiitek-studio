from django.test import SimpleTestCase

from apps.marketing_content.validation import (
    InvalidOutput,
    clean_concepts,
    clean_script,
    find_unsupported_claims,
    parse_json_object,
    script_texts,
)

FACTS = [
    {"ref": "F1", "label": "Business name", "value": "Mama Neema Catering"},
    {"ref": "F2", "label": "Price", "value": "Chakula cha harusi: TZS 15000"},
    {"ref": "F3", "label": "Phone number", "value": "0712 345 678"},
]
REFS = {"F1", "F2", "F3"}


def flags_for(text):
    return find_unsupported_claims([("caption", text)], FACTS)


class ParseTests(SimpleTestCase):
    def test_plain_and_fenced_json(self):
        self.assertEqual(parse_json_object('{"a": 1}'), {"a": 1})
        self.assertEqual(parse_json_object('```json\n{"a": 1}\n```'), {"a": 1})

    def test_rejects_non_objects(self):
        for text in ["", "hello", "[1, 2]", '{"a": ']:
            with self.subTest(text=text), self.assertRaises(InvalidOutput):
                parse_json_object(text)


class CleanTests(SimpleTestCase):
    def test_concepts_are_limited_and_unknown_refs_removed(self):
        data = {"concepts": [
            {"title": f"C{i}", "angle": "a", "key_message": "k", "fact_ids": ["F1", "F9", 3]}
            for i in range(5)
        ]}

        concepts, unknown = clean_concepts(data, REFS)

        self.assertEqual(len(concepts), 3)
        self.assertEqual(concepts[0]["fact_ids"], ["F1"])
        self.assertIn("F9", unknown)

    def test_concept_missing_required_text_is_invalid(self):
        with self.assertRaises(InvalidOutput):
            clean_concepts({"concepts": [{"title": "x"}]}, REFS)
        with self.assertRaises(InvalidOutput):
            clean_concepts({"ideas": []}, REFS)

    def test_script_cleaning(self):
        data = {
            "title": "  Harusi   yako ",
            "scenes": [
                {"voiceover": "Karibu", "on_screen_text": "x" * 200, "visual": "Picha",
                 "duration_seconds": 500, "fact_ids": ["F1"]},
                {"voiceover": "Piga simu", "duration_seconds": "5"},
            ],
            "hashtags": ["#Harusi", "harusi", "Dar es Salaam!", 7],
            "fact_ids": ["F3", "F3"],
        }

        script, unknown = clean_script(data, REFS)

        self.assertEqual(script["title"], "Harusi yako")
        self.assertEqual(len(script["scenes"][0]["on_screen_text"]), 80)
        self.assertEqual(script["scenes"][0]["duration_seconds"], 5)
        self.assertEqual(script["scenes"][1]["duration_seconds"], 5)
        self.assertEqual(script["hashtags"], ["Harusi", "harusi", "DaresSalaam"])
        self.assertEqual(script["fact_ids"], ["F3"])
        self.assertEqual(unknown, [])

    def test_script_without_text_is_invalid(self):
        with self.assertRaises(InvalidOutput):
            clean_script({"title": "x", "scenes": [{"visual": "only a picture"}]}, REFS)


class ClaimCheckTests(SimpleTestCase):
    def test_numbers_from_facts_are_allowed(self):
        self.assertEqual(flags_for("Harusi kwa TZS 15000 tu. Piga 0712 345 678."), [])

    def test_partial_number_match_is_not_enough(self):
        flags = flags_for("Kuanzia 15 kwa sahani")
        self.assertEqual([f["text"] for f in flags], ["15"])

    def test_invented_numbers_are_flagged(self):
        texts = {f["text"] for f in flags_for("Punguzo la 20% kwa wateja 500 tangu 2010")}
        self.assertTrue({"20", "500", "2010"} <= texts)

    def test_risky_phrases_in_english_and_kiswahili(self):
        for text, phrase in [
            ("The best caterer in town", "best"),
            ("Award-winning food", "award"),
            ("Guaranteed satisfaction", "guaranteed"),
            ("Chakula bora zaidi Dar", "bora zaidi"),
            ("Tumeshinda tuzo", "tuzo"),
            ("Ladha ya uhakika", "uhakika"),
            ("Punguzo kwa wiki hii", "punguzo"),
        ]:
            with self.subTest(text=text):
                self.assertIn(phrase, [f["text"] for f in flags_for(text)])

    def test_harmless_creative_text_is_not_flagged(self):
        self.assertEqual(flags_for("Karibu ufurahie ladha ya nyumbani na Mama Neema Catering"), [])

    def test_whole_words_only(self):
        # "bestow" contains "best"; "free" inside "freedom".
        self.assertEqual(flags_for("We bestow freedom of choice"), [])

    def test_phrase_supported_by_facts_is_not_flagged(self):
        facts = FACTS + [{"ref": "F4", "label": "Other", "value": "Winner of the best caterer award 2024"}]
        flags = find_unsupported_claims([("caption", "Best caterer award 2024 winner")], facts)
        self.assertEqual(flags, [])

    def test_script_texts_cover_all_visible_fields(self):
        script = {"title": "T", "headline": "H", "caption": "C", "call_to_action": "A",
                  "scenes": [{"voiceover": "V", "on_screen_text": "O", "visual": "not checked"}],
                  "hashtags": ["Tag"]}
        self.assertEqual([t for _, t in script_texts(script)], ["T", "H", "C", "A", "V", "O", "Tag"])
