"""Extraction of page information from fetched HTML.

Everything returned here is observed page content, never inference. Website
text is untrusted data: it is stored and displayed as plain text and is
never interpreted as instructions.
"""

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

MAX_TEXT_CHARS = 20_000
MAX_HEADINGS = 40
MAX_IMAGES = 50
MAX_LINKS = 300
MAX_STRUCTURED_ITEMS = 10
MAX_JSON_LD_CHARS = 100_000

# Elements whose text is not page content.
NON_CONTENT_TAGS = [
    "script", "style", "noscript", "template", "svg", "canvas", "iframe",
    "form", "button", "select", "input", "textarea",
]
BOILERPLATE_TAGS = ["nav", "header", "footer", "aside"]

NON_PAGE_EXTENSIONS = re.compile(
    r"\.(pdf|jpe?g|png|gif|webp|svg|ico|bmp|tiff?|mp4|mov|avi|webm|mp3|wav|ogg|"
    r"zip|rar|7z|gz|tar|exe|msi|dmg|apk|docx?|xlsx?|pptx?|csv|json|xml|rss|txt|css|js)$",
    re.IGNORECASE,
)
WHITESPACE = re.compile(r"[ \t\r\f\v]+")
BLANK_LINES = re.compile(r"\n\s*\n+")


@dataclass
class PageInfo:
    title: str = ""
    meta_description: str = ""
    canonical_url: str = ""
    language: str = ""
    theme_color: str = ""
    open_graph: dict = field(default_factory=dict)
    headings: list = field(default_factory=list)
    text: str = ""
    text_truncated: bool = False
    images: list = field(default_factory=list)
    links: list = field(default_factory=list)
    structured_data: list = field(default_factory=list)


def _clean(text, limit=None):
    text = WHITESPACE.sub(" ", text or "").strip()
    return text[:limit] if limit else text


def normalize_link(base_url, href):
    """Return an absolute http(s) URL without fragment, or "" if unusable."""
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")):
        return ""
    try:
        absolute = urljoin(base_url, href)
        parts = urlsplit(absolute)
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return ""
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))


def is_probably_page(url):
    return not NON_PAGE_EXTENSIONS.search(urlsplit(url).path)


def _main_text(soup):
    for tag in soup(NON_CONTENT_TAGS):
        tag.decompose()
    container = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.find("article")
    if container is None:
        container = soup.body or soup
        for tag in container.find_all(BOILERPLATE_TAGS):
            tag.decompose()
    text = container.get_text("\n", strip=True)
    lines = [_clean(line) for line in text.split("\n")]
    return BLANK_LINES.sub("\n\n", "\n".join(line for line in lines if line))


def _json_ld_items(soup):
    items = []
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        if not raw.strip() or len(raw) > MAX_JSON_LD_CHARS:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict) and isinstance(candidate.get("@graph"), list):
                candidates.extend(item for item in candidate["@graph"] if isinstance(item, dict))
                continue
            if isinstance(candidate, dict) and candidate.get("@type"):
                items.append(candidate)
            if len(items) >= MAX_STRUCTURED_ITEMS:
                return items
    return items


def extract_page(html_bytes, page_url, charset=""):
    """Parse HTML and return a PageInfo. Never raises on malformed HTML."""
    soup = BeautifulSoup(html_bytes, "html.parser", from_encoding=charset or None)
    info = PageInfo()

    if soup.title and soup.title.string:
        info.title = _clean(soup.title.string, 300)

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        info.language = _clean(html_tag["lang"], 20).lower()

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").strip().lower()
        content = _clean(meta.get("content"), 1000)
        if not name or not content:
            continue
        if name == "description" and not info.meta_description:
            info.meta_description = content
        elif name == "theme-color" and not info.theme_color:
            info.theme_color = content[:30]
        elif name.startswith("og:") and name[3:] in {"title", "description", "image", "site_name", "type", "locale"}:
            info.open_graph.setdefault(name[3:], content)

    if info.open_graph.get("image"):
        info.open_graph["image"] = normalize_link(page_url, info.open_graph["image"])

    for link in soup.find_all("link", href=True):
        if "canonical" in [value.lower() for value in (link.get("rel") or [])]:
            info.canonical_url = normalize_link(page_url, link["href"])
            break

    info.structured_data = _json_ld_items(soup)

    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = _clean(heading.get_text(" ", strip=True), 300)
        if text:
            info.headings.append({"level": int(heading.name[1]), "text": text})
        if len(info.headings) >= MAX_HEADINGS:
            break

    seen_images = set()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        absolute = normalize_link(page_url, src)
        if absolute and absolute not in seen_images:
            seen_images.add(absolute)
            info.images.append({"url": absolute, "alt": _clean(img.get("alt"), 300)})
        if len(info.images) >= MAX_IMAGES:
            break

    seen_links = set()
    for anchor in soup.find_all("a", href=True):
        rel = [value.lower() for value in (anchor.get("rel") or [])]
        absolute = normalize_link(page_url, anchor["href"])
        if not absolute or absolute in seen_links or "nofollow" in rel:
            continue
        seen_links.add(absolute)
        info.links.append({"url": absolute, "text": _clean(anchor.get_text(" ", strip=True), 200)})
        if len(info.links) >= MAX_LINKS:
            break

    text = _main_text(soup)
    if len(text) > MAX_TEXT_CHARS:
        info.text = text[:MAX_TEXT_CHARS]
        info.text_truncated = True
    else:
        info.text = text
    return info
