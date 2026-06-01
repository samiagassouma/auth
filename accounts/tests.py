from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .forms import LoginForm
from .google import GoogleAuthError
from .models import EmailVerificationToken, OneTimePassword


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()

    def test_signup_creates_inactive_user_and_sends_verification_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'full_name': 'Alice Example',
                'email': 'alice@example.com',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertRedirects(response, reverse('check_email'))
        user = User.objects.get(email='alice@example.com')
        verification = EmailVerificationToken.objects.get(user=user)
        self.assertEqual(user.get_full_name(), 'Alice Example')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(verification.token), mail.outbox[0].body)

    def test_signup_rejects_password_without_required_complexity(self):
        response = self.client.post(
            reverse('signup'),
            {
                'full_name': 'Alice Example',
                'email': 'alice@example.com',
                'password1': 'password',
                'password2': 'password',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password must contain at least one uppercase letter.')
        self.assertContains(response, 'Password must contain at least one special character.')
        self.assertFalse(User.objects.filter(email='alice@example.com').exists())

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(username='Alice', email='alice@example.com')

        response = self.client.post(
            reverse('signup'),
            {
                'full_name': 'Alice Example',
                'email': 'ALICE@example.com',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that email already exists.')
        self.assertEqual(User.objects.filter(email__iexact='alice@example.com').count(), 1)

    def test_signup_rejects_invalid_full_name_and_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'full_name': 'A',
                'email': 'not-an-email',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full name must be 2 to 150 characters.')
        self.assertContains(response, 'Enter a valid email address.')
        self.assertFalse(User.objects.filter(first_name='A').exists())

    def test_verification_activates_user_and_logs_them_in(self):
        user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='StrongPassword123',
            is_active=False,
        )
        verification = EmailVerificationToken.objects.create(user=user)

        response = self.client.get(reverse('verify_email', kwargs={'token': verification.token}))

        user.refresh_from_db()
        verification.refresh_from_db()
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(user.is_active)
        self.assertIsNotNone(verification.verified_at)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_unverified_user_cannot_log_in(self):
        User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='StrongPassword123',
            is_active=False,
        )

        response = self.client.post(
            reverse('login'),
            {
                'email': 'alice@example.com',
                'password': 'StrongPassword123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please verify your email address before logging in.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_allows_existing_user_to_access_dashboard(self):
        User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='StrongPassword123',
        )

        response = self.client.post(
            reverse('login'),
            {
                'email': 'bob@example.com',
                'password': 'StrongPassword123',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_password_reset_sends_email_for_active_user(self):
        User.objects.create_user(
            username='carol',
            email='carol@example.com',
            password='OldStrongPassword123',
        )

        response = self.client.post(reverse('password_reset'), {'email': 'carol@example.com'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/reset/', mail.outbox[0].body)

    def test_password_reset_changes_password_from_emailed_link(self):
        user = User.objects.create_user(
            username='dave',
            email='dave@example.com',
            password='OldStrongPassword123',
        )
        self.client.post(reverse('password_reset'), {'email': 'dave@example.com'})
        reset_path = self._extract_reset_path(mail.outbox[0].body)
        response = self.client.get(reset_path)
        confirm_path = response.url

        response = self.client.post(
            confirm_path,
            {
                'new_password1': 'NewStrongPassword123',
                'new_password2': 'NewStrongPassword123',
            },
        )

        user.refresh_from_db()
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.assertTrue(user.check_password('NewStrongPassword123'))
        self.assertFalse(user.check_password('OldStrongPassword123'))

    def test_password_reset_does_not_email_unverified_user(self):
        User.objects.create_user(
            username='erin',
            email='erin@example.com',
            password='OldStrongPassword123',
            is_active=False,
        )

        response = self.client.post(reverse('password_reset'), {'email': 'erin@example.com'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_api_signup_creates_inactive_user_and_sends_verification_otp(self):
        response = self.api_client.post(
            reverse('api_signup'),
            {
                'full_name': 'Frank Example',
                'email': 'frank@example.com',
                'password': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='frank@example.com')
        otp = OneTimePassword.objects.get(
            user=user,
            purpose=OneTimePassword.EMAIL_VERIFICATION,
        )
        self.assertEqual(user.get_full_name(), 'Frank Example')
        self.assertEqual(response.data['user']['full_name'], 'Frank Example')
        self.assertNotIn('username', response.data['user'])
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)

    def test_api_signup_rejects_password_without_required_complexity(self):
        response = self.api_client.post(
            reverse('api_signup'),
            {
                'full_name': 'Frank Example',
                'email': 'frank@example.com',
                'password': 'Password1',
                'password2': 'Password1',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Password must contain at least one special character.', str(response.data))
        self.assertFalse(User.objects.filter(email='frank@example.com').exists())

    def test_api_signup_rejects_invalid_full_name_and_email(self):
        response = self.api_client.post(
            reverse('api_signup'),
            {
                'full_name': 'F',
                'email': 'not-an-email',
                'password': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Full name must be 2 to 150 characters.', str(response.data))
        self.assertIn('Enter a valid email address.', str(response.data))
        self.assertFalse(User.objects.filter(first_name='F').exists())

    def test_api_verify_email_activates_user(self):
        user = User.objects.create_user(
            username='grace',
            email='grace@example.com',
            password='StrongPassword123',
            is_active=False,
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.EMAIL_VERIFICATION,
            code='123456',
        )

        response = self.api_client.post(
            reverse('api_verify_email'),
            {'email': 'grace@example.com', 'otp': '123456'},
            format='json',
        )

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(otp.used_at)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_api_login_returns_access_and_refresh_tokens(self):
        user = User.objects.create_user(
            username='heidi',
            email='heidi@example.com',
            first_name='Heidi Example',
            password='StrongPassword123',
        )

        response = self.api_client.post(
            reverse('api_login'),
            {'email': 'heidi@example.com', 'password': 'StrongPassword123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['id'], user.id)
        self.assertEqual(response.data['user']['full_name'], 'Heidi Example')
        self.assertNotIn('username', response.data['user'])

    def test_api_login_requires_email(self):
        User.objects.create_user(
            username='heidi',
            email='heidi@example.com',
            password='StrongPassword123',
        )

        response = self.api_client.post(
            reverse('api_login'),
            {'username': 'heidi', 'password': 'StrongPassword123'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_login_form_authenticates_with_email_and_password(self):
        user = User.objects.create_user(
            username='heidi',
            email='heidi@example.com',
            password='StrongPassword123',
        )

        form = LoginForm(data={
            'email': 'heidi@example.com',
            'password': 'StrongPassword123',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), user)

    def test_login_page_allows_email_identifier(self):
        User.objects.create_user(
            username='heidi',
            email='heidi@example.com',
            password='StrongPassword123',
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'heidi@example.com', 'password': 'StrongPassword123'},
        )

        self.assertRedirects(response, reverse('dashboard'))

    def test_api_login_rejects_unverified_user(self):
        User.objects.create_user(
            username='ivan',
            email='ivan@example.com',
            password='StrongPassword123',
            is_active=False,
        )

        response = self.api_client.post(
            reverse('api_login'),
            {'email': 'ivan@example.com', 'password': 'StrongPassword123'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Please verify your email address before logging in.', str(response.data))

    def test_api_refresh_token_returns_new_access_token(self):
        User.objects.create_user(
            username='judy',
            email='judy@example.com',
            password='StrongPassword123',
        )
        login_response = self.api_client.post(
            reverse('api_login'),
            {'email': 'judy@example.com', 'password': 'StrongPassword123'},
            format='json',
        )

        response = self.api_client.post(
            reverse('api_token_refresh'),
            {'refresh': login_response.data['refresh']},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_api_forgot_password_sends_otp_and_reset_changes_password(self):
        user = User.objects.create_user(
            username='kate',
            email='kate@example.com',
            password='OldStrongPassword123',
        )

        forgot_response = self.api_client.post(
            reverse('api_forgot_password'),
            {'email': 'kate@example.com'},
            format='json',
        )
        otp = OneTimePassword.objects.get(
            user=user,
            purpose=OneTimePassword.PASSWORD_RESET,
        )
        reset_response = self.api_client.post(
            reverse('api_reset_password'),
            {
                'email': 'kate@example.com',
                'otp': otp.code,
                'new_password': 'NewStrongPassword123',
                'new_password2': 'NewStrongPassword123',
            },
            format='json',
        )

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertEqual(forgot_response.status_code, 200)
        self.assertEqual(reset_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)
        self.assertTrue(user.check_password('NewStrongPassword123'))
        self.assertIsNotNone(otp.used_at)

    def test_api_forgot_password_does_not_email_unverified_user(self):
        User.objects.create_user(
            username='laura',
            email='laura@example.com',
            password='OldStrongPassword123',
            is_active=False,
        )

        response = self.api_client.post(
            reverse('api_forgot_password'),
            {'email': 'laura@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    @patch('accounts.serializers.GoogleLoginSerializer.verifier_class')
    def test_api_google_login_creates_active_user_and_returns_tokens(self, verifier_class):
        verifier_class.return_value.verify.return_value = {
            'iss': 'https://accounts.google.com',
            'sub': 'google-user-id',
            'email': 'maya@example.com',
            'email_verified': True,
            'name': 'Maya Example',
        }

        response = self.api_client.post(
            reverse('api_google_login'),
            {'id_token': 'valid-google-id-token'},
            format='json',
        )

        user = User.objects.get(email='maya@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_active)
        self.assertEqual(user.get_full_name(), 'Maya Example')
        self.assertFalse(user.has_usable_password())
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['id'], user.id)
        self.assertEqual(response.data['user']['full_name'], 'Maya Example')
        self.assertNotIn('username', response.data['user'])
        self.assertEqual(int(self.api_client.session['_auth_user_id']), user.id)

    @patch('accounts.serializers.GoogleLoginSerializer.verifier_class')
    def test_api_google_login_activates_existing_unverified_user(self, verifier_class):
        user = User.objects.create_user(
            username='nora',
            email='nora@example.com',
            password='StrongPassword123',
            is_active=False,
        )
        otp = OneTimePassword.objects.create(
            user=user,
            purpose=OneTimePassword.EMAIL_VERIFICATION,
            code='123456',
        )
        verifier_class.return_value.verify.return_value = {
            'iss': 'https://accounts.google.com',
            'sub': 'google-user-id',
            'email': 'nora@example.com',
            'email_verified': True,
        }

        response = self.api_client.post(
            reverse('api_google_login'),
            {'id_token': 'valid-google-id-token'},
            format='json',
        )

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_active)
        self.assertTrue(user.has_usable_password())
        self.assertIsNotNone(otp.used_at)

    @patch('accounts.serializers.GoogleLoginSerializer.verifier_class')
    def test_api_google_login_rejects_invalid_token(self, verifier_class):
        verifier_class.return_value.verify.side_effect = GoogleAuthError('Invalid Google ID token.')

        response = self.api_client.post(
            reverse('api_google_login'),
            {'id_token': 'invalid-google-id-token'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid Google ID token.', str(response.data))

    def _extract_reset_path(self, email_body):
        for line in email_body.splitlines():
            if '/reset/' in line:
                return line.split('testserver', 1)[1].strip()
        self.fail('Password reset link was not found in email body.')
