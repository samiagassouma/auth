from django.urls import reverse

from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from allauth.utils import build_absolute_uri


class DribbbleOAuth2Adapter(OAuth2Adapter):
    provider_id = "dribbble"

    access_token_url = "https://dribbble.com/oauth/token"
    authorize_url = "https://dribbble.com/oauth/authorize"
    profile_url = "https://api.dribbble.com/v2/user"

    def get_callback_url(self, request, app):
        callback_url = reverse("dribbble_callback")
        return build_absolute_uri(request, callback_url, self.redirect_uri_protocol)

    def complete_login(self, request, app, token, response=None, **kwargs):
        extra_data = self._fetch_user_info(token.token)
        print("Dribbble OAuth2Adapter complete_login extra_data:", extra_data)
        return self.get_provider().sociallogin_from_response(
            request,
            extra_data,
        )

    def _fetch_user_info(self, access_token):
        resp = get_adapter().get_requests_session().get(
            self.profile_url,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        if not resp.ok:
            raise OAuth2Error("Request to Dribbble user info failed")

        return resp.json()


oauth2_login = OAuth2LoginView.adapter_view(DribbbleOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(DribbbleOAuth2Adapter)
