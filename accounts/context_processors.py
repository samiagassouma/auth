from django.conf import settings


def google_oauth(request):
    return {
        'google_oauth2_client_id': getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', ''),
    }
