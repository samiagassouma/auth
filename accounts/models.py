import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification',
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Email verification for {self.user}'

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(hours=24)

    def mark_verified(self):
        self.verified_at = timezone.now()
        self.save(update_fields=['verified_at'])


class OneTimePassword(models.Model):
    EMAIL_VERIFICATION = 'email_verification'
    PASSWORD_RESET = 'password_reset'
    PURPOSE_CHOICES = (
        (EMAIL_VERIFICATION, 'Email verification'),
        (PASSWORD_RESET, 'Password reset'),
    )
    EXPIRY_MINUTES = 10

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='one_time_passwords',
    )
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('user', 'purpose', 'code')),
        ]

    def __str__(self):
        return f'{self.get_purpose_display()} OTP for {self.user}'

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(minutes=self.EXPIRY_MINUTES)

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])
