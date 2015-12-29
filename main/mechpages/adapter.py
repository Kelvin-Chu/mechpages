from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import resolve_url


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        threshold = 2

        assert request.user.is_authenticated()
        if (request.user.last_login - request.user.date_joined).seconds < threshold and not EmailAddress.objects.filter(
                user=request.user, verified=True).exists():
            url = reverse_lazy('account_email_verification_sent')
        else:
            url = settings.LOGIN_REDIRECT_URL
        return resolve_url(url)
