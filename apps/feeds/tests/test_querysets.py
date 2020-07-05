import pytest

from django_dynamic_fixture import G

from apps.feeds.models import Feed
from apps.feeds.models import Item


@pytest.mark.django_db
def test_annotate_unread_items_count_queryset(authenticated_user):
    """
    Verify custom queryset method annotates
    the correct unread items count value
    """
    # Create a feed that the authenticated user follows
    feed = G(Feed, title="Currentusersfeed1", subscriber=authenticated_user)

    # Create item within the feed
    item1 = G(Item, title="item1", feed=feed)
    item2 = G(Item, title="item2", feed=feed)
    item3 = G(Item, title="item3", feed=feed)

    # Verify initially all items are unread
    qs = Feed.objects.annotate_unread_items_count(authenticated_user)
    assert qs.values_list("unread", flat=True)[0] == 3

    # View first item
    item1.mark_as_read()

    # Verify the unread items count decreases
    qs = Feed.objects.annotate_unread_items_count(authenticated_user)
    assert qs.values_list("unread", flat=True)[0] == 2

    # View first item again
    item1.mark_as_read()

    # Verify the unread items count does not change
    qs = Feed.objects.annotate_unread_items_count(authenticated_user)
    assert qs.values_list("unread", flat=True)[0] == 2

    # View all other items
    item2.mark_as_read()
    item3.mark_as_read()

    # Verify the unread items count is 0
    qs = Feed.objects.annotate_unread_items_count(authenticated_user)
    assert qs.values_list("unread", flat=True)[0] == 0

    # Add an item
    item4 = G(Item, title="item4", feed=feed)

    # Verify the unread items count is 1
    qs = Feed.objects.annotate_unread_items_count(authenticated_user)
    assert qs.values_list("unread", flat=True)[0] == 1
