from django.contrib.auth import login as auth_login
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .serializers import (
    ForgotPasswordSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
    VerifyEmailSerializer,
)
from .user_utils import get_user_full_name


class SignupAPIView(APIView):
    """Create an inactive user and send the email-verification link."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=SignupSerializer,
        auth=[],
    )
    def post(self, request):
        print("Signup request data:", request.data)  # Debugging line
        serializer = SignupSerializer(data=request.data, context={"request": request})
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


class LoginAPIView(APIView):
    """Authenticate by email/password and return a JWT pair."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=LoginSerializer,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print("Login successful for user:", serializer.validated_data['user'].email)  # Debugging line
        print("Serializer validated data:", serializer.validated_data)  # Debugging line
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


# class VerifyEmailAPIView(APIView):
#     permission_classes = (permissions.AllowAny,)

# def get(self, request):
#     print("Verify email request data:", request.data)  # Debugging line
#     serializer = VerifyEmailSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     data = serializer.save()
#     return Response(
#         {
#             'detail': 'Email verified successfully.',
#             'access': data['access'],
#             'refresh': data['refresh'],
#             'user': {
#                 'id': data['user'].id,
#                 'full_name': get_user_full_name(data['user']),
#                 'email': data['user'].email,
#             },
#         }
#     )

class VerifyEmailAPIView(APIView):
    """Activate a user account from the token embedded in the verification URL."""

    permission_classes = (permissions.AllowAny,)

    # @extend_schema(
    #     parameters= [
    #         {
    #             "name": "token",
    #             "in": "path",
    #             "description": "The email verification token.",
    #             "required": True,
    #             "schema": {
    #                 "type": "string"
    #             }
    #         }
    #     ],
    # )
    def get(self, request, token):
        serializer = VerifyEmailSerializer(data={"token": token})
        serializer.is_valid(raise_exception=True)

        data = serializer.save()

        return Response(
            {
                "detail": "Email verified successfully.",
                "user": {
                    "id": data["user"].id,
                    "full_name": get_user_full_name(data["user"]),
                    "email": data["user"].email,
                },
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordAPIView(APIView):
    """Start the password-reset flow by sending an OTP when the account is active."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=ForgotPasswordSerializer,
        auth=[],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'If an active account exists for this email, a reset OTP has been sent.'})


class ResetPasswordAPIView(APIView):
    """Replace the user's password after validating the reset OTP."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=ResetPasswordSerializer,
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password reset successfully.'})


class ResendOTPAPIView(APIView):
    """Send another OTP for flows that allow retrying an email-delivered code."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=ResendOTPSerializer,
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'If the email is pending verification, a new OTP has been sent.'})


class GoogleLoginAPIView(APIView):
    """Log in or provision a user from a trusted Google ID token."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        # Keep Django's session auth in sync for clients that also use browser sessions.
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
