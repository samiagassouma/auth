# Auth Service

This repository is a Django authentication service. It exposes a REST API for
signup, email verification, login, JWT refresh, Google ID-token login, and
password reset flows. It also includes django-allauth configuration and several
manual OAuth redirect/callback views for social providers.

The `Company`, `Offre_mission`, and `Offre_poste` apps are currently scaffolded
apps with empty models and placeholder views.

## Stack

- Django
- Django REST Framework
- djangorestframework-simplejwt
- django-allauth
- django-cors-headers
- PostgreSQL through `psycopg`
- PyJWT for Google ID-token verification
- `requests` for manual OAuth provider calls
- `python-dotenv` for loading `.env`

## Project Layout

```text
auth/                 Django project settings and root URL config
accounts/             Authentication API, serializers, models, email helpers, SSO views
Company/              Placeholder domain app
Offre_mission/        Placeholder domain app
Offre_poste/          Placeholder domain app
docs/API.md           REST and SSO endpoint documentation
manage.py             Django management entry point
```

## Main Features

- Email/password signup with an inactive user until verification.
- Email verification through a `EmailVerificationToken` link.
- JWT login and token refresh using Simple JWT.
- Password reset through six-digit one-time passwords.
- Google login through a frontend-provided Google ID token.
- django-allauth provider configuration for Adobe, Dribbble, Google, Facebook,
  Instagram, GitHub, Twitter/X, LinkedIn, Yahoo, Microsoft, Slack, Apple, and
  Telegram.
- Manual OAuth routes for Adobe/Behance, LinkedIn, Dribbble, Upwork, and
  Instagram.

See [docs/API.md](docs/API.md) for request and response contracts.

## Setup

1. Create and activate a virtual environment.

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install the project dependencies.

   The repository currently does not include a `requirements.txt`, so install
   the packages used by the code:

   ```powershell
   pip install Django djangorestframework djangorestframework-simplejwt django-allauth django-cors-headers psycopg[binary] PyJWT requests python-dotenv
   ```

3. Create a `.env` file for OAuth provider credentials.

   Do not commit real secrets. The settings module loads `.env` automatically.

4. Prepare the database.

   The current settings use PostgreSQL:

   ```text
   database: auth-db
   user: postgres
   password: root
   host: localhost
   port: 5432
   ```

   Create the database locally, then run migrations:

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create an admin user if needed.

   ```powershell
   python manage.py createsuperuser
   ```

6. Start the development server.

   ```powershell
   python manage.py runserver
   ```

## Important Settings

The service is currently configured for local development:

- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- CORS allows `http://127.0.0.1:3000` and `http://localhost:3000`
- `EMAIL_BACKEND = django.core.mail.backends.console.EmailBackend`
- Access tokens expire after 5 minutes
- Refresh tokens expire after 1 day
- Email verification links expire after 24 hours
- Password reset OTP codes expire after 10 minutes

Before production use, move secrets and database credentials into environment
variables, disable debug mode, tighten `ALLOWED_HOSTS`, configure a real email
backend, and review CSRF/CORS settings.

## Environment Variables

The current settings read these provider variables:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
GOOGLE_OAUTH2_CLIENT_ID
ADOBE_CLIENT_ID
ADOBE_CLIENT_SECRET
ADOBE_REDIRECT_URI
DRIBBBLE_CLIENT_ID
DRIBBBLE_CLIENT_SECRET
DRIBBBLE_REDIRECT_URI
LINKEDIN_CLIENT_ID
LINKEDIN_CLIENT_SECRET
LINKEDIN_REDIRECT_URI
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_REDIRECT_URI
TWITTER_CLIENT_ID
TWITTER_CLIENT_SECRET
TWITTER_REDIRECT_URI
FACEBOOK_CLIENT_ID
FACEBOOK_CLIENT_SECRET
FACEBOOK_REDIRECT_URI
INSTAGRAM_CLIENT_ID
INSTAGRAM_CLIENT_SECRET
INSTAGRAM_REDIRECT_URI
YAHOO_CLIENT_ID
YAHOO_CLIENT_SECRET
YAHOO_REDIRECT_URI
MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET
MICROSOFT_REDIRECT_URI
SLACK_CLIENT_ID
SLACK_CLIENT_SECRET
SLACK_REDIRECT_URI
```

The manual OAuth views also reference these Django settings:

```text
UPWORK_CLIENT_ID
UPWORK_CLIENT_SECRET
UPWORK_REDIRECT_URI
```

If those routes are used, add matching settings in `auth/settings.py` that read
from `.env`.

## Data Models

### EmailVerificationToken

Stores one email verification token per user.

- `user`: one-to-one relation to the Django user
- `token`: unique UUID used in the verification URL
- `created_at`: creation timestamp
- `verified_at`: set when the email is verified
- `is_verified`: true when `verified_at` is set
- `is_expired`: true after 24 hours

### OneTimePassword

Stores six-digit OTP codes for email verification or password reset.

- `user`: relation to the Django user
- `purpose`: `email_verification` or `password_reset`
- `code`: six-digit code
- `created_at`: creation timestamp
- `used_at`: set after successful use
- `is_used`: true when `used_at` is set
- `is_expired`: true after 10 minutes

Creating a new OTP marks previous unused OTPs for the same user and purpose as
used.

## Current Development Notes

- `accounts/api_views.py` defines `VerifyEmailAPIView` twice. Python keeps the
  second, token-based class, so the active API is `GET
  /api/auth/verify-email/<token>/`.
- `SignupAPIView` response text says an OTP was sent, but the current serializer
  sends a verification link.
- `ResendOTPSerializer` is named for OTP resend, but the current implementation
  sends a password reset OTP to active users.
- `accounts/tests.py` still references deleted form/template routes and older
  OTP-based verification behavior. Update tests before relying on them as a
  signal for the current API.
- `accounts/signals.py` defines django-allauth receivers, but `accounts/apps.py`
  does not currently import the module in `ready()`. Add that hook if the signal
  behavior should always be active.
- `auth/settings.py` prints Instagram OAuth environment values at import time.
  Remove those debug prints before sharing logs or deploying.
- `admin/` is registered in both `auth/urls.py` and `accounts/urls.py`, which
  causes Django's `urls.W005` warning about a non-unique `admin` namespace.
- The root route renders `index.html`; make sure that template exists before
  using the route.

## Useful Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py runserver
```
