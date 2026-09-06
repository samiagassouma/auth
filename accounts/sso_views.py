"""Manual OAuth redirect/callback views for providers not handled directly by the API."""

from django import views
import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.http import JsonResponse
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
import secrets

User = get_user_model()


@login_required
def google_data(request):
    """Placeholder for returning stored Google profile data for the signed-in user."""

    ...


#     try:
#         social_account = SocialAccount.objects.get(
#             user=request.user,
#             provider="google"
#         )

#         data = social_account.extra_data
#         print("Google Extra Data:", data)

#         return JsonResponse({
#             "id": data.get("sub"),
#             "name": data.get("name"),
#             "given_name": data.get("given_name"),
#             "family_name": data.get("family_name"),
#             "email": data.get("email"),
#             "picture": data.get("picture"),
#             "verified_email": data.get("email_verified"),
#         })

#     except SocialAccount.DoesNotExist:
#         return JsonResponse(
#             {"error": "Google account not linked"},
#             status=404
#         )


def google_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/google/login/")
    # return redirect("/api/auth/google/login/")


def linkedin_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/oidc/linkedin/login/")


def facebook_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/facebook/login/")


def instagram_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/instagram/login/")


def twitter_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/twitter_oauth2/login/")


def adobe_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/adobe/login/")


def dribbble_auth(request):
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    return redirect("/accounts/dribbble/login/")


#
# def google_signup(request):
#     request.session["social_auth_process"] = "signup"
#
#     return redirect("/accounts/google/login/")


def google_login(request):
    """
    Redirect the user to Google's OpenID Connect authorization page.
    """
    intent = request.GET.get("process")
    print("intent==", intent)
    if intent == "login":
        request.session["social_auth_process"] = "login"
    elif intent == "signup":
        request.session["social_auth_process"] = "signup"

    request.session.save()
    state = secrets.token_urlsafe(32)
    print("Generated OAuth state:", state)

    # Store state in the user's Django session.
    # This protects the OAuth callback against CSRF.
    request.session["google_oauth_state"] = state

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    }

    authorization_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + urlencode(params)
    )

    return redirect(authorization_url)


