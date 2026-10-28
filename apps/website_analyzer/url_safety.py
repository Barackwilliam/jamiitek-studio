"""Validation of user-submitted website URLs before any network access.

This module is the first SSRF defence (see docs/ARCHITECTURE.md, section 7).
A URL is accepted only if it uses HTTP or HTTPS on an allowed port and every
address its hostname resolves to is a public internet address. Callers that
connect to the site must use the addresses returned here instead of
resolving the hostname again, so that DNS rebinding cannot change the
destination after validation (see fetch.py).
"""

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

ALLOWED_SCHEMES = ("http", "https")
DEFAULT_PORTS = {"http": 80, "https": 443}
DEFAULT_ALLOWED_PORTS = frozenset({80, 443})
MAX_URL_LENGTH = 2048

BLOCKED_HOSTNAMES = frozenset({"localhost", "metadata", "metadata.google.internal"})
BLOCKED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".intranet",
    ".lan",
    ".home.arpa",
)

NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")

# Hostnames made only of digits, dots and hex markers are unusual IP formats
# such as "2130706433" or "0x7f.1" that resolvers may translate to private
# addresses. Valid dotted IPv4 literals are handled separately.
SCHEME_ONLY_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

NUMERIC_HOST_PATTERN = re.compile(r"^(0x[0-9a-f]+|[0-9]+)(\.(0x[0-9a-f]+|[0-9]+))*$")


class UnsafeURLError(ValueError):
    """Raised when a URL must not be fetched. `message` is safe to show users."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ValidatedURL:
    url: str
    scheme: str
    hostname: str
    port: int
    addresses: tuple


def is_public_ip(address):
    """Return True only for addresses that are safe to connect to."""
    ip = ipaddress.ip_address(address)
    if ip.version == 6:
        # Addresses that embed an IPv4 address are judged by that address.
        if ip.ipv4_mapped is not None:
            return is_public_ip(ip.ipv4_mapped)
        if ip.sixtofour is not None:
            return is_public_ip(ip.sixtofour)
        if ip.teredo is not None:
            return all(is_public_ip(embedded) for embedded in ip.teredo)
        if ip in NAT64_PREFIX:
            return is_public_ip(ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF))
    return ip.is_global and not ip.is_multicast and not ip.is_reserved


def resolve_host(hostname, port):
    """Return the IP addresses for hostname using the system resolver."""
    try:
        results = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise UnsafeURLError(
            "dns_failed",
            "We could not find this website address. Check the spelling, "
            "or enter your business details manually.",
        ) from exc
    addresses = []
    for _family, _type, _proto, _canonname, sockaddr in results:
        # Strip any IPv6 zone identifier such as "%eth0".
        address = sockaddr[0].split("%", 1)[0]
        if address not in addresses:
            addresses.append(address)
    return addresses


def normalize_url(raw_url, allowed_ports=DEFAULT_ALLOWED_PORTS):
    """Check URL syntax and return (url, scheme, ascii_hostname, port).

    No network access happens here.
    """
    url = (raw_url or "").strip()
    if not url:
        raise UnsafeURLError("empty", "Enter a website address.")
    if len(url) > MAX_URL_LENGTH:
        raise UnsafeURLError("too_long", "This website address is too long.")
    if any(char in url for char in "\\\r\n\t ") or any(ord(c) < 32 for c in url):
        raise UnsafeURLError("invalid", "This website address contains invalid characters.")

    if "://" not in url:
        # "mailto:x" or "javascript:..." name a scheme; "example.com:8080"
        # is a bare domain with a port.
        scheme_match = SCHEME_ONLY_PATTERN.match(url)
        if scheme_match and not url[scheme_match.end():][:1].isdigit():
            raise UnsafeURLError(
                "scheme", "Only website addresses starting with http:// or https:// are supported."
            )
        url = "https://" + url

    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise UnsafeURLError("invalid", "This is not a valid website address.") from exc

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(
            "scheme", "Only website addresses starting with http:// or https:// are supported."
        )
    if parts.username is not None or parts.password is not None:
        raise UnsafeURLError(
            "credentials", "Website addresses containing a username or password are not supported."
        )

    hostname = (parts.hostname or "").rstrip(".")
    if not hostname:
        raise UnsafeURLError("invalid", "This website address has no domain name.")

    is_ip_literal = True
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        is_ip_literal = False

    if not is_ip_literal:
        try:
            hostname = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise UnsafeURLError("invalid", "This website address is not valid.") from exc
        if NUMERIC_HOST_PATTERN.match(hostname):
            raise UnsafeURLError(
                "numeric_host", "Enter the website's domain name instead of a numeric address."
            )
        if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_HOST_SUFFIXES):
            raise UnsafeURLError("blocked_host", "This address points to a private network.")
        if "." not in hostname:
            raise UnsafeURLError(
                "invalid", "Enter a full website address, for example example.com."
            )

    if port is None:
        port = DEFAULT_PORTS[scheme]
    if port not in allowed_ports:
        raise UnsafeURLError("port", "Website addresses with this port number are not supported.")

    host_for_url = f"[{hostname}]" if ":" in hostname else hostname
    netloc = host_for_url if port == DEFAULT_PORTS[scheme] else f"{host_for_url}:{port}"
    normalized = urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))
    return normalized, scheme, hostname, port


def validate_public_url(
    raw_url,
    *,
    resolver=None,
    is_allowed_ip=is_public_ip,
    allowed_ports=DEFAULT_ALLOWED_PORTS,
):
    """Return a ValidatedURL, or raise UnsafeURLError if it must not be fetched.

    Every resolved address must be allowed. A hostname that resolves to both
    public and private addresses is rejected, because a later connection
    could reach either one.
    """
    url, scheme, hostname, port = normalize_url(raw_url, allowed_ports)
    try:
        # An IP literal is its own address; checking it must never depend
        # on what a resolver says about it.
        addresses = (str(ipaddress.ip_address(hostname)),)
    except ValueError:
        resolve = resolver or resolve_host
        addresses = tuple(resolve(hostname, port))
    if not addresses:
        raise UnsafeURLError("dns_failed", "We could not find this website address.")
    for address in addresses:
        try:
            allowed = is_allowed_ip(address)
        except ValueError:
            allowed = False
        if not allowed:
            raise UnsafeURLError(
                "private_address",
                "This address points to a private or reserved network and cannot be analyzed.",
            )
    return ValidatedURL(url=url, scheme=scheme, hostname=hostname, port=port, addresses=addresses)
