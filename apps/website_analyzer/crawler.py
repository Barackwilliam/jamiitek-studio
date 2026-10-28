"""A small, polite crawler for one business website.

The crawler reads robots.txt, fetches the start page, then follows the most
relevant internal links (about, services, products, contact, ...) up to a
page limit. It reports every page it attempted, including failures and pages
skipped because robots.txt disallows them, so users can see exactly what was
and was not analyzed.
"""

import heapq
import time
from dataclasses import dataclass, field
from urllib import robotparser
from urllib.parse import urlsplit, urlunsplit

from .extract import extract_page, is_probably_page
from .fetch import FetchError, safe_fetch
from .url_safety import UnsafeURLError

ROBOTS_USER_AGENT = "JamiiTekStudioBot"
ROBOTS_CONTENT_TYPES = frozenset({"text/plain", "text/html", "application/octet-stream", ""})
MAX_ROBOTS_BYTES = 500_000
MAX_CRAWL_DELAY = 10.0

# Words in a link's path or text that suggest a page useful for marketing,
# in English and Kiswahili. Higher scores are crawled first.
RELEVANCE_KEYWORDS = {
    3: ["about", "kuhusu", "services", "service", "huduma", "products", "product",
        "bidhaa", "shop", "duka", "store", "menu", "pricing", "prices", "bei"],
    2: ["contact", "mawasiliano", "wasiliana", "rooms", "tours", "safari", "packages",
        "courses", "programs", "portfolio", "solutions", "features", "offers", "catalog"],
    1: ["team", "timu", "gallery", "picha", "faq", "location", "mahali", "booking", "events"],
}
LOW_VALUE_KEYWORDS = ["login", "signin", "register", "cart", "checkout", "account", "privacy",
                      "terms", "cookie", "wp-admin", "feed", "tag/", "author/", "search"]


@dataclass
class CrawledPage:
    url: str
    status: str  # "success", "failed" or "skipped"
    http_status: int = None
    info: object = None
    error_code: str = ""
    error_message: str = ""
    depth: int = 0


@dataclass
class CrawlResult:
    pages: list = field(default_factory=list)
    stopped_reason: str = ""

    @property
    def succeeded(self):
        return [page for page in self.pages if page.status == "success"]


