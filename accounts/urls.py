from django.contrib.auth import views as auth_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    ForgotPasswordAPIView,
    GoogleLoginAPIView,
    LoginAPIView,
    ResendEmailOTPAPIView,
    ResetPasswordAPIView,
    SignupAPIView,
    VerifyEmailAPIView,
)
# from .forms import LoginForm
#from .views import check_email, dashboard, home, signup_view, verify_email

urlpatterns = [
    #path('', home, name='home'),
    # path(
    #     'login/',
    #     auth_views.LoginView.as_view(
    #         template_name='registration/login.html',
    #         authentication_form=LoginForm,
    #         redirect_authenticated_user=True,
    #     ),
    #     name='login',
    # ),
    # path(
    #     'password-reset/',
    #     auth_views.PasswordResetView.as_view(
    #         template_name='registration/password_reset_form.html',
    #         email_template_name='registration/password_reset_email.html',
    #         subject_template_name='registration/password_reset_subject.txt',
    #         success_url='done/',
    #     ),
    #     name='password_reset',
    # ),
    # path(
    #     'password-reset/done/',
    #     auth_views.PasswordResetDoneView.as_view(
    #         template_name='registration/password_reset_done.html',
    #     ),
    #     name='password_reset_done',
    # ),
    # path(
    #     'reset/<uidb64>/<token>/',
    #     auth_views.PasswordResetConfirmView.as_view(
    #         template_name='registration/password_reset_confirm.html',
    #         success_url='/reset/done/',
    #     ),
    #     name='password_reset_confirm',
    # ),
    # path(
    #     'reset/done/',
    #     auth_views.PasswordResetCompleteView.as_view(
    #         template_name='registration/password_reset_complete.html',
    #     ),
    #     name='password_reset_complete',
    # ),
    #path('signup/', signup_view, name='signup'),
    #path('check-email/', check_email, name='check_email'),
    #path('verify-email/<uuid:token>/', verify_email, name='verify_email'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    #path('dashboard/', dashboard, name='dashboard'),
    path('api/auth/signup/', SignupAPIView.as_view(), name='api_signup'),
    path('api/auth/verify-email/', VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('api/auth/resend-otp/', ResendEmailOTPAPIView.as_view(), name='api_resend_otp'),
    path('api/auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/auth/google/', GoogleLoginAPIView.as_view(), name='api_google_login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='api_forgot_password'),
    path('api/auth/reset-password/', ResetPasswordAPIView.as_view(), name='api_reset_password'),
]