from django.urls import include, path

from .views import oauth2_callback, oauth2_login

urlpatterns = [
    path(
        "dribbble/",
        include(
            [
                path("login/", oauth2_login, name="dribbble_login"),
                # path("callback/", oauth2_callback, name="dribbble_callback"),
                path(
                    "login/callback/",
                    oauth2_callback,
                    name="dribbble_callback",
                ),
            ]
        ),
    )
]
