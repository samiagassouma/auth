import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _


FULL_NAME_MIN_LENGTH = 2
FULL_NAME_MAX_LENGTH = 150
FULL_NAME_RULE_MESSAGE = _('Full name must be 2 to 150 characters.')
EMAIL_MAX_LENGTH = 254
EMAIL_RULE_MESSAGE = _('Enter a valid email address.')
PASSWORD_PATTERN = r'(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9\s]).{8,}'
PASSWORD_RULE_MESSAGE = _(
    'Password must contain at least 8 characters, one uppercase letter, '
    'one lowercase letter, and one special character.'
)

email_validator = EmailValidator(message=EMAIL_RULE_MESSAGE)


def validate_signup_full_name(full_name):
    full_name = ' '.join(full_name.split())

    if len(full_name) < FULL_NAME_MIN_LENGTH or len(full_name) > FULL_NAME_MAX_LENGTH:
        raise ValidationError(FULL_NAME_RULE_MESSAGE)

    return full_name


def validate_signup_email(email):
    email = email.strip().lower()

    if len(email) > EMAIL_MAX_LENGTH:
        raise ValidationError(_('Email address must be 254 characters or fewer.'))
    if any(char.isspace() for char in email):
        raise ValidationError(EMAIL_RULE_MESSAGE)

    email_validator(email)
    return email


def validate_signup_password(password):
    errors = []

    if len(password) < 8:
        errors.append(_('Password must contain at least 8 characters.'))
    if not re.search(r'[A-Z]', password):
        errors.append(_('Password must contain at least one uppercase letter.'))
    if not re.search(r'[a-z]', password):
        errors.append(_('Password must contain at least one lowercase letter.'))
    if not re.search(r'[^A-Za-z0-9\s]', password):
        errors.append(_('Password must contain at least one special character.'))

    if errors:
        raise ValidationError(errors)
