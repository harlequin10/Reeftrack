from django.http import HttpResponseRedirect
from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class GoogleSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom behaviour for Google OAuth sign-in.

    - New Google users are created without a password (unusable password).
    - New Google users must complete their profile (first/middle/last name)
      before using the system.
    - If an existing account (whose profile is not approved) has the same
      email, block the sign-in so the approval workflow is not bypassed.
    """

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        profile = getattr(user, 'profile', None)
        if profile is not None:
            profile.profile_completed = False
            profile.save(update_fields=['profile_completed'])
        return user

    def pre_social_login(self, request, sociallogin):
        email = (sociallogin.account.extra_data or {}).get('email')
        if not email or sociallogin.is_existing:
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()

        existing = User.objects.filter(email__iexact=email).first()
        if existing is None:
            return
        profile = getattr(existing, 'profile', None)
        if profile is not None and profile.status != 'approved':
            raise ImmediateHttpResponse(
                HttpResponseRedirect(reverse('login') + '?status=pending')
            )


class ReefTrackAccountAdapter(DefaultAccountAdapter):
    """Redirect to the profile-completion step for new Google users."""

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'profile'):
            if not user.profile.profile_completed:
                return reverse('complete_google_profile')
        return super().get_login_redirect_url(request)
