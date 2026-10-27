"""Fetching a single web page safely.

Every hop of a redirect chain is validated with url_safety, and each
connection goes to an address that was validated for that hop, never to a
fresh DNS lookup. Responses are limited in size and time, and compressed
responses are refused so a small download cannot expand into a huge one.
"""

import http.client
import socket
import ssl
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

from .url_safety import (
    DEFAULT_ALLOWED_PORTS,
    UnsafeURLError,
    is_public_ip,
    validate_public_url,
)

USER_AGENT = "JamiiTekStudioBot/0.1 (+website analysis for the site owner)"
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
HTML_CONTENT_TYPES = frozenset({"text/html", "application/xhtml+xml"})
CHUNK_SIZE = 64 * 1024


class FetchError(Exception):
    """Raised when a page could not be fetched. `message` is safe to show users."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content_type: str
    charset: str
    body: bytes
    redirects: tuple = field(default_factory=tuple)


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection to a pre-validated IP address, sending the real Host."""

    def __init__(self, host, port, address, timeout):
        super().__init__(host, port, timeout=timeout)
        self.address = address

    def connect(self):
        self.sock = socket.create_connection((self.address, self.port), self.timeout)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection to a pre-validated IP address.

    The certificate is still verified against the hostname, because the
    hostname is used for SNI and certificate matching.
    """

    def __init__(self, host, port, address, timeout, context):
        super().__init__(host, port, timeout=timeout, context=context)
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _open_connection(target, timeout, ssl_context):
    last_error = None
    for address in target.addresses:
        if target.scheme == "https":
            conn = PinnedHTTPSConnection(
                target.hostname, target.port, address, timeout, ssl_context
            )
        else:
            conn = PinnedHTTPConnection(target.hostname, target.port, address, timeout)
        try:
            conn.connect()
            return conn
        except OSError as exc:
            conn.close()
            last_error = exc
    raise last_error


def _request_path(url):
    after_scheme = url.split("://", 1)[1]
    slash = after_scheme.find("/")
    return after_scheme[slash:] if slash != -1 else "/"


def _read_limited(response, max_bytes, deadline):
    chunks = []
    total = 0
    while True:
        if time.monotonic() > deadline:
            raise FetchError("timeout", "The website took too long to respond.")
        chunk = response.read(CHUNK_SIZE)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > max_bytes:
            raise FetchError("too_large", "The page is too large to analyze.")
        chunks.append(chunk)


def _parse_content_type(header):
    media_type, _, params = (header or "").partition(";")
    charset = ""
    for param in params.split(";"):
        name, _, value = param.strip().partition("=")
        if name.lower() == "charset":
            charset = value.strip().strip('"').lower()
    return media_type.strip().lower(), charset


def safe_fetch(
    url,
    *,
    resolver=None,
    is_allowed_ip=is_public_ip,
    allowed_ports=DEFAULT_ALLOWED_PORTS,
    allowed_content_types=HTML_CONTENT_TYPES,
    timeout=10.0,
    total_timeout=20.0,
    max_bytes=2_000_000,
    max_redirects=5,
    ssl_context=None,
):
    """Fetch one page, following safe redirects. Raises UnsafeURLError or FetchError.

    A non-2xx final status is returned, not raised, so callers can report it.
    """
    ssl_context = ssl_context or ssl.create_default_context()
    deadline = time.monotonic() + total_timeout
    redirects = []
    visited = set()
    current = url

    while True:
        target = validate_public_url(
            current,
            resolver=resolver,
            is_allowed_ip=is_allowed_ip,
            allowed_ports=allowed_ports,
        )
        if target.url in visited:
            raise FetchError("redirect_loop", "The website redirects in a loop.")
        visited.add(target.url)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FetchError("timeout", "The website took too long to respond.")

        conn = None
        try:
            conn = _open_connection(target, min(timeout, remaining), ssl_context)
            conn.request(
                "GET",
                _request_path(target.url),
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            response = conn.getresponse()

            if response.status in REDIRECT_STATUSES:
                location = response.getheader("Location")
                if not location:
                    raise FetchError("bad_redirect", "The website sent an invalid redirect.")
                if len(redirects) >= max_redirects:
                    raise FetchError("too_many_redirects", "The website redirects too many times.")
                redirects.append(target.url)
                current = urljoin(target.url, location.strip())
                continue

            encoding = (response.getheader("Content-Encoding") or "identity").strip().lower()
            if encoding != "identity":
                raise FetchError(
                    "unsupported_encoding", "The website sent a compressed response we cannot accept."
                )

            content_type, charset = _parse_content_type(response.getheader("Content-Type"))
            if 200 <= response.status < 300 and content_type not in allowed_content_types:
                raise FetchError("unsupported_type", "This address does not point to a web page.")

            declared_length = response.getheader("Content-Length")
            if declared_length and declared_length.isdigit() and int(declared_length) > max_bytes:
                raise FetchError("too_large", "The page is too large to analyze.")

            body = _read_limited(response, max_bytes, deadline)
            return FetchResult(
                url=target.url,
                status=response.status,
                content_type=content_type,
                charset=charset,
                body=body,
                redirects=tuple(redirects),
            )
        except (FetchError, UnsafeURLError):
            raise
        except (socket.timeout, TimeoutError) as exc:
            raise FetchError("timeout", "The website took too long to respond.") from exc
        except ssl.SSLError as exc:
            raise FetchError(
                "tls_error", "The website's security certificate could not be verified."
            ) from exc
        except (http.client.HTTPException, ValueError) as exc:
            raise FetchError("bad_response", "The website sent an invalid response.") from exc
        except OSError as exc:
            raise FetchError("connection_failed", "We could not connect to the website.") from exc
        finally:
            if conn is not None:
                conn.close()
