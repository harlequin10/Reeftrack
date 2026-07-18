from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect('login')
            
            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def curator_required(view_func):
    return role_required(['curator', 'admin'])(view_func)

def contributor_required(view_func):
    return role_required(['contributor', 'curator', 'admin'])(view_func)