import datetime as dt

import freezegun
import pytest

from django import urls
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django_dynamic_fixture import G


@pytest.mark.parametrize(
    "view_name", ["user:welcome", "user:signup", "user:login"]
)
def test_public_views(view_name, client):
    """
    Verify the signup and login views are publicly accessible
    """
    url = urls.reverse(view_name)
    resp = client.get(url)

    assert resp.status_code == 200


def test_welcome_page(client):
    """
    Verify the welcome page is rendered as expected
    """
    url = urls.reverse("user:welcome")
    resp = client.get(url)

    assert resp.status_code == 200
    assert b"Welcome To RSS Scraper!" in resp.content


@freezegun.freeze_time("2020-06-20 10:00")
@pytest.mark.django_db
def test_signup(client):
    """
    Signup a user and verifies user is created
    """
    signup_url = urls.reverse("user:signup")

    resp = client.post(
        signup_url,
        {
            "username": "test_username",
            "password1": "pump3dupk!cks",
            "password2": "pump3dupk!cks",
        },
    )

    # Verify user is redirected to home page
    assert resp.status_code == 302
    assert resp.url == urls.reverse("home")

    # Verify 'test_user' object is created
    user = get_user_model().objects.get(username="test_username")
    assert user.last_login == dt.datetime(2020, 6, 20, 10)


@pytest.mark.django_db
def test_login_and_logout(client):
    """
    Test logging in and logging out
    """
    # Create a fake user
    user = G(get_user_model(), username="fake")
    user.set_password("fake")
    user.save()

    login_url = urls.reverse("user:login")
    resp = client.post(login_url, {"username": "fake", "password": "fake"})

    # Login url should redirect to home page
    assert resp.status_code == 302
    assert resp.url == urls.reverse("home")

    # Logged in users have a session created for them
    assert Session.objects.count() == 1

    # Log out user
    logout_url = urls.reverse("user:logout")
    resp = client.get(logout_url)

    # Logout should redirect to login page
    assert resp.status_code == 302
    assert resp.url == urls.reverse("user:login")

    # Verify no active sessions
    assert not Session.objects.exists()
