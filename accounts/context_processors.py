from django.conf import settings


def google_oauth(request):
    """Expose the Google OAuth client ID to templates that render login controls."""

    return {
        'google_oauth2_client_id': getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', ''),
    }
