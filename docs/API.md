# API Documentation

This document describes the routes registered by `accounts/urls.py`, which is
included at the project root by `auth/urls.py`.

For local development, the default base URL is:

```text
http://127.0.0.1:8000
```

## Authentication

Protected API endpoints should use Simple JWT access tokens:

```http
Authorization: Bearer <access_token>
```

The current API endpoints in `accounts/api_views.py` are public auth endpoints
and use `AllowAny`.

## Endpoints

### POST `/api/auth/signup/`

Creates a new inactive user and sends an email verification link.

Request body:

```json
{
  "full_name": "Alice Example",
  "email": "alice@example.com",
  "password": "StrongPassword123!",
  "password2": "StrongPassword123!"
}
```

Validation:

- `full_name` must be 2 to 150 characters after whitespace normalization.
- `email` must be valid, 254 characters or fewer, and unique case-insensitively.
- `password` and `password2` must match.
- Passwords must pass Django password validation and include at least 8
  characters, one uppercase letter, one lowercase letter, and one special
  character.

Success response: `201 Created`

```json
{
  "detail": "Signup successful. Check your email for the verification OTP.",
  "user": {
    "id": 1,
    "full_name": "Alice Example",
    "email": "alice@example.com"
  }
}
```

Current behavior note: the response mentions an OTP, but the implementation
sends a verification link built from `/api/auth/verify-email/<token>/`.

### GET `/api/auth/verify-email/<token>/`

Verifies a user's email address using an `EmailVerificationToken`.

URL parameter:

```text
token: UUID string
```

Success response: `200 OK`

```json
{
  "detail": "Email verified successfully.",
  "user": {
    "id": 1,
    "full_name": "Alice Example",
    "email": "alice@example.com"
  }
}
```

Effects:

- Sets `user.is_active = True`.
- Sets `EmailVerificationToken.verified_at`.

Failure cases:

- Invalid token.
- Token already verified.
- Token older than 24 hours.

### POST `/api/auth/login/`

Authenticates an active user by email and password and returns JWT tokens.

Request body:

```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123!"
}
```

Success response: `200 OK`

```json
{
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>",
  "user": {
    "id": 1,
    "full_name": "Alice Example",
    "email": "alice@example.com"
  }
}
```

Failure cases:

- Invalid email or password.
- User exists but `is_active = False`.

### POST `/api/auth/token/refresh/`

Returns a new access token from a valid refresh token.

Request body:

```json
{
  "refresh": "<jwt-refresh-token>"
}
```

Success response: `200 OK`

```json
{
  "access": "<new-jwt-access-token>"
}
```

### POST `/api/auth/google/`

Authenticates a user with a Google ID token supplied by the frontend.

Request body:

```json
{
  "id_token": "<google-id-token>"
}
```

Validation:

- Verifies the token signature against Google's JWKS endpoint.
- Requires the audience to match `GOOGLE_OAUTH2_CLIENT_ID`.
- Requires issuer `accounts.google.com` or `https://accounts.google.com`.
- Requires an email address.
- Requires `email_verified = true`.

Success response: `200 OK`

```json
{
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>",
  "user": {
    "id": 1,
    "full_name": "Alice Example",
    "email": "alice@example.com"
  }
}
```

Effects:

- Creates the user if the email does not exist.
- Gives new Google-created users an unusable password.
- Activates inactive users.
- Marks related pending email-verification records as verified or used.
- Logs the user into the Django session as well as returning JWTs.

### POST `/api/auth/forgot-password/`

Starts or checks the password reset OTP flow.

Email-only request body:

```json
{
  "email": "alice@example.com"
}
```

With only an email, the endpoint sends a password reset OTP if an active account
exists. It returns the same generic response whether or not an active account is
found.

Optional OTP validation request body:

```json
{
  "email": "alice@example.com",
  "otp": "123456"
}
```

With `otp`, the serializer validates that the code exists, is unused, and is not
expired. The code is not marked used here; the password is changed by
`/api/auth/reset-password/`.

Success response: `200 OK`

```json
{
  "detail": "If an active account exists for this email, a reset OTP has been sent."
}
```

### POST `/api/auth/reset-password/`

Changes a user's password using a valid password reset OTP.

Request body:

```json
{
  "email": "alice@example.com",
  "otp": "123456",
  "new_password": "NewStrongPassword123!",
  "new_password2": "NewStrongPassword123!"
}
```

Validation:

- User must exist and be active.
- OTP must match an unused password reset OTP.
- OTP must be no older than 10 minutes.
- `new_password` and `new_password2` must match.
- Password must pass Django password validation.

Success response: `200 OK`

```json
{
  "detail": "Password reset successfully."
}
```

Effects:

- Updates the user's password.
- Marks the OTP as used.

### POST `/api/auth/resend-otp/`

Current implementation:

```json
{
  "email": "alice@example.com"
}
```

Success response: `200 OK`

```json
{
  "detail": "If the email is pending verification, a new OTP has been sent."
}
```

Current behavior note: despite the endpoint name and response text, the
serializer currently finds active users and sends a password reset OTP.

## Browser and SSO Routes

### GET `/`

Renders `index.html` through `accounts.sso_views.index`.

### `/accounts/`

Includes django-allauth's built-in routes.

Examples include provider login, callback, signup, and account-management routes
defined by django-allauth. Adobe is available at `/accounts/adobe/login/`.
Dribbble is available at `/accounts/dribbble/login/` and uses
`/accounts/dribbble/callback/` as its callback path.

### Manual OAuth Routes

These routes redirect to external providers, exchange authorization codes, and
return provider profile JSON or redirect locally.

| Route | View | Current behavior |
| --- | --- | --- |
| `/api/auth/adobe/` | `adobe_auth` | Stores optional login/signup intent and redirects to allauth Adobe login |
| `/api/auth/dribbble/` | `dribbble_auth` | Stores optional login/signup intent and redirects to allauth Dribbble login |
| `/auth/behance/login/` | `behance_login` | Redirects to Adobe authorization |
| `/auth/behance/callback/` | `behance_callback` | Exchanges Adobe code, fetches profile, creates/logs in user, redirects to `/` |
| `/api/auth/linkedin/` | `linkedin_login` | Redirects to LinkedIn authorization |
| `/auth/linkedin/callback/` | `linkedin_callback` | Exchanges LinkedIn code and returns userinfo JSON |
| `/auth/dribbble/` | `dribbble_login` | Redirects to Dribbble authorization |
| `/auth/dribbble/callback/` | `dribbble_callback` | Exchanges Dribbble code and returns profile JSON |
| `/auth/upwork/` | `upwork_login` | Redirects to Upwork authorization |
| `/auth/upwork/callback/` | `upwork_callback` | Exchanges Upwork code and returns profile JSON |
| `/google-data/` | `google_data` | Login-protected placeholder |

The Instagram manual route functions exist in `accounts/sso_views.py`, but their
URL patterns are currently commented out.

## Example cURL Flow

Signup:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d "{\"full_name\":\"Alice Example\",\"email\":\"alice@example.com\",\"password\":\"StrongPassword123!\",\"password2\":\"StrongPassword123!\"}"
```

Login after email verification:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"alice@example.com\",\"password\":\"StrongPassword123!\"}"
```

Refresh:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"<jwt-refresh-token>\"}"
```
