from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .views import AdobeOAuth2Adapter


class AdobeAccount(ProviderAccount):
    def get_avatar_url(self):
        return self.account.extra_data.get("picture")

    def to_str(self):
        data = self.account.extra_data
        return data.get("name") or data.get("email") or super().to_str()


class AdobeProvider(OAuth2Provider):
    id = "adobe"
    name = "Adobe"
    account_class = AdobeAccount
    oauth2_adapter_class = AdobeOAuth2Adapter

    def get_default_scope(self):
        return [
            "openid",
            "AdobeID",
            "email",
            "profile",
        ]

    def extract_uid(self, data):
        return str(data["sub"])

    def extract_common_fields(self, data):
        return {
            "email": data.get("email"),
            "email_verified": data.get("email_verified"),
            "username": data.get("email") or data.get("name") or data.get("sub"),
            "name": data.get("name"),
            "first_name": data.get("given_name"),
            "last_name": data.get("family_name"),
        }

    def extract_email_addresses(self, data):
        email = data.get("email")
        if not email:
            return []

        return [
            EmailAddress(
                email=email,
                verified=bool(data.get("email_verified")),
                primary=True,
            )
        ]


provider_classes = [AdobeProvider]
