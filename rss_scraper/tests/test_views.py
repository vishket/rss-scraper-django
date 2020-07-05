import pytest

from django import urls


@pytest.mark.django_db
def test_redirect_to_myfeeds_when_logged_in(authenticated_user, client):
    """
    Verify we redirect to the myfeeds page when
    a user is logged in
    """
    url = urls.reverse("home")
    resp = client.get(url)

    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")


def test_redirect_to_welcome_page_when_logged_out(client):
    """
    Verify we redirect to welcome page when
    user is not logged in
    """
    url = urls.reverse("home")
    resp = client.get(url)

    assert resp.status_code == 302
    assert resp.url == urls.reverse("user:welcome")
