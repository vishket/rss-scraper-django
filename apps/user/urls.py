import django.contrib.auth.views as auth_views
from django.urls import include, path
from stronghold.decorators import public

import apps.user.views as user_views


app_name = "user"
urlpatterns = [
    path("welcome/", public(user_views.Welcome.as_view()), name="welcome"),
    path("signup/", public(user_views.Signup.as_view()), name="signup"),
    path("login/", public(user_views.Login.as_view()), name="login"),
    path("logout/", auth_views.logout_then_login, name="logout"),
]
