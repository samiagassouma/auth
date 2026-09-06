import uuid
from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import EmailVerificationToken, OneTimePassword
from .providers.adobe.provider import AdobeAccount, AdobeProvider
from .providers.dribbble.provider import DribbbleAccount, DribbbleProvider


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationAPIViewTests(TestCase):
    """Unit coverage for accounts.api_views, excluding the Google login view."""

    def setUp(self):
        self.api_client = APIClient()

    def test_signup_creates_inactive_user_and_sends_verification_link(self):
        response = self.api_client.post(
            reverse("api_signup"),
            {
                "full_name": "  Alice   Example  ",
                "email": "ALICE@example.com",
                "password": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            format="json",
        )

        user = User.objects.get(email="alice@example.com")
        verification = EmailVerificationToken.objects.get(user=user)
        verify_path = reverse(
            "api_verify_email",
            kwargs={"token": verification.token},
        )

        # The active API now sends a tokenized verification link, not an OTP.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(user.is_active)
        self.assertEqual(user.get_full_name(), "Alice Example")
        self.assertEqual(response.data["user"]["id"], user.id)
        self.assertEqual(response.data["user"]["full_name"], "Alice Example")
        self.assertEqual(response.data["user"]["email"], "alice@example.com")
        self.assertNotIn("username", response.data["user"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(verify_path, mail.outbox[0].body)
        self.assertFalse(
            OneTimePassword.objects.filter(
                user=user,
                purpose=OneTimePassword.EMAIL_VERIFICATION,
            ).exists()
        )

    def test_signup_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(
            username="existing",
            email="alice@example.com",
            password="StrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_signup"),
            {
                "full_name": "Alice Example",
                "email": "ALICE@example.com",
                "password": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A user with that email already exists.", str(response.data))
        self.assertEqual(User.objects.filter(email__iexact="alice@example.com").count(), 1)

    def test_signup_rejects_invalid_name_and_email(self):
        response = self.api_client.post(
            reverse("api_signup"),
            {
                "full_name": "A",
                "email": "not-an-email",
                "password": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Full name must be 2 to 150 characters.", str(response.data))
        self.assertIn("Enter a valid email address.", str(response.data))
        self.assertFalse(User.objects.filter(first_name="A").exists())

    def test_signup_rejects_password_without_required_complexity(self):
        response = self.api_client.post(
            reverse("api_signup"),
            {
                "full_name": "Alice Example",
                "email": "alice@example.com",
                "password": "password",
                "password2": "password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Password must contain at least one uppercase letter.", str(response.data))
        self.assertIn("Password must contain at least one special character.", str(response.data))
        self.assertFalse(User.objects.filter(email="alice@example.com").exists())

    def test_signup_rejects_password_confirmation_mismatch(self):
        response = self.api_client.post(
            reverse("api_signup"),
            {
                "full_name": "Alice Example",
                "email": "alice@example.com",
                "password": "StrongPassword123!",
                "password2": "DifferentPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match.", str(response.data))
        self.assertFalse(User.objects.filter(email="alice@example.com").exists())

    def test_verify_email_activates_user_and_marks_token_verified(self):
        user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="StrongPassword123!",
            is_active=False,
        )
        verification = EmailVerificationToken.objects.create(user=user)

        response = self.api_client.get(
            reverse("api_verify_email", kwargs={"token": verification.token})
        )

        user.refresh_from_db()
        verification.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(verification.verified_at)
        self.assertEqual(response.data["detail"], "Email verified successfully.")
        self.assertEqual(response.data["user"]["id"], user.id)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_verify_email_rejects_unknown_token(self):
        response = self.api_client.get(
            reverse("api_verify_email", kwargs={"token": uuid.uuid4()})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid verification token.", str(response.data))

    def test_verify_email_rejects_expired_token(self):
        user = User.objects.create_user(
            username="carol",
            email="carol@example.com",
            password="StrongPassword123!",
            is_active=False,
        )
        verification = EmailVerificationToken.objects.create(user=user)
        EmailVerificationToken.objects.filter(pk=verification.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )

        response = self.api_client.get(
            reverse("api_verify_email", kwargs={"token": verification.token})
        )

        user.refresh_from_db()
        verification.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.is_active)
        self.assertIsNone(verification.verified_at)
        self.assertIn("Verification token has expired.", str(response.data))

    def test_verify_email_rejects_already_verified_token(self):
        user = User.objects.create_user(
            username="dave",
            email="dave@example.com",
            password="StrongPassword123!",
        )
        verification = EmailVerificationToken.objects.create(
            user=user,
            verified_at=timezone.now(),
        )

        response = self.api_client.get(
            reverse("api_verify_email", kwargs={"token": verification.token})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This email is already verified.", str(response.data))

    def test_login_returns_jwt_pair_for_active_user(self):
        user = User.objects.create_user(
            username="erin",
            email="erin@example.com",
            first_name="Erin Example",
            password="StrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_login"),
            {
                "email": "ERIN@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["id"], user.id)
        self.assertEqual(response.data["user"]["full_name"], "Erin Example")
        self.assertEqual(response.data["user"]["email"], "erin@example.com")
        self.assertNotIn("username", response.data["user"])

    def test_login_rejects_invalid_credentials(self):
        User.objects.create_user(
            username="frank",
            email="frank@example.com",
            password="StrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_login"),
            {
                "email": "frank@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid credentials.", str(response.data))

    def test_login_rejects_unverified_user(self):
        User.objects.create_user(
            username="grace",
            email="grace@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        response = self.api_client.post(
            reverse("api_login"),
            {
                "email": "grace@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please verify your email address before logging in.", str(response.data))

    def test_forgot_password_sends_reset_otp_for_active_user(self):
        user = User.objects.create_user(
            username="heidi",
            email="heidi@example.com",
            first_name="Heidi Example",
            password="OldStrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_forgot_password"),
            {"email": "HEIDI@example.com"},
            format="json",
        )

        otp = OneTimePassword.objects.get(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If an active account exists for this email, a reset OTP has been sent.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)

    def test_forgot_password_keeps_response_generic_for_inactive_or_unknown_email(self):
        User.objects.create_user(
            username="ivan",
            email="ivan@example.com",
            password="OldStrongPassword123!",
            is_active=False,
        )

        for email in ("ivan@example.com", "missing@example.com"):
            with self.subTest(email=email):
                mail.outbox.clear()

                response = self.api_client.post(
                    reverse("api_forgot_password"),
                    {"email": email},
                    format="json",
                )

                # The response remains generic to avoid account enumeration.
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_accepts_valid_otp_without_consuming_it(self):
        user = User.objects.create_user(
            username="judy",
            email="judy@example.com",
            password="OldStrongPassword123!",
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
            code="123456",
        )

        response = self.api_client.post(
            reverse("api_forgot_password"),
            {
                "email": "judy@example.com",
                "otp": "123456",
            },
            format="json",
        )

        otp.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(otp.used_at)
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_rejects_expired_otp(self):
        user = User.objects.create_user(
            username="kate",
            email="kate@example.com",
            password="OldStrongPassword123!",
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
            code="123456",
        )
        OneTimePassword.objects.filter(pk=otp.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )

        response = self.api_client.post(
            reverse("api_forgot_password"),
            {
                "email": "kate@example.com",
                "otp": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired OTP.", str(response.data))

    def test_reset_password_updates_password_and_marks_otp_used(self):
        user = User.objects.create_user(
            username="laura",
            email="laura@example.com",
            password="OldStrongPassword123!",
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
            code="123456",
        )

        response = self.api_client.post(
            reverse("api_reset_password"),
            {
                "email": "laura@example.com",
                "otp": "123456",
                "new_password": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
            format="json",
        )

        user.refresh_from_db()
        otp.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Password reset successfully.")
        self.assertTrue(user.check_password("NewStrongPassword123!"))
        self.assertIsNotNone(otp.used_at)

    def test_reset_password_rejects_mismatched_passwords_without_using_otp(self):
        user = User.objects.create_user(
            username="mallory",
            email="mallory@example.com",
            password="OldStrongPassword123!",
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
            code="123456",
        )

        response = self.api_client.post(
            reverse("api_reset_password"),
            {
                "email": "mallory@example.com",
                "otp": "123456",
                "new_password": "NewStrongPassword123!",
                "new_password2": "DifferentPassword123!",
            },
            format="json",
        )

        user.refresh_from_db()
        otp.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match.", str(response.data))
        self.assertTrue(user.check_password("OldStrongPassword123!"))
        self.assertIsNone(otp.used_at)

    def test_reset_password_rejects_invalid_otp(self):
        user = User.objects.create_user(
            username="nancy",
            email="nancy@example.com",
            password="OldStrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_reset_password"),
            {
                "email": "nancy@example.com",
                "otp": "000000",
                "new_password": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
            format="json",
        )

        user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired OTP.", str(response.data))
        self.assertTrue(user.check_password("OldStrongPassword123!"))

    def test_resend_otp_sends_reset_otp_for_active_user(self):
        user = User.objects.create_user(
            username="olivia",
            email="olivia@example.com",
            first_name="Olivia Example",
            password="StrongPassword123!",
        )

        response = self.api_client.post(
            reverse("api_resend_otp"),
            {"email": "olivia@example.com"},
            format="json",
        )

        otp = OneTimePassword.objects.get(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
        )

        # This asserts the serializer's current behavior, despite the route name.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "If the email is pending verification, a new OTP has been sent.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)

    def test_resend_otp_keeps_response_generic_for_inactive_or_unknown_email(self):
        User.objects.create_user(
            username="peggy",
            email="peggy@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        for email in ("peggy@example.com", "missing@example.com"):
            with self.subTest(email=email):
                mail.outbox.clear()

                response = self.api_client.post(
                    reverse("api_resend_otp"),
                    {"email": email},
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(mail.outbox), 0)


class OAuthProviderRoutingTests(TestCase):
    """OAuth tests are limited to allauth/built-in routing and custom providers."""

    def test_allauth_redirect_helpers_store_requested_login_intent(self):
        cases = (
            ("google_auth", "login", "/accounts/google/login/"),
            ("adobe_auth", "signup", "/accounts/adobe/login/"),
            ("dribbble_auth", "login", "/accounts/dribbble/login/"),
        )

        for url_name, process, expected_location in cases:
            with self.subTest(url_name=url_name, process=process):
                response = self.client.get(
                    reverse(url_name),
                    {"process": process},
                )

                # The view only records intent and hands off to django-allauth.
                self.assertEqual(response.status_code, status.HTTP_302_FOUND)
                self.assertEqual(response["Location"], expected_location)
                self.assertEqual(
                    self.client.session["social_auth_process"],
                    process,
                )


class CustomOAuthProviderTests(TestCase):
    """Unit tests for custom django-allauth providers created in this app."""

    @staticmethod
    def _provider_app(provider_id):
        return SimpleNamespace(provider=provider_id, provider_id=provider_id)

    def test_adobe_provider_extracts_profile_fields_and_verified_email(self):
        provider = AdobeProvider(
            request=None,
            app=self._provider_app("adobe"),
        )
        payload = {
            "sub": "adobe-user-id",
            "email": "ada@example.com",
            "email_verified": True,
            "name": "Ada Example",
            "given_name": "Ada",
            "family_name": "Example",
        }

        email_addresses = provider.extract_email_addresses(payload)

        self.assertEqual(provider.get_default_scope(), ["openid", "AdobeID", "email", "profile"])
        self.assertEqual(provider.extract_uid(payload), "adobe-user-id")
        self.assertEqual(
            provider.extract_common_fields(payload),
            {
                "email": "ada@example.com",
                "email_verified": True,
                "username": "ada@example.com",
                "name": "Ada Example",
                "first_name": "Ada",
                "last_name": "Example",
            },
        )
        self.assertEqual(len(email_addresses), 1)
        self.assertEqual(email_addresses[0].email, "ada@example.com")
        self.assertTrue(email_addresses[0].verified)
        self.assertTrue(email_addresses[0].primary)

    def test_adobe_account_prefers_name_and_picture_from_extra_data(self):
        account = SimpleNamespace(
            extra_data={
                "email": "ada@example.com",
                "name": "Ada Example",
                "picture": "https://example.com/ada.png",
            }
        )

        wrapped = AdobeAccount(account)

        self.assertEqual(wrapped.to_str(), "Ada Example")
        self.assertEqual(wrapped.get_avatar_url(), "https://example.com/ada.png")

    def test_dribbble_provider_extracts_profile_fields_and_verified_email(self):
        provider = DribbbleProvider(
            request=None,
            app=self._provider_app("dribbble"),
        )
        payload = {
            "id": 9876,
            "email": "dia@example.com",
            "login": "dia-design",
            "name": "Dia Designer",
        }

        email_addresses = provider.extract_email_addresses(payload)

        self.assertEqual(provider.get_default_scope(), ["public"])
        self.assertEqual(provider.extract_uid(payload), "9876")
        self.assertEqual(
            provider.extract_common_fields(payload),
            {
                "email": "dia@example.com",
                "email_verified": True,
                "username": "dia-design",
                "name": "Dia Designer",
            },
        )
        self.assertEqual(len(email_addresses), 1)
        self.assertEqual(email_addresses[0].email, "dia@example.com")
        self.assertTrue(email_addresses[0].verified)
        self.assertTrue(email_addresses[0].primary)

    def test_dribbble_account_prefers_login_and_profile_assets(self):
        account = SimpleNamespace(
            extra_data={
                "login": "dia-design",
                "name": "Dia Designer",
                "html_url": "https://dribbble.com/dia-design",
                "avatar_url": "https://example.com/dia.png",
            }
        )

        wrapped = DribbbleAccount(account)

        self.assertEqual(wrapped.to_str(), "dia-design")
        self.assertEqual(wrapped.get_profile_url(), "https://dribbble.com/dia-design")
        self.assertEqual(wrapped.get_avatar_url(), "https://example.com/dia.png")
