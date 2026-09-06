from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Django app configuration for the authentication account module."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        ...
        # import accounts.signals
        # from allauth.socialaccount.providers.instagram.views import (
        #     InstagramOAuth2Adapter,
        # )
        #
        # InstagramOAuth2Adapter.authorize_url = (
        #     "https://www.instagram.com/oauth/authorize"
        # )
