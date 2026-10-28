import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from django.test import SimpleTestCase

from apps.website_analyzer.crawler import crawl, link_score
from apps.website_analyzer.fetch import FetchError, FetchResult, safe_fetch
from apps.website_analyzer.url_safety import UnsafeURLError

FIXTURES = Path(__file__).parent / "fixtures" / "site"


def page(url, body=b"<title>T</title>", status=200):
    return FetchResult(url=url, status=status, content_type="text/html", charset="utf-8", body=body)


class FakeFetch:
    """Maps URLs to FetchResults or exceptions; records every request."""

    def __init__(self, routes, robots=None):
        self.routes = routes
        self.robots = robots
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append(url)
        if url.endswith("/robots.txt"):
            if isinstance(self.robots, Exception):
                raise self.robots
            if self.robots is None:
                return page(url, b"not found", status=404)
            status, text = self.robots
            return FetchResult(url, status, "text/plain", "utf-8", text.encode())
        outcome = self.routes.get(url)
        if outcome is None:
            return page(url, b"missing", status=404)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def html_with_links(*hrefs):
    return ("<title>Home</title>" + "".join(f'<a href="{h}">{h}</a>' for h in hrefs)).encode()


class CrawlerTests(SimpleTestCase):
    START = "https://shop.example/"

    def run_crawl(self, fetch, **kwargs):
        options = {"min_delay": 0, "sleep": lambda seconds: None}
        options.update(kwargs)
        return crawl(self.START, fetch=fetch, **options)

    def test_follows_internal_links_and_ignores_external_and_files(self):
        fetch = FakeFetch({
            self.START: page(self.START, html_with_links(
                "/about", "https://other.example/x", "/brochure.pdf", "/logo.png")),
            self.START + "about": page(self.START + "about"),
        })

        result = self.run_crawl(fetch)

        self.assertEqual([p.url for p in result.pages], [self.START, self.START + "about"])
        self.assertNotIn("https://other.example/x", fetch.calls)
        self.assertNotIn(self.START + "brochure.pdf", fetch.calls)

    def test_relevant_pages_are_crawled_first(self):
        fetch = FakeFetch({
            self.START: page(self.START, html_with_links("/blog/news", "/gallery", "/huduma")),
        })

        self.run_crawl(fetch)

        page_calls = [url for url in fetch.calls if not url.endswith("robots.txt")]
        self.assertEqual(page_calls[1], self.START + "huduma")

    def test_low_value_pages_are_skipped(self):
        fetch = FakeFetch({self.START: page(self.START, html_with_links("/login", "/cart", "/privacy-policy"))})

        result = self.run_crawl(fetch)

        self.assertEqual(len(result.pages), 1)

    def test_page_limit_is_enforced(self):
        links = [f"/p{i}" for i in range(20)]
        fetch = FakeFetch({self.START: page(self.START, html_with_links(*links))}
                          | {self.START + f"p{i}": page(self.START + f"p{i}") for i in range(20)})

        result = self.run_crawl(fetch, max_pages=5)

        self.assertEqual(len(result.pages), 5)
        self.assertEqual(result.stopped_reason, "page_limit")

    def test_duplicate_links_are_fetched_once(self):
        fetch = FakeFetch({
            self.START: page(self.START, html_with_links("/about", "/about#team", "about")),
            self.START + "about": page(self.START + "about", html_with_links("/", "/about")),
        })

        self.run_crawl(fetch)

        self.assertEqual(fetch.calls.count(self.START + "about"), 1)
        self.assertEqual(fetch.calls.count(self.START), 1)

    def test_robots_disallowed_pages_are_reported_as_skipped(self):
        fetch = FakeFetch(
            {self.START: page(self.START, html_with_links("/private/a", "/about")),
             self.START + "about": page(self.START + "about")},
            robots=(200, "User-agent: *\nDisallow: /private/\n"),
        )

        result = self.run_crawl(fetch)

        skipped = [p for p in result.pages if p.status == "skipped"]
        self.assertEqual([p.url for p in skipped], [self.START + "private/a"])
        self.assertNotIn(self.START + "private/a", fetch.calls)

    def test_robots_specific_to_our_bot_is_respected(self):
        fetch = FakeFetch({self.START: page(self.START)},
                          robots=(200, "User-agent: JamiiTekStudioBot\nDisallow: /\n"))

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[0].status, "skipped")
        self.assertEqual(fetch.calls, [self.START + "robots.txt"])

    def test_robots_server_error_means_no_crawling_and_says_why(self):
        fetch = FakeFetch({self.START: page(self.START)}, robots=(503, "down"))

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[0].status, "failed")
        self.assertEqual(result.pages[0].error_code, "server_error")
        self.assertNotIn(self.START, fetch.calls)

    def test_unreachable_site_is_reported_as_unreachable_not_as_robots_refusal(self):
        fetch = FakeFetch({self.START: page(self.START)},
                          robots=UnsafeURLError("dns_failed", "We could not find this website address."))

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[0].status, "failed")
        self.assertEqual(result.pages[0].error_code, "dns_failed")
        self.assertNotIn("robots", result.pages[0].error_message)
        self.assertNotIn(self.START, fetch.calls)

    def test_missing_robots_allows_crawling(self):
        fetch = FakeFetch({self.START: page(self.START)}, robots=None)

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[0].status, "success")

    def test_failed_pages_are_recorded_and_crawl_continues(self):
        fetch = FakeFetch({
            self.START: page(self.START, html_with_links("/about", "/huduma")),
            self.START + "huduma": FetchError("timeout", "The website took too long to respond."),
            self.START + "about": page(self.START + "about"),
        })

        result = self.run_crawl(fetch)

        statuses = {p.url: p.status for p in result.pages}
        self.assertEqual(statuses[self.START + "huduma"], "failed")
        self.assertEqual(statuses[self.START + "about"], "success")

    def test_unsafe_link_is_recorded_as_failed_not_fetched(self):
        fetch = FakeFetch({
            self.START: page(self.START, html_with_links("/about")),
            self.START + "about": UnsafeURLError("private_address", "private"),
        })

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[1].error_code, "private_address")

    def test_error_status_page_is_failed(self):
        fetch = FakeFetch({self.START: page(self.START, b"gone", status=410)})

        result = self.run_crawl(fetch)

        self.assertEqual(result.pages[0].status, "failed")
        self.assertEqual(result.pages[0].http_status, 410)

    def test_start_redirect_to_www_allows_that_host(self):
        www = "https://www.shop.example/"
        fetch = FakeFetch({
            self.START: page(www, html_with_links("/about")),
            www + "about": page(www + "about"),
        })

        result = self.run_crawl(fetch)

        self.assertEqual([p.url for p in result.pages], [www, www + "about"])

    def test_delay_between_requests_respects_crawl_delay(self):
        waits = []
        now = [0.0]
        fetch = FakeFetch(
            {self.START: page(self.START, html_with_links("/about")),
             self.START + "about": page(self.START + "about")},
            robots=(200, "User-agent: *\nCrawl-delay: 3\n"),
        )

        crawl(self.START, fetch=fetch, min_delay=1.0,
              sleep=lambda s: (waits.append(s), now.__setitem__(0, now[0] + s)),
              clock=lambda: now[0])

        self.assertEqual(waits, [3.0])

    def test_time_budget_stops_crawl(self):
        now = [0.0]

        def slow_fetch(url, **kwargs):
            now[0] += 50
            return FakeFetch({})(url) if url.endswith("robots.txt") else page(
                url, html_with_links("/a", "/b", "/c"))

        result = crawl(self.START, fetch=slow_fetch, min_delay=0, time_budget=120,
                       sleep=lambda s: None, clock=lambda: now[0])

        self.assertEqual(result.stopped_reason, "time_limit")
        self.assertLess(len(result.pages), 4)

    def test_on_page_callback_receives_each_page(self):
        seen = []
        fetch = FakeFetch({self.START: page(self.START)})

        self.run_crawl(fetch, on_page=seen.append)

        self.assertEqual([p.url for p in seen], [self.START])


