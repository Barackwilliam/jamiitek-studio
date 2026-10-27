"""SSRF protection tests. No test here uses real DNS or the network."""

from unittest import mock

from django.test import SimpleTestCase

from apps.website_analyzer.url_safety import (
    UnsafeURLError,
    is_public_ip,
    normalize_url,
    resolve_host,
    validate_public_url,
)

PUBLIC_IP = "93.184.215.14"


def fixed_resolver(*addresses):
    def resolve(hostname, port):
        return list(addresses)

    return resolve


class IsPublicIPTests(SimpleTestCase):
    def test_public_addresses_are_allowed(self):
        for address in [PUBLIC_IP, "8.8.8.8", "2606:4700:4700::1111"]:
            with self.subTest(address=address):
                self.assertTrue(is_public_ip(address))

    def test_private_and_special_addresses_are_blocked(self):
        blocked = [
            "127.0.0.1",          # loopback
            "127.255.255.254",
            "0.0.0.0",            # unspecified
            "10.0.0.1",           # private
            "172.16.0.1",
            "192.168.1.1",
            "169.254.169.254",    # cloud metadata (link-local)
            "100.64.0.1",         # carrier-grade NAT
            "192.0.0.1",          # IETF protocol assignments
            "198.18.0.1",         # benchmarking
            "224.0.0.1",          # multicast
            "239.255.255.250",
            "240.0.0.1",          # reserved
            "255.255.255.255",    # broadcast
            "::1",                # IPv6 loopback
            "::",                 # IPv6 unspecified
            "fe80::1",            # IPv6 link-local
            "fc00::1",            # IPv6 unique local
            "ff02::1",            # IPv6 multicast
            "fd00:ec2::254",      # AWS IPv6 metadata
        ]
        for address in blocked:
            with self.subTest(address=address):
                self.assertFalse(is_public_ip(address))

    def test_ipv6_forms_embedding_private_ipv4_are_blocked(self):
        for address in [
            "::ffff:127.0.0.1",        # IPv4-mapped
            "::ffff:169.254.169.254",
            "2002:7f00:1::",           # 6to4 wrapping 127.0.0.1
            "64:ff9b::7f00:1",         # NAT64 wrapping 127.0.0.1
            "64:ff9b::a9fe:a9fe",      # NAT64 wrapping 169.254.169.254
        ]:
            with self.subTest(address=address):
                self.assertFalse(is_public_ip(address))

    def test_ipv6_forms_embedding_public_ipv4_are_allowed(self):
        self.assertTrue(is_public_ip("::ffff:8.8.8.8"))
        self.assertTrue(is_public_ip("64:ff9b::808:808"))


class NormalizeURLTests(SimpleTestCase):
    def test_bare_domain_gets_https(self):
        url, scheme, host, port = normalize_url("example.com")
        self.assertEqual((url, scheme, host, port), ("https://example.com/", "https", "example.com", 443))

    def test_bare_domain_with_allowed_port(self):
        url, *_ = normalize_url("example.com:443/shop")
        self.assertEqual(url, "https://example.com/shop")

    def test_normalizes_case_trailing_dot_and_fragment(self):
        url, *_ = normalize_url("HTTPS://Example.COM./About?x=1#team")
        self.assertEqual(url, "https://example.com/About?x=1")

    def test_international_domain_is_converted_to_ascii(self):
        url, _, host, _ = normalize_url("https://bücher.example/")
        self.assertEqual(host, "xn--bcher-kva.example")
        self.assertEqual(url, "https://xn--bcher-kva.example/")

    def test_rejected_inputs(self):
        cases = {
            "": "empty",
            "   ": "empty",
            "ftp://example.com/": "scheme",
            "file:///etc/passwd": "scheme",
            "javascript:alert(1)": "scheme",
            "mailto:owner@example.com": "scheme",
            "data:text/html,hello": "scheme",
            "gopher://example.com/": "scheme",
            "https://user:pass@example.com/": "credentials",
            "https://user@example.com/": "credentials",
            "https://example.com:22/": "port",
            "https://example.com:99999/": "invalid",
            "https://localhost/": "blocked_host",
            "https://LOCALHOST./": "blocked_host",
            "https://printer.local/": "blocked_host",
            "https://metadata.google.internal/": "blocked_host",
            "https://2130706433/": "numeric_host",      # decimal 127.0.0.1
            "https://0x7f000001/": "numeric_host",      # hexadecimal
            "https://0177.0.0.1/": "numeric_host",      # octal
            "https://127.1/": "numeric_host",           # shortened
            "https://intranet/": "invalid",
            "https://exa mple.com/": "invalid",
            "https://example.com\\@evil.com/": "invalid",
            "https://example.com/\r\nHost: evil": "invalid",
            "https://" + "a" * 2050 + ".com/": "too_long",
        }
        for raw, code in cases.items():
            with self.subTest(raw=raw):
                with self.assertRaises(UnsafeURLError) as ctx:
                    normalize_url(raw)
                self.assertEqual(ctx.exception.code, code)


