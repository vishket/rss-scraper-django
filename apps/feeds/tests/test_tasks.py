import feedparser
import pytest
import requests
from time import sleep

from celery.exceptions import MaxRetriesExceededError

from django_dynamic_fixture import G

from apps.feeds.models import Feed
from apps.feeds.models import Item
from apps.feeds.tasks import get_feed
from apps.feeds.tasks import notify_subscriber
from apps.feeds.tasks import parse_feed
from apps.feeds.tasks import update_feed
from apps.feeds.tasks import update_all_feeds
from apps.feeds.tasks import update_feed_items
from apps.notifications.models import Notification


@pytest.mark.django_db(transaction=True)
def test_feed_update_fail(celery_worker, mocker, requests_mock, authenticated_user):
    """
    Verify user is notified when a feed update fails
    """
    rss_url = "https://test.com/rss"
    requests_mock.get(rss_url, exc=requests.exceptions.RequestException("error"))
    mocker.patch(
        "apps.feeds.tasks.get_feed.retry", side_effect=MaxRetriesExceededError()
    )

    # Create test feed
    feed = Feed.objects.create(
        title="test",
        link="https://test.com",
        description="testing...",
        subscriber=authenticated_user,
        rss_url=rss_url,
    )
    # Verify feed has no existing items
    assert not feed.items.exists()

    # Verify user has not (unread) notifications
    assert authenticated_user.notifications.count() == 0

    update_feed_items.delay(feed.pk)
    sleep(8)

    feed.refresh_from_db()
    assert not feed.items.exists()
    assert authenticated_user.notifications.count() == 1
    notification = authenticated_user.notifications.first()
    assert feed.title in notification.title
    assert notification.details == feed.get_update_url()
    assert notification.unread


@pytest.mark.django_db(transaction=True)
def test_update_all_feeds_success(
    celery_worker, mocker, authenticated_user, requests_mock, rss_feed
):
    """
    Test successfully asynchronously updating all feeds
    """
    rss_url = "https://test.com/rss/xml"
    requests_mock.get(rss_url, status_code=200, text=str(rss_feed))
    mocker.patch("apps.feeds.tasks.parse", return_value=rss_feed)

    # Create a test feeds and related item
    feed_zero_items = G(Feed, title="test", rss_url=rss_url)
    feed_two_items = G(Feed, title="test", rss_url=rss_url)
    G(Item, title="test0", feed=feed_two_items, bookmark=True)
    G(Item, title="test1", feed=feed_two_items)

    # Verify feeds initial items
    assert feed_zero_items.items.count() == 0
    assert feed_two_items.items.count() == 2

    update_all_feeds()

    sleep(3)
    feed_zero_items.refresh_from_db()
    feed_two_items.refresh_from_db()

    # Verify both feeds are updated
    # and the two existing items are deleted
    assert Item.objects.count() == 7
    assert feed_zero_items.items.count() == 3
    assert feed_two_items.items.count() == 4


@pytest.mark.django_db(transaction=True)
def test_get_feed_success(celery_worker, authenticated_user, requests_mock):
    """
    Test successfully requesting rss xml
    """
    rss_url = "https://test.com/rss"
    resp_text = "ok"
    requests_mock.get(rss_url, status_code=200, text=resp_text)

    # Create test feed
    feed = G(
        Feed,
        title="test",
        link="https://foo.com",
        description="testing...",
        subscriber=authenticated_user,
        rss_url=rss_url,
    )

    assert get_feed.delay(feed.pk).get(timeout=10) == resp_text


@pytest.mark.django_db(transaction=True)
def test_parse_feed_fail():
    """
    Test feed items are not updated if errors raised while parsing feed
    """
    malformed_rss_feed = "foo"
    assert not parse_feed(malformed_rss_feed)


@pytest.mark.django_db(transaction=True)
def test_update_feed_fail():
    """
    Test feed is not updated if errors while updating feed
    """
    # Create a fake feed with an item
    feed = G(Feed, title="fake")
    item = G(Item, title="test", feed=feed)
    before_last_updated_at = feed.last_updated_at

    # Verify feed items are not updated
    # for empty parsed feed
    update_feed(None, feed.pk)

    feed.refresh_from_db()
    after_last_updated_at = feed.last_updated_at

    assert before_last_updated_at == after_last_updated_at
    assert feed.items.exists()


@pytest.mark.django_db(transaction=True)
def test_notify_user(authenticated_user):
    feed = G(Feed, title="test", subscriber=authenticated_user)

    assert not authenticated_user.notifications.exists()

    notify_subscriber(feed.pk)
    assert authenticated_user.notifications.count() == 1
    notification = authenticated_user.notifications.first()

    assert feed.title in notification.title
    assert feed.get_update_url() == notification.details
