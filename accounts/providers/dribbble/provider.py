from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .views import DribbbleOAuth2Adapter


class DribbbleAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get("html_url")

    def get_avatar_url(self):
        return self.account.extra_data.get("avatar_url")

    def to_str(self):
        data = self.account.extra_data
        return data.get("login") or data.get("name") or super().to_str()


class DribbbleProvider(OAuth2Provider):
    id = "dribbble"
    name = "Dribbble"
    account_class = DribbbleAccount
    oauth2_adapter_class = DribbbleOAuth2Adapter

    def get_default_scope(self):
        return ["public"]

    def extract_uid(self, data):
        return str(data["id"])

    def extract_common_fields(self, data):
        return {
            "email": data.get("email"),
            "email_verified": bool(data.get("email")),
            "username": data.get("login") or data.get("email") or str(data["id"]),
            "name": data.get("name"),
        }

    def extract_email_addresses(self, data):
        email = data.get("email")
        if not email:
            return []

        return [
            EmailAddress(
                email=email,
                verified=True,
                primary=True,
            )
        ]


provider_classes = [DribbbleProvider]