def google_callback(request):
    """
    Handle Google's OAuth callback.

    Exchange the authorization code for tokens,
    retrieve the Google user's identity,
    and authenticate/create the Django user.
    """
    process = request.session.get("social_auth_process")
    print("Google callback received with params:", request.GET)
    print("Session data:", request.session.items())

    print("OAuth process:", process)

    if process not in ("login", "signup"):
        return JsonResponse(
            {"error": "Invalid authentication process."},
            status=400,
        )

    # ----------------------------------------
    # 1. Check for OAuth errors
    # ----------------------------------------

    error = request.GET.get("error")

    if error:
        return JsonResponse(
            {
                "error": error,
                "description": request.GET.get("error_description"),
            },
            status=400,
        )

    # ----------------------------------------
    # 2. Get authorization code
    # ----------------------------------------

    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"error": "Authorization code missing"},
            status=400,
        )

    # ----------------------------------------
    # 3. Validate OAuth state
    # ----------------------------------------

    state = request.GET.get("state")
    # expected_state = request.session.pop(
    #     "google_oauth_state",
    #     None,
    # )
    # or state != expected_state:
    if not state:
        return JsonResponse(
            {"error": "Invalid OAuth state"},
            status=400,
        )

    # ----------------------------------------
    # 4. Exchange code for tokens
    # ----------------------------------------

    token_url = "https://oauth2.googleapis.com/token"

    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(
        token_url,
        data=token_data,
        timeout=10,
    )

    if not token_response.ok:
        return JsonResponse(
            {
                "error": "Google token exchange failed",
                "details": token_response.json(),
            },
            status=400,
        )

    tokens = token_response.json()

    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    if not access_token:
        return JsonResponse(
            {
                "error": "Access token missing",
                "details": tokens,
            },
            status=400,
        )

    # ----------------------------------------
    # 5. Get Google user information
    # ----------------------------------------

    userinfo_url = (
        "https://openidconnect.googleapis.com/v1/userinfo"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    userinfo_response = requests.get(
        userinfo_url,
        headers=headers,
        timeout=10,
    )

    if not userinfo_response.ok:
        return JsonResponse(
            {
                "error": "Failed to retrieve Google user information",
                "details": userinfo_response.json(),
            },
            status=400,
        )

    google_user = userinfo_response.json()
    print("Google User Info:", google_user)

    # ----------------------------------------
    # 6. Extract identity
    # ----------------------------------------

    google_id = google_user.get("sub")
    email = google_user.get("email")
    email_verified = google_user.get("email_verified")
    full_name = google_user.get("name")
    picture = google_user.get("picture")

    if not google_id:
        return JsonResponse(
            {"error": "Google user ID missing"},
            status=400,
        )

    if not email:
        return JsonResponse(
            {"error": "Google email missing"},
            status=400,
        )

    if not email_verified:
        return JsonResponse(
            {"error": "Google email is not verified"},
            status=400,
        )

    user = User.objects.filter(
        email__iexact=email
    ).first()

    # ----------------------------------------
    # For now, return Google profile
    # ----------------------------------------
    if process == "login":

        if user is None:
            return redirect(
                f"{settings.FRONTEND_URL}/login"
                "?social_error=user_not_found"
            )

        # Existing user → login
        login(request, user)

        request.session.pop("social_auth_process", None)

        return redirect(
            f"{settings.FRONTEND_URL}/login"
            "?social_success=1"
        )

        # ==================================================
        # SIGNUP
        # ==================================================

    if process == "signup":

        if user is not None:
            return redirect(
                f"{settings.FRONTEND_URL}/signup"
                "?social_error=account_exists"
            )

        # New user → create
        user = User.objects.create_user(
            email=email,
            first_name=google_data.get("given_name", ""),
            last_name=google_data.get("family_name", ""),
        )

        # If you have a username field, you'll need to
        # provide it here as well.

        login(request, user)

        request.session.pop("social_auth_process", None)

        return redirect(
            f"{settings.FRONTEND_URL}/signup"
            "?social_success=1"
        )
    # return JsonResponse(
    #     {
    #         "provider": "google",
    #         "google_id": google_id,
    #         "email": email,
    #         "email_verified": email_verified,
    #         "full_name": full_name,
    #         "picture": picture,
    #     }
    # )


ADOBE_AUTH_URL = "https://ims-na1.adobelogin.com/ims/authorize/v2"
ADOBE_TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
ADOBE_USERINFO_URL = "https://ims-na1.adobelogin.com/ims/userinfo/v2"


def behance_login(request):
    """Redirect the user to Adobe/Behance to begin OAuth authorization."""

    params = {
        "client_id": settings.ADOBE_CLIENT_ID,
        "redirect_uri": settings.ADOBE_REDIRECT_URI,
        "response_type": "code",
        "scope": "AdobeID openid profile email additional_info.roles org.read",
    }
    print(f"{ADOBE_AUTH_URL}?{urlencode(params)}")
    query = requests.compat.urlencode(params)
    return redirect(f"{ADOBE_AUTH_URL}?{urlencode(params)}")


def behance_callback(request):
    """Exchange Adobe's authorization code, create/login the user, and return to the frontend."""

    print("Adobe callback received with params:", request.GET)
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        return JsonResponse({"error": error}, status=400)

    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.ADOBE_CLIENT_ID,
        "client_secret": settings.ADOBE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.ADOBE_REDIRECT_URI,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(ADOBE_TOKEN_URL, data=data, headers=headers)
    tokens = response.json()
    print("response from Adobe token endpoint:", response.json())

    if response.status_code != 200:
        return JsonResponse(response.json(), status=response.status_code)

    if "access_token" not in tokens:
        return JsonResponse(tokens, status=400)

    access_token = tokens["access_token"]

    profile_response = requests.get(
        ADOBE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print("response from Adobe userinfo endpoint:", profile_response.json())

    profile = profile_response.json()

    email = profile.get("email")
    username = profile.get("name") or email

    if not email:
        return JsonResponse({"error": "Email not returned by Adobe"}, status=400)

    User = get_user_model()

    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": username}
    )
    print(f"User {'created' if created else 'retrieved'}: {user}")

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
    )
    return redirect(f"{settings.FRONTEND_URL}/")


def linkedin_login(request):
    """Redirect the user to LinkedIn's OpenID Connect authorization page."""

    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email",
    }

    print("login")

    url = "https://www.linkedin.com/oauth/v2/authorization?" + urlencode(params)
    return redirect(url)


def linkedin_callback(request):
    """Exchange LinkedIn's authorization code and return the fetched profile data."""

    print("callback received with params:", request.GET)
    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }

    token_response = requests.post(token_url, data=data)
    token_data = token_response.json()

    access_token = token_data.get("access_token")

    if not access_token:
        return JsonResponse(token_data, status=400)

    userinfo_url = "https://api.linkedin.com/v2/userinfo"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    profile_response = requests.get(userinfo_url, headers=headers)
    print("LinkedIn Profile Response:", profile_response.text)
    profile_data = profile_response.json()

    return JsonResponse(profile_data)


