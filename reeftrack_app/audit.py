"""
Security audit logging helpers.
The SecurityAuditLog model is defined in models.py.
"""
from .models import SecurityAuditLog


def log_security_event(event, request=None, user=None, details=None):
    """Helper to create an audit log entry."""
    ip = None
    ua = ''
    if request:
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    if user is None and request:
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None

    SecurityAuditLog.objects.create(
        user=user,
        event=event,
        ip_address=ip,
        user_agent=ua,
        details=details or {},
    )


def get_client_ip(request):
    """Extract client IP, respecting X-Forwarded-For behind proxy."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
