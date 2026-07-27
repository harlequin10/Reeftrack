"""
Custom security middleware for ReefTrack.
Adds Content-Security-Policy headers and account lockout logic.
"""
import time
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


class ContentSecurityPolicyMiddleware:
    """Adds Content-Security-Policy header to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only set CSP on HTML responses (not static files, APIs, etc.)
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://unpkg.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com https://*.basemaps.cartocdn.com; "
                "connect-src 'self' ws: wss: https://*.tile.openstreetmap.org; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        return response


# ==================== ACCOUNT LOCKOUT ====================

LOCKOUT_FAILURE_LIMIT = 5       # failures before lockout
LOCKOUT_TIMEOUT = 900           # 15 minutes in seconds


def record_failed_login(identifier):
    """Record a failed login attempt. Locks account after LOCKOUT_FAILURE_LIMIT failures."""
    key = f'login_failures:{identifier}'
    failures = cache.get(key, 0) + 1
    cache.set(key, failures, LOCKOUT_TIMEOUT)
    return failures


def is_locked_out(identifier):
    """Check if an account/IP is currently locked out."""
    key = f'login_failures:{identifier}'
    failures = cache.get(key, 0)
    return failures >= LOCKOUT_FAILURE_LIMIT


def clear_login_failures(identifier):
    """Clear failure count on successful login."""
    key = f'login_failures:{identifier}'
    cache.delete(key)


def record_failed_login_for_view(request, identifier):
    """Record failure and return True if now locked out."""
    failures = record_failed_login(identifier)
    if failures >= LOCKOUT_FAILURE_LIMIT:
        return True
    return False
