import jwt
from django.conf import settings
from jwt import InvalidTokenError, PyJWKClient


GOOGLE_JWKS_URL = 'https://www.googleapis.com/oauth2/v3/certs'
GOOGLE_ISSUERS = ('accounts.google.com', 'https://accounts.google.com')


class GoogleAuthError(Exception):
    """Raised when a Google ID token cannot be trusted for local login."""

    pass


class GoogleIDTokenVerifier:
    """Validate Google ID tokens against Google's signing keys and this app's client ID."""

    def __init__(self, jwks_url=GOOGLE_JWKS_URL):
        self.jwks_client = PyJWKClient(jwks_url)

    def verify(self, id_token):
        client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', '')
        if not client_id:
            raise GoogleAuthError('Google OAuth client ID is not configured.')

        try:
            # Google rotates its keys, so fetch the matching public key for this token.
            signing_key = self.jwks_client.get_signing_key_from_jwt(id_token)
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=client_id,
            )
        except InvalidTokenError as exc:
            raise GoogleAuthError('Invalid Google ID token.') from exc
        except Exception as exc:
            raise GoogleAuthError('Could not verify Google ID token.') from exc

        # The JWT signature alone is not enough; these claims must match our login rules.
        if payload.get('iss') not in GOOGLE_ISSUERS:
            raise GoogleAuthError('Invalid Google token issuer.')
        if not payload.get('email'):
            raise GoogleAuthError('Google account did not provide an email address.')
        if payload.get('email_verified') not in (True, 'true', 'True'):
            raise GoogleAuthError('Google email address is not verified.')
        return payload
