from bs4 import BeautifulSoup
import pytest

from django import urls
from django_dynamic_fixture import G

from apps.notifications.models import Notification


@pytest.mark.parametrize(
    "url_name, url_kwargs",
    [
        ("notifications:notifications", None),
        ("notifications:notification_detail", {"pk": 1}),
    ],
)
def test_protected_view(client, url_name, url_kwargs):
    """
    Verify notifications views are protected from unauthenticated access
    """
    url = urls.reverse(url_name, kwargs=url_kwargs)
    resp = client.get(url)

    assert resp.status_code == 302
    assert resp.url.startswith(urls.reverse("user:login"))


@pytest.mark.django_db
def test_notifications_page(authenticated_user, client):
    """
    Verify the notifications lists user's notifications
    """
    # Create some test notifications
    notification1 = Notification.objects.create(title="test1", user=authenticated_user)
    notification2 = Notification.objects.create(title="test2", user=authenticated_user)

    # Render notifications page
    url = urls.reverse("notifications:notifications")
    resp = client.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_notifications = [
        n.get_text().strip()
        for n in soup.select('a[href*="/notifications/notification"]')
    ]

    # Verify page is rendered with notifications
    # ordered in reverse chronological time
    assert resp.status_code == 200
    assert int(rendered_notifications[0].split(" ")[-1]) == Notification.objects.count()
    assert rendered_notifications[1:] == [notification2.title, notification1.title]


@pytest.mark.django_db
def test_notifications_detail_page(authenticated_user, client):
    """
    Verify the notifications detail page renders as expected
    """
    # Create a test notification with some test details
    notification = Notification.objects.create(
        title="failed update", user=authenticated_user, details="/feeds/1"
    )

    # Render the notifications detail page
    url = notification.get_absolute_url()
    resp = client.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")

    # Verify the details page is rendered with the
    # notification title and details
    assert resp.status_code == 200
    assert notification.title == soup.select("p")[1].get_text().strip()
    assert notification.details in soup.select("a[href]")[-1]
