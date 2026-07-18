def role_base_template(request):
    """Context processor that sets base_template based on user role."""
    base = 'contributor/base_contributor.html'
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'profile'):
        role = request.user.profile.role
        if role == 'admin':
            base = 'admin/base_admin.html'
        elif role == 'curator':
            base = 'curator/base_curator.html'
    return {'base_template': base}
