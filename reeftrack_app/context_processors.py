from django.conf import settings


def role_base_template(request):
    """Context processor that sets base_template based on user role."""
    base = 'contributor/base_contributor.html'
    detail_url = 'contributor_assessment_detail'
    role_label = 'Contributor'
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role == 'admin':
            base = 'admin/base_admin.html'
            detail_url = 'admin_assessment_detail'
            role_label = 'Admin'
        elif role == 'curator':
            base = 'curator/base_curator.html'
            detail_url = 'curator_assessment_detail'
            role_label = 'Curator'
    return {'base_template': base, 'assessment_detail_url': detail_url, 'role_label': role_label}


def google_oauth_configured(request):
    """True when Google OAuth client credentials are present."""
    return {
        'google_oauth_configured': bool(
            getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', '') and
            getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', '')
        )
    }
