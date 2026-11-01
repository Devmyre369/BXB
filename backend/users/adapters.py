from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse


class BXBSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        """
        Called when a new social account is registered.
        """

        user = super().save_user(request, sociallogin, form)

        # New Google/GitHub users must complete BXB onboarding.
        user.onboarding_completed = False
        user.save(update_fields=["onboarding_completed"])

        return user


class BXBAccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        """
        Redirect users according to their onboarding status.
        """

        if request.user.is_authenticated and not request.user.onboarding_completed:
            return reverse("onboarding")

        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        """
        Ensure newly registered social users complete onboarding.
        """

        if request.user.is_authenticated and not request.user.onboarding_completed:
            return reverse("onboarding")

        return super().get_signup_redirect_url(request)