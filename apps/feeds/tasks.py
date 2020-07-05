import requests
import datetime as dt

from celery.decorators import task
from celery.exceptions import MaxRetriesExceededError

from django.conf import settings

from apps.feeds.models import Feed
from apps.feeds.models import Item
from apps.feeds.date_utils import str_to_datetime
from apps.feeds.feed_parser import ParseContentError
from apps.feeds.feed_parser import parse
from apps.notifications.models import Notification


@task(name="feeds.update_all")
def update_all_feeds():
    feed_ids = Feed.objects.values_list("id", flat=True)

    for feed_id in feed_ids:
        update_feed_items.delay(feed_id)

    return "Started feed updates!"


@task
def update_feed_items(feed_id):
    """
    For given feed ID: get new items --> parse items --> store items
    Chain function using Celery's chain primitive:
    https://docs.celeryproject.org/en/stable/userguide/canvas.html#chains

    If any function in the chain fails, it'll return a None.

    :param feed_id: str - Feed's PK
    :return: None
    """
    chain = get_feed.s(feed_id) | parse_feed.s() | update_feed.s(feed_id)
    chain()


@task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def get_feed(self, feed_id):
    """
    Get a feed's rss and return rss xml as str.

    In case of errors while requesting feed rss:
    1) retry x (max_retries)
    2) notify user/subscriber when max retries exceeds

    :param feed_id: str - Feed's PK
    :return: str - rss xml or ""
    """
    feed = Feed.objects.get(pk=feed_id)

    try:
        resp = requests.get(feed.rss_url)
        return resp.text
    except Exception as exc:
        try:
            self.retry(countdown=settings.CELERY_RETRY_BACKOFF ** self.request.retries)
        except MaxRetriesExceededError as exc:
            notify_subscriber(feed.pk)
            return ""


@task
def parse_feed(feed):
    """
    A simple wrapper to the feed parser's parse function

    :param feed: str - rss xml
    :return: List - entries/items within the feed
    """
    try:
        return parse(feed).entries
    except ParseContentError as exc:
        return []


@task
def update_feed(parsed_items, feed_id):
    """
    Create item instances from parsed items and
    update/replace given feed's items & last_updated_at

    :param parsed_items: List - Items within feed
    :param feed_id: str - Feed's PK
    :return: None
    """
    if not parsed_items:
        return None

    feed = Feed.objects.get(pk=feed_id)
    feed.items.filter(bookmark=False).delete()

    items_list = []
    for item in parsed_items:
        items_list.append(
            Item(
                title=item.get("title"),
                link=item.get("link"),
                description=item.get("description"),
                summary=item.get("summary"),
                feed=feed,
                published_at=str_to_datetime(item.get("published")),
            )
        )
    Item.objects.bulk_create(items_list)
    feed.last_updated_at = dt.datetime.utcnow()
    feed.save()


def notify_subscriber(feed_id):
    feed = Feed.objects.get(pk=feed_id)
    update_feed_url = feed.get_update_url()

    Notification.objects.create(
        title=f"Failed to Update feed: {feed}",
        details=f"{update_feed_url}",
        user=feed.subscriber,
    )