def _origin(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def _same_site(host, allowed_hosts):
    host = (host or "").lower()
    bare = host[4:] if host.startswith("www.") else host
    return bare in allowed_hosts


def _site_key(host):
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def link_score(url, text):
    haystack = (urlsplit(url).path + " " + (text or "")).lower()
    if any(word in haystack or word in url.lower() for word in LOW_VALUE_KEYWORDS):
        return -1
    for score, words in RELEVANCE_KEYWORDS.items():
        if any(word in haystack for word in words):
            return score
    return 0


class RobotsCache:
    """Fetches and caches robots.txt per origin, following RFC 9309."""

    def __init__(self, fetch):
        self.fetch = fetch
        self.parsers = {}
        # origin -> (code, message) when robots.txt could not be read.
        self.problems = {}

    def get(self, url):
        origin = _origin(url)
        if origin not in self.parsers:
            self.parsers[origin] = self._load(origin)
        return self.parsers[origin]

    def problem(self, url):
        """Return (code, message) if the site's robots.txt could not be read, else None."""
        self.get(url)
        return self.problems.get(_origin(url))

    def _load(self, origin):
        parser = robotparser.RobotFileParser()
        try:
            result = self.fetch(
                origin + "/robots.txt",
                allowed_content_types=ROBOTS_CONTENT_TYPES,
                max_bytes=MAX_ROBOTS_BYTES,
            )
        except (FetchError, UnsafeURLError) as exc:
            # RFC 9309: if robots.txt is unreachable, assume crawling is not
            # allowed. Usually the whole site is unreachable, so report that.
            parser.disallow_all = True
            self.problems[origin] = (exc.code, exc.message)
            return parser
        if 400 <= result.status < 500:
            parser.allow_all = True
        elif result.status >= 500:
            parser.disallow_all = True
            self.problems[origin] = (
                "server_error",
                "The website is having technical problems right now, so we did not read it. "
                "Please try again later.",
            )
        else:
            text = result.body.decode(result.charset or "utf-8", errors="replace")
            parser.parse(text.splitlines())
        return parser

    def allowed(self, url):
        return self.get(url).can_fetch(ROBOTS_USER_AGENT, url)

    def crawl_delay(self, url):
        delay = self.get(url).crawl_delay(ROBOTS_USER_AGENT)
        return min(float(delay), MAX_CRAWL_DELAY) if delay else None


def crawl(
    start_url,
    *,
    fetch=safe_fetch,
    max_pages=8,
    max_depth=2,
    min_delay=1.0,
    time_budget=120.0,
    sleep=time.sleep,
    clock=time.monotonic,
    on_page=None,
):
    """Crawl one website starting at start_url and return a CrawlResult.

    `fetch` must behave like safe_fetch (every call is SSRF-checked).
    `on_page` is called with each CrawledPage as soon as it is known, so
    callers can save progress.
    """
    result = CrawlResult()
    robots = RobotsCache(fetch)
    deadline = clock() + time_budget
    allowed_hosts = {_site_key(urlsplit(start_url).hostname)}
    seen = set()
    queue = []  # (negative score, order, url, depth)
    order = 0
    last_request_at = None

    def record(page):
        result.pages.append(page)
        if on_page:
            on_page(page)

    def enqueue(url, text, depth):
        nonlocal order
        if url in seen or not is_probably_page(url):
            return
        if not _same_site(urlsplit(url).hostname, allowed_hosts):
            return
        score = link_score(url, text)
        if score < 0:
            return
        seen.add(url)
        order += 1
        heapq.heappush(queue, (-score, order, url, depth))

    seen.add(start_url)
    heapq.heappush(queue, (-100, 0, start_url, 0))

    while queue:
        fetched_count = sum(1 for page in result.pages if page.status != "skipped")
        if fetched_count >= max_pages:
            result.stopped_reason = "page_limit"
            break
        if clock() >= deadline:
            result.stopped_reason = "time_limit"
            break

        _, _, url, depth = heapq.heappop(queue)

        problem = robots.problem(url)
        if problem:
            code, message = problem
            record(CrawledPage(
                url=url, status="failed", depth=depth, error_code=code, error_message=message,
            ))
            continue

        if not robots.allowed(url):
            record(CrawledPage(
                url=url, status="skipped", depth=depth, error_code="robots",
                error_message="The website's robots.txt asks crawlers not to read this page.",
            ))
            continue

        delay = max(min_delay, robots.crawl_delay(url) or 0)
        if last_request_at is not None:
            wait = last_request_at + delay - clock()
            if wait > 0:
                if clock() + wait >= deadline:
                    result.stopped_reason = "time_limit"
                    break
                sleep(wait)
        last_request_at = clock()

        try:
            response = fetch(url)
        except (FetchError, UnsafeURLError) as exc:
            record(CrawledPage(
                url=url, status="failed", depth=depth,
                error_code=exc.code, error_message=exc.message,
            ))
            continue

        if not 200 <= response.status < 300:
            record(CrawledPage(
                url=response.url, status="failed", http_status=response.status, depth=depth,
                error_code="http_status",
                error_message=f"The website answered with status {response.status}.",
            ))
            continue

        if depth == 0:
            # A start page that redirects (for example to www. or another
            # domain) defines the site we are analyzing.
            allowed_hosts.add(_site_key(urlsplit(response.url).hostname))
        seen.add(response.url)

        info = extract_page(response.body, response.url, response.charset)
        record(CrawledPage(
            url=response.url, status="success", http_status=response.status,
            info=info, depth=depth,
        ))

        if depth < max_depth:
            for link in info.links:
                enqueue(link["url"], link["text"], depth + 1)

    return result
