from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import AdobeProvider

urlpatterns = default_urlpatterns(AdobeProvider)