class LinkScoreTests(SimpleTestCase):
    def test_scores(self):
        self.assertEqual(link_score("https://x.example/huduma", ""), 3)
        self.assertEqual(link_score("https://x.example/page", "Wasiliana nasi"), 2)
        self.assertEqual(link_score("https://x.example/random", ""), 0)
        self.assertEqual(link_score("https://x.example/wp-admin/", ""), -1)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CrawlFixtureSiteTests(SimpleTestCase):
    """End to end against a local server, using the real safe_fetch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        handler = functools.partial(QuietHandler, directory=str(FIXTURES))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        super().tearDownClass()

    def test_crawls_fixture_site(self):
        fetch = functools.partial(
            safe_fetch,
            resolver=lambda host, port: ["127.0.0.1"],
            is_allowed_ip=lambda ip: ip == "127.0.0.1",
            allowed_ports={self.port},
            timeout=2.0,
        )
        start = f"http://mamaneema.test:{self.port}/index.html"

        result = crawl(start, fetch=fetch, min_delay=0, max_pages=8)

        by_url = {p.url.rsplit("/", 1)[-1]: p for p in result.pages}
        self.assertEqual(by_url["index.html"].status, "success")
        self.assertEqual(by_url["index.html"].info.language, "sw")
        self.assertEqual(by_url["kuhusu.html"].status, "success")
        self.assertEqual(by_url["huduma.html"].info.meta_description,
                         "Chakula cha sherehe, ofisi na mikutano.")
        self.assertEqual(by_url["report.html"].status, "skipped")      # robots.txt
        self.assertEqual(by_url["contact.html"].status, "failed")      # 404
        self.assertEqual(by_url["contact.html"].http_status, 404)
        self.assertNotIn("login.html", by_url)                         # low value
        self.assertNotIn("menu.pdf", by_url)                           # not a page
        self.assertNotIn("sponsored.html", by_url)                     # nofollow
