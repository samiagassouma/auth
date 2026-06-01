from django.contrib.auth import get_user_model


def build_unique_username(email, preferred_name=''):
    User = get_user_model()
    base = preferred_name or email.split('@', 1)[0]
    base = ''.join(char for char in base if char.isalnum() or char in ('_', '-'))[:140]
    if not base:
        base = 'user'

    username = base
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix = str(counter)
        username = f'{base[:150 - len(suffix)]}{suffix}'
        counter += 1
    return username


def get_user_full_name(user):
    return user.get_full_name() or user.username

