from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class AdobeOAuth2Adapter(OAuth2Adapter):
    provider_id = "adobe"

    access_token_url = "https://ims-na1.adobelogin.com/ims/token/v3"

    authorize_url = "https://ims-na1.adobelogin.com/ims/authorize/v2"

    profile_url = "https://ims-na1.adobelogin.com/ims/userinfo/v2"

    def complete_login(self, request, app, token, response=None, **kwargs):
        extra_data = self._fetch_user_info(token.token, app)
        print("Adobe OAuth2Adapter complete_login extra_data:", extra_data)

        if response and response.get("sub") and not extra_data.get("sub"):
            extra_data["sub"] = response["sub"]

        return self.get_provider().sociallogin_from_response(
            request,
            extra_data,
        )

    def _fetch_user_info(self, access_token, app):
        params = {}
        if app.client_id:
            params["client_id"] = app.client_id

        resp = get_adapter().get_requests_session().get(
            self.profile_url,
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        if not resp.ok:
            raise OAuth2Error("Request to Adobe user info failed")

        return resp.json()


oauth2_login = OAuth2LoginView.adapter_view(AdobeOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(AdobeOAuth2Adapter)
