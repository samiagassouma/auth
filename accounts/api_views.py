from django.contrib.auth import login as auth_login
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ForgotPasswordSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    ResendEmailOTPSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
    VerifyEmailSerializer,
)
from .user_utils import get_user_full_name


class SignupAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'detail': 'Signup successful. Check your email for the verification OTP.',
                'user': {
                    'id': user.id,
                    'full_name': get_user_full_name(user),
                    'email': user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(
            {
                'detail': 'Email verified successfully.',
                'access': data['access'],
                'refresh': data['refresh'],
                'user': {
                    'id': data['user'].id,
                    'full_name': get_user_full_name(data['user']),
                    'email': data['user'].email,
                },
            }
        )


class ResendEmailOTPAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ResendEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'If the email is pending verification, a new OTP has been sent.'})


class LoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                'access': serializer.validated_data['access'],
                'refresh': serializer.validated_data['refresh'],
                'user': {
                    'id': serializer.validated_data['user'].id,
                    'full_name': get_user_full_name(serializer.validated_data['user']),
                    'email': serializer.validated_data['user'].email,
                },
            }
        )


class GoogleLoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        auth_login(
            request._request,
            data['user'],
            backend='django.contrib.auth.backends.ModelBackend',
        )
        return Response(
            {
                'access': data['access'],
                'refresh': data['refresh'],
                'user': {
                    'id': data['user'].id,
                    'full_name': get_user_full_name(data['user']),
                    'email': data['user'].email,
                },
            }
        )


class ForgotPasswordAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'If an active account exists for this email, a reset OTP has been sent.'})


class ResetPasswordAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password reset successfully.'})
