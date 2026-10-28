import gettext
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from apps.marketing_content.models import ContentDraft, GenerationJob, MarketingBrief
from apps.projects.models import Project
from apps.website_analyzer.models import WebsiteAnalysis

LOCALE_DIR = Path(settings.BASE_DIR) / "locale" / "sw" / "LC_MESSAGES"


def po_entries(path):
    """Yield (msgid, [msgstr...]) from a .po file (enough for these checks)."""
    entry, field = None, None
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if not line.strip():
            if entry:
                yield entry
            entry, field = None, None
            continue
        if line.startswith("#"):
            continue
        match = re.match(r'^(msgctxt|msgid|msgid_plural|msgstr(?:\[\d\])?) "(.*)"$', line)
        if match:
            entry = entry or {}
            field = match.group(1)
            entry[field] = match.group(2)
        elif line.startswith('"') and entry is not None:
            entry[field] += line[1:-1]


class CatalogTests(TestCase):
    def test_every_message_is_translated(self):
        untranslated = [
            e["msgid"] for e in po_entries(LOCALE_DIR / "django.po")
            if e.get("msgid") and not all(v for k, v in e.items() if k.startswith("msgstr"))
        ]
        self.assertEqual(untranslated, [])

    def test_compiled_catalog_matches_the_source(self):
        # The .mo file is committed so Windows users need no gettext tools;
        # it must be recompiled whenever the .po file changes.
        with open(LOCALE_DIR / "django.mo", "rb") as handle:
            compiled = gettext.GNUTranslations(handle)
        for entry in po_entries(LOCALE_DIR / "django.po"):
            if not entry.get("msgid") or "msgid_plural" in entry:
                continue
            key = entry["msgid"]
            if "msgctxt" in entry:
                key = f"{entry['msgctxt']}\x04{key}"
            source = entry["msgstr"].encode().decode("unicode_escape").encode("latin-1").decode("utf-8")
            self.assertEqual(compiled._catalog.get(key.encode().decode("unicode_escape")
                                                   .encode("latin-1").decode("utf-8")), source, key)

    def test_placeholders_are_kept(self):
        for entry in po_entries(LOCALE_DIR / "django.po"):
            if not entry.get("msgid"):
                continue
            wanted = sorted(re.findall(r"%\(\w+\)", entry["msgid"]))
            for field, value in entry.items():
                if field.startswith("msgstr"):
                    self.assertEqual(sorted(re.findall(r"%\(\w+\)", value)), wanted, entry["msgid"])


class LanguageSwitchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("amina", password="test-pass-123!")
        cls.project = Project.objects.create(owner=cls.user, name="Duka", website_url="https://amina.example/")

    def switch_to_swahili(self):
        return self.client.post(reverse("set_language"), {"language": "sw", "next": "/projects/"})

    def test_switching_language_keeps_the_page_and_sets_a_cookie(self):
        response = self.switch_to_swahili()
        self.assertRedirects(response, "/projects/", fetch_redirect_response=False)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "sw")
        self.assertTrue(response.cookies[settings.LANGUAGE_COOKIE_NAME]["httponly"])

    def test_pages_render_in_swahili(self):
        self.switch_to_swahili()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="sw">')
        self.assertContains(response, "Geuza tovuti yako kuwa maudhui ya matangazo")
        self.assertContains(response, 'value="en"')  # Offers the way back.

        self.client.force_login(self.user)
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertContains(response, "Hatua za kuanza")
        self.assertContains(response, "Chambua tovuti yako")

    def test_unsafe_next_url_is_ignored(self):
        response = self.client.post(reverse("set_language"),
                                    {"language": "sw", "next": "https://evil.example/"})
        self.assertNotIn("evil.example", response.get("Location", ""))

    def test_stored_english_messages_are_shown_in_swahili(self):
        WebsiteAnalysis.objects.create(project=self.project, start_url=self.project.website_url,
                                       status="failed", error_message="We could not connect to the website.")
        brief = MarketingBrief.objects.create(project=self.project, objective="sales", audience="x",
                                              platform="instagram")
        GenerationJob.objects.create(brief=brief, kind="concepts", status="failed",
                                     error_message="The AI service is not responding right now. "
                                                   "Your work is saved; please try again later.")
        ContentDraft.objects.create(brief=brief, kind="concept", data={"title": "x"}, flags=[
            {"code": "unsupported_number", "location": "scene 2 voiceover", "text": "50%",
             "message": "The number “50%” is not in your confirmed information."}])
        self.client.force_login(self.user)
        self.switch_to_swahili()

        analysis = self.project.analyses.get()
        response = self.client.get(analysis.get_absolute_url())
        self.assertContains(response, "Hatukuweza kuunganishwa na tovuti.")
        response = self.client.get(brief.get_absolute_url())
        self.assertContains(response, "Huduma ya AI haijibu kwa sasa.")
        self.assertContains(response, "Namba “50%” haipo")
        self.assertContains(response, "onyesho 2, sauti ya msimulizi")

    def test_unknown_stored_messages_fall_back_to_the_original(self):
        with translation.override("sw"):
            message = "Some new message"  # A variable, so makemessages does not collect it.
            self.assertEqual(translation.gettext(message), message)


class PromptLanguageTests(TestCase):
    def test_prompts_and_fact_snapshots_stay_in_english_for_swahili_users(self):
        from apps.business_profiles.models import BusinessProfile, FactKey, ProfileFact
        from apps.marketing_content import prompts
        from apps.marketing_content.generation import confirmed_facts

        user = get_user_model().objects.create_user("amina", password="test-pass-123!")
        project = Project.objects.create(owner=user, name="Duka", business_details="x")
        profile = BusinessProfile.objects.create(project=project)
        ProfileFact.objects.create(profile=profile, key=FactKey.PHONE, value="0754 123 456",
                                   source="user", status="confirmed")
        brief = MarketingBrief.objects.create(project=project, objective="sales", audience="x",
                                              platform="instagram", tone="friendly")
        with translation.override("sw"):
            facts = confirmed_facts(project)
            prompt = prompts.concepts_prompt(brief, facts)
        self.assertEqual(facts[0]["label"], "Phone number")
        self.assertIn('"objective": "Increase sales"', prompt)
        self.assertIn('"tone": "Friendly"', prompt)
        self.assertNotIn("Kuongeza mauzo", prompt)
