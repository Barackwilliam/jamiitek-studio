"""Turning a website analysis into suggested profile facts.

Only information that is written on the website is suggested, each with the
page and the part of the page it came from. Nothing is inferred, translated,
summarized or invented: a suggestion is a quotation the user must review.
Structured data (JSON-LD) and standard meta tags are preferred; page text is
used only for clearly shaped values such as phone numbers and email
addresses, and for list lines on pages that describe services or products.
"""

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from django.db import transaction

from apps.website_analyzer.models import AnalyzedPage

from .models import BusinessProfile, FactKey, ProfileFact, max_length_for, normalize_value

BUSINESS_TYPES = {
    "organization", "corporation", "localbusiness", "store", "restaurant", "foodestablishment",
    "hotel", "lodgingbusiness", "travelagency", "professionalservice", "educationalorganization",
    "medicalbusiness", "ngo", "onlinestore", "autodealer", "homeandconstructionbusiness",
}
OFFERING_TYPES = {"product", "service", "menuitem", "course", "offer", "trip", "event"}

SOCIAL_HOSTS = {
    "facebook.com": "Facebook", "instagram.com": "Instagram", "x.com": "X", "twitter.com": "X",
    "tiktok.com": "TikTok", "youtube.com": "YouTube", "linkedin.com": "LinkedIn",
    "wa.me": "WhatsApp", "whatsapp.com": "WhatsApp", "pinterest.com": "Pinterest",
}
SOCIAL_NON_PROFILE_PATHS = ("/sharer", "/share", "/intent", "/dialog", "/plugins", "/watch")

OFFERING_PAGE_WORDS = ("service", "huduma", "product", "bidhaa", "menu", "shop", "duka",
                       "packages", "courses", "rooms", "tours")

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERNS = [
    re.compile(r"\+\d{1,3}[\s.-]?\(?\d{2,4}\)?(?:[\s.-]?\d{2,4}){2,3}"),  # international
    re.compile(r"(?<!\d)0[67]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}(?!\d)"),        # Tanzanian mobile
]
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
TITLE_SEPARATORS = re.compile(r"\s+[|\-–—·:]\s+")

MAX_SUGGESTIONS_PER_KEY = 15


@dataclass
class Suggestion:
    key: str
    value: str
    evidence: list = field(default_factory=list)


class SuggestionCollector:
    def __init__(self):
        self._by_identity = {}

    def add(self, key, value, url, detail):
        value = " ".join(str(value or "").split())
        if not value:
            return
        value = value[: max_length_for(key)]
        identity = (key, normalize_value(value))
        suggestion = self._by_identity.get(identity)
        if suggestion is None:
            if sum(1 for k, _ in self._by_identity if k == key) >= MAX_SUGGESTIONS_PER_KEY:
                return
            suggestion = Suggestion(key=key, value=value)
            self._by_identity[identity] = suggestion
        item = {"url": url, "detail": detail}
        if item not in suggestion.evidence:
            suggestion.evidence.append(item)

    def results(self):
        return list(self._by_identity.values())


def _types(item):
    value = item.get("@type")
    values = value if isinstance(value, list) else [value]
    return {v.lower() for v in values if isinstance(v, str)}


def _text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _address_text(address):
    if isinstance(address, str):
        return address
    if not isinstance(address, dict):
        return ""
    parts = [address.get(k) for k in ("streetAddress", "addressLocality", "addressRegion",
                                      "postalCode", "addressCountry")]
    return ", ".join(_text(p) for p in parts if _text(p))


def _offering_items(item):
    """Yield (name, price_text) for offerings described in structured data."""
    candidates = []
    if _types(item) & OFFERING_TYPES:
        candidates.append(item)
    for key in ("makesOffer", "hasOfferCatalog", "itemListElement", "offers"):
        value = item.get(key)
        if isinstance(value, dict):
            value = value.get("itemListElement", [value])
        if isinstance(value, list):
            candidates.extend(v for v in value if isinstance(v, dict))
    for candidate in candidates:
        offered = candidate.get("itemOffered") if isinstance(candidate.get("itemOffered"), dict) else candidate
        name = _text(offered.get("name"))
        if not name:
            continue
        price = ""
        source = candidate if "price" in candidate else candidate.get("offers")
        if isinstance(source, list):
            source = source[0] if source else None
        if isinstance(source, dict) and _text(source.get("price")):
            currency = _text(source.get("priceCurrency"))
            price = f"{currency} {source['price']}".strip()
        yield name, price


