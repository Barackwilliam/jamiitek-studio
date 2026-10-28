"""Tests for safe_fetch against a local test server.

The local server listens on 127.0.0.1, which the real policy blocks. These
tests therefore use a policy that allows only 127.0.0.1 and a resolver that
maps test hostnames to fixed addresses, so the redirect and pinning logic
can be exercised without any real network access.
"""

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from django.test import SimpleTestCase

from apps.website_analyzer import fetch
from apps.website_analyzer.fetch import FetchError, safe_fetch
from apps.website_analyzer.url_safety import UnsafeURLError

PAGE = b"<!doctype html><title>Duka la Mama</title><p>Karibu</p>"


class Handler(BaseHTTPRequestHandler):
    routes = {}

    def do_GET(self):
        self.server.requests.append((self.path, self.headers.get("Host")))
        action = self.routes.get(self.path.split("?")[0])
        if action is None:
            self._send(404, b"not found", "text/plain")
            return
        action(self)

    def _send(self, status, body, content_type="text/html; charset=utf-8", headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def redirect_to(location, status=302):
    return lambda h: h._send(status, b"", headers={"Location": location})


def slow_page(h):
    time.sleep(1.5)
    h._send(200, PAGE)


def streaming_huge_page(h):
    h.send_response(200)
    h.send_header("Content-Type", "text/html")
    h.end_headers()
    try:
        for _ in range(100):
            h.wfile.write(b"x" * 65536)
    except (BrokenPipeError, ConnectionResetError):
        pass


Handler.routes = {
    "/": lambda h: h._send(200, PAGE),
    "/moved": redirect_to("/"),
    "/to-metadata": redirect_to("http://169.254.169.254/latest/meta-data/"),
    "/to-file": redirect_to("file:///etc/passwd"),
    "/loop-a": redirect_to("/loop-b"),
    "/loop-b": redirect_to("/loop-a"),
    "/no-location": lambda h: h._send(302, b""),
    "/image": lambda h: h._send(200, b"\x89PNG", "image/png"),
    "/gzip": lambda h: h._send(200, b"\x1f\x8b", headers={"Content-Encoding": "gzip"}),
    "/big-declared": lambda h: h._send(200, b"x" * 5000),
    "/big-streamed": streaming_huge_page,
    "/slow": slow_page,
    "/missing-page": lambda h: h._send(404, b"<p>gone</p>"),
}


class SafeFetchTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.requests = []
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        super().tearDownClass()

    def setUp(self):
        self.server.requests.clear()
        self.addresses = {
            "site.test": ["127.0.0.1"],
            "shop.test": ["127.0.0.1"],
            "evil.test": ["10.0.0.5"],
        }
        self.resolver_calls = []

    def resolver(self, hostname, port):
        self.resolver_calls.append(hostname)
        return self.addresses[hostname]

    def fetch(self, path, **kwargs):
        options = {
            "resolver": self.resolver,
            "is_allowed_ip": lambda ip: ip == "127.0.0.1",
            "allowed_ports": {self.port},
            "timeout": 1.0,
            "total_timeout": 5.0,
        }
        options.update(kwargs)
        return safe_fetch(f"http://site.test:{self.port}{path}", **options)

    def test_fetches_html_page_with_real_host_header(self):
        result = self.fetch("/")

        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, PAGE)
        self.assertEqual(result.content_type, "text/html")
        self.assertEqual(result.charset, "utf-8")
        self.assertEqual(self.server.requests[-1], ("/", f"site.test:{self.port}"))

    def test_follows_relative_redirect(self):
        result = self.fetch("/moved")

        self.assertEqual(result.url, f"http://site.test:{self.port}/")
        self.assertEqual(result.redirects, (f"http://site.test:{self.port}/moved",))

    def test_follows_redirect_to_other_public_host_and_revalidates_it(self):
        Handler.routes["/to-other-host"] = redirect_to(f"http://shop.test:{self.port}/")

        result = self.fetch("/to-other-host")

        self.assertEqual(result.url, f"http://shop.test:{self.port}/")
        self.assertEqual(self.resolver_calls, ["site.test", "shop.test"])

    def test_redirect_to_host_resolving_to_private_address_is_blocked(self):
        Handler.routes["/to-private-host"] = redirect_to(f"http://evil.test:{self.port}/")

        with self.assertRaises(UnsafeURLError) as ctx:
            self.fetch("/to-private-host")

        self.assertEqual(ctx.exception.code, "private_address")

    def test_redirect_to_cloud_metadata_is_blocked_before_connecting(self):
        with mock.patch("socket.create_connection", wraps=fetch.socket.create_connection) as connect:
            with self.assertRaises(UnsafeURLError):
                self.fetch("/to-metadata")

        connected_to = [call.args[0][0] for call in connect.call_args_list]
        self.assertNotIn("169.254.169.254", connected_to)

    def test_redirect_to_file_scheme_is_blocked(self):
        with self.assertRaises(UnsafeURLError) as ctx:
            self.fetch("/to-file")
        self.assertEqual(ctx.exception.code, "scheme")

    def test_redirect_loop_is_detected(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/loop-a")
        self.assertEqual(ctx.exception.code, "redirect_loop")

    def test_too_many_redirects(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/moved", max_redirects=0)
        self.assertEqual(ctx.exception.code, "too_many_redirects")

    def test_redirect_without_location(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/no-location")
        self.assertEqual(ctx.exception.code, "bad_redirect")

    def test_dns_rebinding_cannot_change_destination_after_validation(self):
        answers = iter([["127.0.0.1"], ["10.0.0.5"]])
        calls = []

        def rebinding_resolver(hostname, port):
            calls.append(hostname)
            return next(answers)

        result = self.fetch("/", resolver=rebinding_resolver)

        self.assertEqual(result.status, 200)
        self.assertEqual(calls, ["site.test"], "hostname must be resolved once per hop")

    def test_non_html_content_is_refused(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/image")
        self.assertEqual(ctx.exception.code, "unsupported_type")

    def test_compressed_response_is_refused(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/gzip")
        self.assertEqual(ctx.exception.code, "unsupported_encoding")

    def test_declared_oversized_response_is_refused(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/big-declared", max_bytes=1000)
        self.assertEqual(ctx.exception.code, "too_large")

    def test_streamed_oversized_response_is_cut_off(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/big-streamed", max_bytes=100_000)
        self.assertEqual(ctx.exception.code, "too_large")

    def test_slow_response_times_out(self):
        with self.assertRaises(FetchError) as ctx:
            self.fetch("/slow", timeout=0.3)
        self.assertEqual(ctx.exception.code, "timeout")

    def test_error_status_is_returned_not_raised(self):
        result = self.fetch("/missing-page")
        self.assertEqual(result.status, 404)

    def test_connection_refused_gives_friendly_error(self):
        with self.assertRaises(FetchError) as ctx:
            safe_fetch(
                "http://site.test:1/",
                resolver=self.resolver,
                is_allowed_ip=lambda ip: ip == "127.0.0.1",
                allowed_ports={1},
                timeout=1.0,
            )
        self.assertEqual(ctx.exception.code, "connection_failed")

    def test_default_policy_refuses_local_server(self):
        with self.assertRaises(UnsafeURLError):
            safe_fetch(f"http://127.0.0.1:{self.port}/", allowed_ports={self.port})
        self.assertEqual(self.server.requests, [])


class PinnedHTTPSConnectionTests(SimpleTestCase):
    def test_connects_to_pinned_address_and_verifies_hostname(self):
        context = mock.Mock()
        raw_socket = object()
        with mock.patch.object(fetch.socket, "create_connection", return_value=raw_socket) as connect:
            conn = fetch.PinnedHTTPSConnection("shop.example", 443, "93.184.215.14", 5, context)
            conn.connect()

        connect.assert_called_once_with(("93.184.215.14", 443), 5)
        context.wrap_socket.assert_called_once_with(raw_socket, server_hostname="shop.example")
