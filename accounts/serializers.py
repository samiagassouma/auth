from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_email_verification_otp, send_password_reset_otp
from .google import GoogleAuthError, GoogleIDTokenVerifier
from .models import EmailVerificationToken, OneTimePassword
from .user_utils import build_unique_username
from .validators import (
    EMAIL_MAX_LENGTH,
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    validate_signup_email,
    validate_signup_full_name,
    validate_signup_password,
)


User = get_user_model()


def build_token_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class SignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(
        min_length=FULL_NAME_MIN_LENGTH,
        max_length=FULL_NAME_MAX_LENGTH,
        error_messages={
            'min_length': 'Full name must be 2 to 150 characters.',
            'max_length': 'Full name must be 2 to 150 characters.',
        },
    )
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_full_name(self, value):
        try:
            return validate_signup_full_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_email(self, value):
        try:
            email = validate_signup_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return email

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})

        user = User(
            username=build_unique_username(attrs['email'], attrs['full_name']),
            email=attrs['email'],
            first_name=attrs['full_name'],
        )
        try:
            validate_signup_password(attrs['password'])
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        full_name = validated_data.pop('full_name')
        email = validated_data.pop('email')
        user = User.objects.create_user(
            username=build_unique_username(email, full_name),
            email=email,
            password=password,
            first_name=full_name,
        )
        user.is_active = False
        user.save(update_fields=['is_active'])
        send_email_verification_otp(user)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    default_error_messages = {
        'invalid_otp': 'Invalid or expired OTP.',
    }

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        otp = attrs['otp'].strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.fail('invalid_otp')

        password_otp = OneTimePassword.objects.filter(
            user=user,
            purpose=OneTimePassword.EMAIL_VERIFICATION,
            code=otp,
            used_at__isnull=True,
        ).first()
        if not password_otp or password_otp.is_expired:
            self.fail('invalid_otp')

        attrs['user'] = user
        attrs['otp_instance'] = password_otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        otp = self.validated_data['otp_instance']
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        otp.mark_used()
        EmailVerificationToken.objects.filter(user=user).update(verified_at=timezone.now())
        return build_token_response(user)


class ResendEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self, **kwargs):
        email = self.validated_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            send_email_verification_otp(user)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        password = attrs['password']
        user = User.objects.filter(email__iexact=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('Please verify your email address before logging in.')

        return build_token_response(user)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    verifier_class = GoogleIDTokenVerifier

    def validate(self, attrs):
        try:
            payload = self.verifier_class().verify(attrs['id_token'])
        except GoogleAuthError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        attrs['google_payload'] = payload
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        payload = self.validated_data['google_payload']
        email = payload['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            user = User.objects.create_user(
                username=build_unique_username(
                    email,
                    payload.get('name') or payload.get('given_name', ''),
                ),
                email=email,
                first_name=payload.get('name') or payload.get('given_name', ''),
            )
            user.set_unusable_password()
            user.save(update_fields=['password'])

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])

        EmailVerificationToken.objects.filter(user=user).update(verified_at=timezone.now())
        OneTimePassword.objects.filter(
            user=user,
            purpose=OneTimePassword.EMAIL_VERIFICATION,
            used_at__isnull=True,
        ).update(used_at=timezone.now())
        return build_token_response(user)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self, **kwargs):
        email = self.validated_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            send_password_reset_otp(user)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    default_error_messages = {
        'invalid_otp': 'Invalid or expired OTP.',
    }

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        otp = attrs['otp'].strip()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        password_otp = None
        if user:
            password_otp = OneTimePassword.objects.filter(
                user=user,
                purpose=OneTimePassword.PASSWORD_RESET,
                code=otp,
                used_at__isnull=True,
            ).first()

        if not user or not password_otp or password_otp.is_expired:
            self.fail('invalid_otp')
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Passwords do not match.'})

        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)}) from exc

        attrs['user'] = user
        attrs['otp_instance'] = password_otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        otp = self.validated_data['otp_instance']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        otp.mark_used()
        return user