class ValidatePublicURLTests(SimpleTestCase):
    def test_public_site_is_accepted(self):
        result = validate_public_url("example.com", resolver=fixed_resolver(PUBLIC_IP))

        self.assertEqual(result.url, "https://example.com/")
        self.assertEqual(result.addresses, (PUBLIC_IP,))

    def test_hostname_resolving_to_private_address_is_blocked(self):
        for address in ["127.0.0.1", "10.1.2.3", "169.254.169.254", "::1"]:
            with self.subTest(address=address):
                with self.assertRaises(UnsafeURLError) as ctx:
                    validate_public_url("https://sneaky.example/", resolver=fixed_resolver(address))
                self.assertEqual(ctx.exception.code, "private_address")

    def test_mixed_public_and_private_resolution_is_blocked(self):
        with self.assertRaises(UnsafeURLError) as ctx:
            validate_public_url(
                "https://sneaky.example/", resolver=fixed_resolver(PUBLIC_IP, "10.0.0.1")
            )
        self.assertEqual(ctx.exception.code, "private_address")

    def test_literal_private_ip_is_blocked(self):
        for raw in ["http://127.0.0.1/", "http://169.254.169.254/latest/meta-data/",
                    "http://[::1]/", "http://[::ffff:127.0.0.1]/", "http://10.0.0.1/"]:
            with self.subTest(raw=raw):
                with self.assertRaises(UnsafeURLError):
                    validate_public_url(raw)

    def test_literal_ip_is_checked_without_consulting_resolver(self):
        resolver = mock.Mock(return_value=[PUBLIC_IP])

        with self.assertRaises(UnsafeURLError):
            validate_public_url("http://127.0.0.1/", resolver=resolver)
        resolver.assert_not_called()

        result = validate_public_url("http://8.8.8.8/", resolver=resolver)
        self.assertEqual(result.addresses, ("8.8.8.8",))
        resolver.assert_not_called()

    def test_unparseable_resolver_answer_is_blocked(self):
        with self.assertRaises(UnsafeURLError):
            validate_public_url("https://odd.example/", resolver=fixed_resolver("not-an-ip"))

    def test_no_addresses_is_an_error(self):
        with self.assertRaises(UnsafeURLError) as ctx:
            validate_public_url("https://empty.example/", resolver=fixed_resolver())
        self.assertEqual(ctx.exception.code, "dns_failed")


class ResolveHostTests(SimpleTestCase):
    def test_dns_failure_gives_friendly_error(self):
        import socket

        with mock.patch("socket.getaddrinfo", side_effect=socket.gaierror("no such host")):
            with self.assertRaises(UnsafeURLError) as ctx:
                resolve_host("missing.example", 443)
        self.assertEqual(ctx.exception.code, "dns_failed")
        self.assertIn("manually", ctx.exception.message)

    def test_strips_ipv6_zone_and_deduplicates(self):
        import socket

        answers = [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("fe80::1%eth0", 443, 0, 2)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_IP, 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_IP, 443)),
        ]
        with mock.patch("socket.getaddrinfo", return_value=answers):
            self.assertEqual(resolve_host("x.example", 443), ["fe80::1", PUBLIC_IP])
