"""django-allauth signal receivers for inspecting linked social-account data."""

from allauth.socialaccount.signals import social_account_updated, social_account_added, pre_social_login
from allauth.account.signals import user_signed_up
from django.dispatch import receiver


def save_google_data(request, sociallogin):
    """Handle Google account data when allauth adds or refreshes the social account."""
    print("SIGNALS FILE LOADED: google")
    if sociallogin.account.provider != "google":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    # profile, created = Profile.objects.get_or_create(user=user)

    # profile.google_id = data.get("sub")
    # profile.picture_url = data.get("picture")
    # profile.save()

    print("Google data saved:")
    print("Google ID:", data.get("sub"))
    print("Picture:", data.get("picture"))


@receiver(social_account_added)
def google_account_added(request, sociallogin, **kwargs):
    print("Google account added signal received.")
    save_google_data(request, sociallogin)


@receiver(social_account_updated)
def google_account_updated(request, sociallogin, **kwargs):
    save_google_data(request, sociallogin)


def save_linkedin_data(request, sociallogin):
    """Handle LinkedIn account data when allauth adds or refreshes the social account."""

    if sociallogin.account.provider != "linkedin":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== LINKEDIN DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("LinkedIn Data:", data)
    print("===================================\n")

    # Example fields (depends on LinkedIn scopes/API)
    linkedin_id = data.get("sub") or data.get("id")
    name = data.get("name")
    picture = data.get("picture")

    print("LinkedIn ID:", linkedin_id)
    print("Name:", name)
    print("Picture:", picture)


@receiver(social_account_added)
def linkedin_account_added(request, sociallogin, **kwargs):
    save_linkedin_data(request, sociallogin)


@receiver(social_account_updated)
def linkedin_account_updated(request, sociallogin, **kwargs):
    save_linkedin_data(request, sociallogin)


def save_twitter_data(request, sociallogin):
    """Handle Twitter/X account data when allauth adds or refreshes the social account."""
    print(sociallogin.account.provider)

    if sociallogin.account.provider != "twitter":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== TWITTER DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("Twitter Data:", data)
    print("===================================\n")


@receiver(social_account_added)
def twitter_account_added(request, sociallogin, **kwargs):
    save_twitter_data(request, sociallogin)


@receiver(social_account_updated)
def twitter_account_updated(request, sociallogin, **kwargs):
    save_twitter_data(request, sociallogin)


# def save_x_data(request, sociallogin):
#     if sociallogin.account.provider not in ["twitter", "twitter_oauth2"]:
#         return

#     user = sociallogin.user
#     data = sociallogin.account.extra_data

#     print("\n========== X (TWITTER) DATA ==========")
#     print("Django User ID:", user.id)
#     print("Email:", user.email)
#     print("Provider:", sociallogin.account.provider)
#     print("X Data:", data)
#     print("======================================\n")

#     # Common fields (depends on API version)
#     x_id = (
#         data.get("id")
#         or data.get("sub")
#         or data.get("data", {}).get("id")
#     )

#     username = (
#         data.get("username")
#         or data.get("screen_name")
#         or data.get("data", {}).get("username")
#     )

#     name = (
#         data.get("name")
#         or data.get("data", {}).get("name")
#     )

#     picture = (
#         data.get("profile_image_url")
#         or data.get("profile_image_url_https")
#         or data.get("data", {}).get("profile_image_url")
#     )

#     print("X ID:", x_id)
#     print("Username:", username)
#     print("Name:", name)
#     print("Picture:", picture)

def save_facebook_data(request, sociallogin):
    """Handle Facebook account data when allauth adds or refreshes the social account."""

    print("SIGNALS FILE LOADED: facebook")
    if sociallogin.account.provider != "facebook":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== FACEBOOK DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("Facebook Data:", data)
    print("===================================\n")


def save_facebook_data(request, sociallogin):
    """Handle Facebook account data when allauth adds or refreshes the social account."""

    print("SIGNALS FILE LOADED: facebook")
    if sociallogin.account.provider != "facebook":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== FACEBOOK DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("Facebook Data:", data)
    print("===================================\n")


@receiver(social_account_added)
def facebook_account_added(request, sociallogin, **kwargs):
    save_facebook_data(request, sociallogin)


@receiver(social_account_updated)
def facebook_account_updated(request, sociallogin, **kwargs):
    save_facebook_data(request, sociallogin)


# @receiver(pre_social_login)
# def facebook_login(request, sociallogin, **kwargs):
#     """Log incoming allauth provider data before a Facebook social login is completed."""
#
#     print("Provider:", sociallogin.account.provider)
#     print("Extra data:", sociallogin.account.extra_data)
#
# @receiver(pre_social_login)
# def instagram_login(request, sociallogin, **kwargs):
#     """Log incoming allauth provider data before an Instagram social login is completed."""
#
#     print("Provider:", sociallogin.account.provider)
#     print("Extra data:", sociallogin.account.extra_data)

def save_instagram_data(request, sociallogin):
    """Handle Instagram account data when allauth adds or refreshes the social account."""

    print("SIGNALS FILE LOADED")
    if sociallogin.account.provider != "instagram":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== INSTAGRAM DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("Instagram Data:", data)
    print("===================================\n")


@receiver(social_account_added)
def instagram_account_added(request, sociallogin, **kwargs):
    save_instagram_data(request, sociallogin)


@receiver(social_account_updated)
def instagram_account_updated(request, sociallogin, **kwargs):
    save_instagram_data(request, sociallogin)


@receiver(user_signed_up)
def save_instagram_after_signup(request, user, **kwargs):
    """Capture Instagram profile data that is only available during allauth signup."""

    sociallogin = kwargs.get("sociallogin")

    if not sociallogin:
        return

    if sociallogin.account.provider != "instagram":
        return

    data = sociallogin.account.extra_data

    print("\n========== INSTAGRAM SIGNUP DATA ==========")
    print("User ID:", user.id)
    print("Instagram ID:", data.get("id"))
    print("Instagram Username:", data.get("username"))
    print("Full data:", data)
    print("==========================================\n")


def save_github_data(request, sociallogin):
    """Handle GitHub account data when allauth adds or refreshes the social account."""

    print("SIGNALS FILE LOADED: github")
    if sociallogin.account.provider != "github":
        return

    user = sociallogin.user
    data = sociallogin.account.extra_data

    print("\n========== GITHUB DATA ==========")
    print("User ID:", user.id)
    print("Email:", user.email)
    print("GitHub Data:", data)
    print("===================================\n")


@receiver(social_account_added)
def github_account_added(request, sociallogin, **kwargs):
    save_github_data(request, sociallogin)


@receiver(social_account_updated)
def github_account_updated(request, sociallogin, **kwargs):
    save_github_data(request, sociallogin)