DRIBBBLE_AUTH_URL = "https://dribbble.com/oauth/authorize"
DRIBBBLE_TOKEN_URL = "https://dribbble.com/oauth/token"
DRIBBBLE_USERINFO_URL = "https://api.dribbble.com/v2/user"


def dribbble_login(request):
    """Redirect the user to Dribbble to grant public profile access."""

    params = {
        "client_id": settings.DRIBBBLE_CLIENT_ID,
        "redirect_uri": settings.DRIBBBLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "public",
    }

    url = DRIBBBLE_AUTH_URL + "?" + urlencode(params)
    return redirect(url)


def dribbble_callback(request):
    """Exchange Dribbble's authorization code, create/login the user, and redirect home."""

    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    token_url = DRIBBBLE_TOKEN_URL

    data = {
        "client_id": settings.DRIBBBLE_CLIENT_ID,
        "client_secret": settings.DRIBBBLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.DRIBBBLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    token_data = token_response.json()

    access_token = token_data.get("access_token")

    if not access_token:
        return JsonResponse(token_data, status=400)

    userinfo_url = DRIBBBLE_USERINFO_URL

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    profile_response = requests.get(userinfo_url, headers=headers)
    print("Dribbble Profile Response:", profile_response.text)
    profile_data = profile_response.json()
    print("Dribbble Profile Data:", profile_data)

    email = profile_data.get("email")
    username = profile_data.get("name") or email
    User = get_user_model()

    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": username}
    )
    print(f"User {'created' if created else 'retrieved'}: {user}")

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
    )

    # return JsonResponse(profile_data)
    return redirect(f"{settings.FRONTEND_URL}/")


def upwork_login(request):
    """Redirect the user to Upwork's OAuth authorization page."""

    auth_url = "https://www.upwork.com/ab/account-security/oauth2/authorize"

    params = {
        "response_type": "code",
        "client_id": settings.UPWORK_CLIENT_ID,
        "redirect_uri": settings.UPWORK_REDIRECT_URI,
    }

    return redirect(f"{auth_url}?{urlencode(params)}")


def upwork_callback(request):
    """Exchange Upwork's authorization code and return the fetched profile data."""

    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    token_url = "https://www.upwork.com/ab/account-security/oauth2/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.UPWORK_REDIRECT_URI,
        "client_id": settings.UPWORK_CLIENT_ID,
        "client_secret": settings.UPWORK_CLIENT_SECRET,
    }

    token_response = requests.post(token_url, data=data)
    token_data = token_response.json()

    access_token = token_data.get("access_token")

    if not access_token:
        return JsonResponse(token_data, status=400)

    userinfo_url = "https://www.upwork.com/api/v3/profile/me"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    profile_response = requests.get(userinfo_url, headers=headers)
    print("Upwork Profile Response:", profile_response.text)
    profile_data = profile_response.json()

    return JsonResponse(profile_data)


def instagram_login(request):
    """Redirect the user to Instagram's OAuth authorization page."""

    auth_url = "https://api.instagram.com/oauth/authorize"

    params = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "scope": "instagram_business_basic",
        "response_type": "code",
    }

    # url = (
    #     "https://www.instagram.com/oauth/authorize"
    #     "?enable_fb_login=0"
    #     "&force_authentication=1"
    #     "&client_id=1459193286005334"
    #     "&redirect_uri=https://71b3-197-26-236-123.ngrok-free.app/accounts/instagram/login/callback/"
    #     "&response_type=code"
    #     "&scope=instagram_business_basic"
    # )
    return redirect(f"{auth_url}?{urlencode(params)}")


def instagram_callback(request):
    """Exchange Instagram's authorization code and return the basic profile data."""

    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    token_url = "https://api.instagram.com/oauth/access_token"

    data = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    token_data = token_response.json()

    access_token = token_data.get("access_token")
    user_id = token_data.get("user_id")

    if not access_token or not user_id:
        return JsonResponse(token_data, status=400)

    userinfo_url = f"https://graph.instagram.com/{user_id}?fields=id,username&access_token={access_token}"

    profile_response = requests.get(userinfo_url)
    print("Instagram Profile Response:", profile_response.text)
    profile_data = profile_response.json()
    print("Instagram Profile Data:", profile_data)

    return JsonResponse(profile_data)


def index(request):
    """Render the local landing page used by manual browser-based auth flows."""

    return render(request, "index.html")
