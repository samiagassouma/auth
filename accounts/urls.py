from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView
from . import sso_views
from django.contrib import admin

from .api_views import (
    ForgotPasswordAPIView,
    GoogleLoginAPIView,
    LoginAPIView,
    ResendOTPAPIView,
    ResendOTPAPIView,
    ResetPasswordAPIView,
    SignupAPIView,
    VerifyEmailAPIView,
)

urlpatterns = [
    # REST authentication endpoints consumed by the frontend.
    path('api/auth/signup/', SignupAPIView.as_view(), name='api_signup'),
    path('api/auth/verify-email/<str:token>/', VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('api/auth/resend-otp/', ResendOTPAPIView.as_view(), name='api_resend_otp'),
    path('api/auth/login/', LoginAPIView.as_view(), name='api_login'),
    # path('api/auth/google/', GoogleLoginAPIView.as_view(), name='api_google_login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='api_forgot_password'),
    path('api/auth/reset-password/', ResetPasswordAPIView.as_view(), name='api_reset_password'),
    # Browser-based social login routes and allauth integration.
    path('', sso_views.index, name='index'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("auth/behance/login/", sso_views.behance_login, name="behance_login"),
    path("auth/behance/callback/", sso_views.behance_callback, name="behance_callback"),
    path("api/auth/linkedin/", sso_views.linkedin_auth, name="linkedin_auth"),
    path("api/auth/facebook/", sso_views.facebook_auth, name="facebook_auth"),
    path("api/auth/instagram/", sso_views.instagram_auth, name="instagram_auth"),
    path("api/auth/twitter/", sso_views.twitter_auth, name="twitter_auth"),
    # path("api/auth/linkedin/", sso_views.linkedin_login, name="linkedin_login"),
    # path("auth/linkedin/callback/", sso_views.linkedin_callback, name="linkedin_callback"),
    # path("authhh/google/", sso_views.google_login, name="google_login"),
    # path("auth/google/callback/", sso_views.google_callback, name="google_callback"),
    path("api/auth/adobe/", sso_views.adobe_auth, name="adobe_auth"),
    path("api/auth/dribbble/", sso_views.dribbble_auth, name="dribbble_auth"),
    path("auth/dribbble/", sso_views.dribbble_login, name="manual_dribbble_login"),
    path("auth/dribbble/callback/", sso_views.dribbble_callback, name="manual_dribbble_callback"),
    path("auth/upwork/", sso_views.upwork_login, name="upwork_login"),
    path("auth/upwork/callback/", sso_views.upwork_callback, name="upwork_callback"),
    # path("auth/instagram/", views.instagram_login, name="instagram_login"),
    # path("auth/instagram/callback/", views.instagram_callback, name="instagram_callback"),
    path("google-data/", sso_views.google_data, name="google_data"),
    path("api/auth/google/", sso_views.google_auth, name="google_auth"),
    # path(
    #     "api/auth/google/login/",
    #     sso_views.google_login,
    #     name="google_login",
    # ),
    #
    # path(
    #     "auth/google/callback/",
    #     sso_views.google_callback,
    #     name="google_callback",
    # ),
]
