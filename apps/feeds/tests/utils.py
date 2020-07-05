import datetime as dt

from apps.feeds.models import Feed
from apps.feeds.models import Item

from django_dynamic_fixture import G


def mock_update_feed(feed_id):
    feed = Feed.objects.get(pk=feed_id)
    feed.items.all().delete()
    G(Item, title="newitem", feed=feed)
    feed.last_updated_at = dt.datetime.utcnow()
    feed.save()
