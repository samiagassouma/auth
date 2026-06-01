import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse

from .models import EmailVerificationToken, OneTimePassword
from .user_utils import get_user_full_name


def generate_otp_code():
    return f'{secrets.randbelow(1000000):06d}'


def create_otp(user, purpose):
    OneTimePassword.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(used_at=timezone.now())
    return OneTimePassword.objects.create(
        user=user,
        purpose=purpose,
        code=generate_otp_code(),
    )


def send_email_verification_otp(user):
    otp = create_otp(user, OneTimePassword.EMAIL_VERIFICATION)
    send_mail(
        subject='Verify your email address',
        message=(
            f'Hi {get_user_full_name(user)},\n\n'
            f'Your email verification OTP is: {otp.code}\n\n'
            f'This code expires in {OneTimePassword.EXPIRY_MINUTES} minutes.'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp


def send_password_reset_otp(user):
    otp = create_otp(user, OneTimePassword.PASSWORD_RESET)
    send_mail(
        subject='Reset your password',
        message=(
            f'Hi {get_user_full_name(user)},\n\n'
            f'Your password reset OTP is: {otp.code}\n\n'
            f'This code expires in {OneTimePassword.EXPIRY_MINUTES} minutes.'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp


def send_verification_email(request, user):
    verification, _ = EmailVerificationToken.objects.update_or_create(
        user=user,
        defaults={},
    )
    verify_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': verification.token})
    )

    send_mail(
        subject='Verify your email address',
        message=(
            f'Hi {get_user_full_name(user)},\n\n'
            f'Please verify your email address by opening this link:\n{verify_url}\n\n'
            'This link expires in 24 hours.'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[user.email],
        fail_silently=False,
    )
