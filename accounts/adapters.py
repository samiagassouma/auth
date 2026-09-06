from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    # def is_open_for_signup(self, request, sociallogin):
    #     print("is_open_for_signup")
    #     return False

    def get_social_user_data(self, sociallogin):
        extra_data = sociallogin.account.extra_data
        provider = sociallogin.account.provider

        full_name = (
                extra_data.get("name")
                or extra_data.get("full_name")
        )

        if not full_name:
            first_name = extra_data.get("given_name", "")
            last_name = extra_data.get("family_name", "")
            full_name = f"{first_name} {last_name}".strip()

        username = (
                extra_data.get("username")
                or extra_data.get("preferred_username")
                or extra_data.get("login")
        )

        email = extra_data.get("email")

        return {
            "full_name": full_name,
            "username": username,
            "email": email,
        }

    def pre_social_login(self, request, sociallogin):
        provider = sociallogin.account.provider

        # process=login or process=signup
        process = request.session.get("social_auth_process")

        print("Provider:", provider)
        print("Process:", process)
        print("Existing:", sociallogin.is_existing)
        print(request.GET)
        print("UID:", sociallogin.account.uid)

        print("Extra data:")
        print(sociallogin.account.extra_data)

        print("Email:", sociallogin.user.email)

        user_exists = sociallogin.is_existing

        # -------------------------
        # LOGIN
        # -------------------------

        if process == "login" and not user_exists:
            raise ImmediateHttpResponse(
            redirect(
                f"{settings.FRONTEND_URL}/login"
                "?social_error=user_not_found"
            )
            )

        # -------------------------
        # SIGNUP
        # -------------------------

        if process == "signup" and user_exists:
            raise ImmediateHttpResponse(
                    redirect(
                        f"{settings.FRONTEND_URL}/signup"
                        "?social_error=account_exists"
                    )
                )
        #
        # data = self.get_social_user_data(sociallogin)
        #
        # user = sociallogin.user
        #
        # user.full_name = data["full_name"] or ""
        #
        # if data["username"]:
        #     user.username = data["username"]
        #
        # if data["email"]:
        #     user.email = data["email"]
        #
        # user.save()

    # def save_user(self, request, sociallogin, form=None):
    #     user = sociallogin.user
    #     data = sociallogin.account.extra_data
    #
    #     # -------------------------
    #     # Full name
    #     # -------------------------
    #     full_name = (
    #             data.get("name")
    #             or data.get("full_name")
    #     )
    #
    #     if not full_name:
    #         first_name = data.get("given_name", "")
    #         last_name = data.get("family_name", "")
    #
    #         full_name = f"{first_name} {last_name}".strip()
    #
    #     # -------------------------
    #     # Email
    #     # -------------------------
    #     email = data.get("email")
    #
    #     # -------------------------
    #     # Username
    #     # -------------------------
    #     username = (
    #             data.get("username")
    #             or data.get("preferred_username")
    #             or data.get("login")
    #     )
    #
    #     if not username and full_name:
    #         username = slugify(full_name)
    #
    #     if not username:
    #         username = f"user_{sociallogin.account.uid}"
    #
    #     user.username = username
    #     user.full_name = full_name or ""
    #
    #     if email:
    #         user.email = email
    #
    #     # IMPORTANT:
    #     # Let allauth save the user.
    #     super().save_user(request, sociallogin, form)

    # def save_user(self, request, sociallogin, form=None):
    #     print("save_user called")
    #     User = get_user_model()
    #
    #     user = sociallogin.user
    #     data = self.get_social_user_data(sociallogin)
    #
    #     # Full name
    #     user.full_name = data["full_name"]
    #
    #     # Email is optional
    #     if data["email"]:
    #         user.email = data["email"]
    #
    #     # Username from provider
    #     username = data["username"]
    #
    #     # If provider has no username, generate one
    #     if not username:
    #         if data["email"]:
    #             username = data["email"].split("@")[0]
    #         elif data["full_name"]:
    #             username = slugify(data["full_name"])
    #         else:
    #             username = f"user_{sociallogin.account.uid}"
    #
    #     # Make username unique
    #     base_username = slugify(username) or "user"
    #     username = base_username
    #     counter = 1
    #
    #     while User.objects.filter(username=username).exists():
    #         username = f"{base_username}_{counter}"
    #         counter += 1
    #
    #     user.username = username
    #
    #     # Let allauth perform the actual save/signup process
    #     super().save_user(request, sociallogin, form)
    #
    #
    # def populate_user(self, request, sociallogin, data):
    #     user = super().populate_user(request, sociallogin, data)
    #
    #     print("populate_user called")
    #
    #     extra_data = sociallogin.account.extra_data
    #
    #     # Full name
    #     user.full_name = (
    #         extra_data.get("name")
    #         or extra_data.get("full_name")
    #         or ""
    #     )
    #
    #     # Username
    #     username = (
    #         extra_data.get("username")
    #         or extra_data.get("preferred_username")
    #         or extra_data.get("login")
    #     )
    #
    #     if username:
    #         user.username = username
    #     else:
    #         # fallback
    #         user.username = (
    #             slugify(user.full_name)
    #             or f"user_{sociallogin.account.uid}"
    #         )
    #
    #     # Email only if provider gives one
    #     email = extra_data.get("email")
    #
    #     if email:
    #         user.email = email
    #
    #     return user