def _from_structured_data(page, collect):
    for item in page.structured_data:
        if not isinstance(item, dict):
            continue
        types = _types(item)
        type_label = "/".join(sorted(t for t in types))
        detail = f"Structured data ({type_label})"
        if types & BUSINESS_TYPES:
            collect.add(FactKey.BUSINESS_NAME, _text(item.get("name")), page.url, detail)
            collect.add(FactKey.DESCRIPTION, _text(item.get("description")), page.url, detail)
            collect.add(FactKey.PHONE, _text(item.get("telephone")), page.url, detail)
            collect.add(FactKey.EMAIL, _text(item.get("email")).removeprefix("mailto:"), page.url, detail)
            collect.add(FactKey.ADDRESS, _address_text(item.get("address")), page.url, detail)
            hours = item.get("openingHours")
            for value in hours if isinstance(hours, list) else [hours]:
                collect.add(FactKey.OPENING_HOURS, _text(value), page.url, detail)
            logo = item.get("logo")
            if isinstance(logo, dict):
                logo = logo.get("url")
            collect.add(FactKey.LOGO, _text(logo), page.url, detail)
            same_as = item.get("sameAs")
            for link in same_as if isinstance(same_as, list) else [same_as]:
                label = _social_label(_text(link))
                if label:
                    collect.add(FactKey.SOCIAL, f"{label}: {link}", page.url, detail)
        for name, price in _offering_items(item):
            collect.add(FactKey.OFFERING, name, page.url, detail)
            if price:
                collect.add(FactKey.PRICE, f"{name}: {price}", page.url, detail)


def _social_label(url):
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    host = (parts.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    label = SOCIAL_HOSTS.get(host)
    path = parts.path.rstrip("/")
    if not label or not path or path.lower().startswith(SOCIAL_NON_PROFILE_PATHS):
        return ""
    return label


def _is_offering_page(page):
    haystack = (urlsplit(page.url).path + " " + page.title).lower()
    return any(word in haystack for word in OFFERING_PAGE_WORDS)


def _from_page(page, is_home, collect):
    if is_home:
        collect.add(FactKey.DESCRIPTION, page.meta_description, page.url, "Page description (meta tag)")
        site_name = page.open_graph.get("site_name") or page.open_graph.get("title")
        collect.add(FactKey.BUSINESS_NAME, site_name, page.url, "Social sharing title (Open Graph)")
        if page.title:
            first_part = TITLE_SEPARATORS.split(page.title)[0]
            collect.add(FactKey.BUSINESS_NAME, first_part, page.url, "Home page title")
        if page.open_graph.get("image"):
            collect.add(FactKey.LOGO, page.open_graph["image"], page.url,
                        "Social sharing image (may be a photo rather than a logo)")
        if HEX_COLOR.match(page.theme_color or ""):
            collect.add(FactKey.BRAND_COLOR, page.theme_color.lower(), page.url, "Theme colour (meta tag)")

    for email in EMAIL_PATTERN.findall(page.text):
        collect.add(FactKey.EMAIL, email, page.url, "Page text")
    for pattern in PHONE_PATTERNS:
        for phone in pattern.findall(page.text):
            collect.add(FactKey.PHONE, phone.strip(), page.url, "Page text")

    for link in page.links:
        label = _social_label(link.get("url", ""))
        if label:
            collect.add(FactKey.SOCIAL, f"{label}: {link['url']}", page.url, "Link on the page")

    if not is_home and _is_offering_page(page):
        headings = {h["text"] for h in page.headings}
        for line in page.text.split("\n"):
            line = line.strip()
            # Short lines that are not sentences are usually list items.
            if (3 <= len(line) <= 80 and not line.endswith((".", "?", "!", ":"))
                    and line not in headings and len(line.split()) <= 10):
                collect.add(FactKey.OFFERING, line, page.url, "Line on a services or products page")


def collect_suggestions(analysis):
    """Return Suggestion objects for every analyzed page of the analysis."""
    collect = SuggestionCollector()
    pages = list(analysis.pages.filter(status=AnalyzedPage.Status.SUCCESS).order_by("position"))
    for index, page in enumerate(pages):
        _from_structured_data(page, collect)
        _from_page(page, is_home=(index == 0), collect=collect)
    return collect.results()


@transaction.atomic
def refresh_suggestions(project, analysis):
    """Replace website suggestions with those from `analysis`.

    Facts the user confirmed, rejected or entered are never removed or
    changed. A suggestion matching one of them is not added again, so a
    rejected value does not come back, but its new evidence is recorded on
    a confirmed fact.
    """
    profile, _ = BusinessProfile.objects.get_or_create(project=project)
    profile.facts.filter(
        source=ProfileFact.Source.WEBSITE, status=ProfileFact.Status.SUGGESTED
    ).delete()

    kept = {}
    for fact in profile.facts.all():
        kept[(fact.key, fact.normalized_value)] = fact
        if fact.original_value:
            kept.setdefault((fact.key, normalize_value(fact.original_value)), fact)
    created = 0
    for suggestion in collect_suggestions(analysis):
        existing = kept.get((suggestion.key, normalize_value(suggestion.value)))
        if existing is not None:
            if existing.status == ProfileFact.Status.CONFIRMED:
                for item in suggestion.evidence:
                    if item not in existing.evidence:
                        existing.evidence.append(item)
                existing.save(update_fields=["evidence", "updated_at"])
            continue
        ProfileFact.objects.create(
            profile=profile,
            key=suggestion.key,
            value=suggestion.value,
            source=ProfileFact.Source.WEBSITE,
            status=ProfileFact.Status.SUGGESTED,
            evidence=suggestion.evidence,
        )
        created += 1

    profile.source_analysis = analysis
    profile.save(update_fields=["source_analysis", "updated_at"])
    return profile, created


def refresh_suggestions_after_analysis(sender, analysis, **kwargs):
    refresh_suggestions(analysis.project, analysis)
