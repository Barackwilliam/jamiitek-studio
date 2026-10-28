from django.conf import settings

# Everything the pages use comes from this site: no inline scripts or styles,
# no third-party resources, and no framing. Images from analyzed websites are
# deliberately never loaded (DEC-019), so img-src can stay 'self'.
DEFAULT_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "media-src 'self'",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware:
    """Adds Content-Security-Policy and Permissions-Policy to every response."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = getattr(settings, "CONTENT_SECURITY_POLICY", DEFAULT_CSP)

    def __call__(self, request):
        response = self.get_response(request)
        if self.csp:
            response.headers.setdefault("Content-Security-Policy", self.csp)
        response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        return response
