from bs4 import BeautifulSoup
import datetime as dt
import freezegun
import pytest

from django import urls
from django_dynamic_fixture import G

from apps.feeds.tests import sample_rss_xml
from apps.feeds.models import Comment
from apps.feeds.models import Feed
from apps.feeds.models import Item
from apps.feeds.tests.utils import mock_update_feed
from apps.notifications.models import Notification


@pytest.fixture
def test_feed(authenticated_user):
    """
    Create a feed with items and authenticated_user
    as subscriber
    """
    feed = G(Feed, title="test_feed", subscriber=authenticated_user)
    return feed


@pytest.fixture
def test_item(test_feed):
    """
    Create a feed with items and authenticated_user
    as subscriber
    """
    item = G(Item, title="test_item", description="testing views here", feed=test_feed)
    return item


@pytest.mark.parametrize(
    "url_name, url_kwargs",
    [
        ("feeds:myfeeds", None),
        ("feeds:follow", None),
        ("feeds:bookmarks", None),
        ("feeds:feed_detail", {"pk": 1}),
        ("feeds:unfollow", {"pk": 1}),
        ("feeds:item_detail", {"pk": 1}),
        ("feeds:update_async", {"pk": 1}),
    ],
)
def test_protected_views(client, url_name, url_kwargs):
    """
    Verify feeds views are protected from unauthenticated access
    """
    url = urls.reverse(url_name, kwargs=url_kwargs)
    resp = client.get(url)

    assert resp.status_code == 302
    assert resp.url.startswith(urls.reverse("user:login"))


@pytest.mark.django_db
def test_view_myfeeds(authenticated_user, client, test_feed):
    """
    Test viewing feeds of an authenticated user
    """
    # To validate ordering of feeds, create another feed and add authenticated_user
    # as subscriber
    feed2 = G(Feed, title="newfeed", subscriber=authenticated_user)

    # To ensure the myfeeds view only displays
    # feeds belonging to currently logged in user,
    # create Feeds belonging to some other user
    feed3 = G(Feed, title="notmyfeed")

    # Render the myfeeds page for authenticated user
    myfeeds_url = urls.reverse("feeds:myfeeds")
    resp = client.get(myfeeds_url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_feeds = [
        feed.get_text().strip() for feed in soup.select('a[href*="/feeds/feed/"]')
    ]
    rendered_feed_titles = [f.split(" ")[0] for f in rendered_feeds]

    # Verify view only lists the authenticated users feeds
    assert len(rendered_feeds) == 2
    assert feed3 not in rendered_feeds

    # Verify feeds listed in reverse chronological order
    assert [feed2.title, test_feed.title] == rendered_feed_titles


@pytest.mark.django_db
def test_view_myfeeds_unread_items_count_update(client, test_feed, test_item):
    """
    Test the unread items count updates when a authenticated user
    views an item
    """
    # Create another item in users' feed to
    # properly verify unread items count update
    item = G(Item, title="newitem", feed=test_feed)

    # Render the myfeeds page for authenticated user
    myfeeds_url = urls.reverse("feeds:myfeeds")
    resp = client.get(myfeeds_url)
    assert resp.status_code == 200

    # Verify user initially has has 2 unread items
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_feeds = [
        feed.get_text().strip() for feed in soup.select('a[href*="/feeds/feed/"]')
    ]
    rendered_feed_unread_count = rendered_feeds[0].strip().split(" ")[-1]

    assert int(rendered_feed_unread_count) == 2

    # User views the 'test item' in their feed
    resp = client.get(test_item.get_absolute_url())

    # Render the myfeeds page again,
    # Verify the unread items count is now 1
    resp = client.get(myfeeds_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    rendered_feeds = [
        feed.get_text().strip() for feed in soup.select('a[href*="/feeds/feed/"]')
    ]
    rendered_feed_unread_count = rendered_feeds[0].strip().split(" ")[-1]

    assert int(rendered_feed_unread_count) == 1

    # User views the same item again
    resp = client.get(test_item.get_absolute_url())

    # Render the myfeeds page,
    resp = client.get(myfeeds_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    rendered_feeds = [
        feed.get_text().strip() for feed in soup.select('a[href*="/feeds/feed/"]')
    ]
    rendered_feed_unread_count = rendered_feeds[0].strip().split(" ")[-1]

    # Verify the unread items count remains 0
    assert int(rendered_feed_unread_count) == 1


@pytest.mark.django_db
def test_view_bookmarks(client, test_feed, test_item):
    """
    Test viewing bookmarked items for authenticated user
    """
    # User bookmarks an item
    test_item.bookmark = True
    test_item.save()

    # Create another item for authenticated user, but don't bookmark
    my_unbookmarked_item = G(Item, title="unbookmarked", feed=test_feed)

    # Create another bookmarked item, not belonging
    # to current user
    not_my_bookmarked_item = G(Item, title="notmybookmarked")

    # Render the myfeeds page
    bookmarks_url = urls.reverse("feeds:bookmarks")
    resp = client.get(bookmarks_url)

    assert resp.status_code == 200

    # Verify only the current user's bookmarked item is displayed
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_items = soup.select('a[href*="/feeds/item"]')[0].get_text().strip()

    assert rendered_items == test_item.title
    assert my_unbookmarked_item.title not in soup
    assert not_my_bookmarked_item.title not in soup


@pytest.mark.django_db
def test_view_follow_feed(authenticated_user, client):
    """
    Test viewing the follow feed page for authenticated user
    """

    # Render the follow feed page
    follow_url = urls.reverse("feeds:follow")
    resp = client.get(follow_url)

    # Verify the page renders and has a
    # field to enter the URL
    assert resp.status_code == 200
    assert b"Type in feed address" in resp.content


@freezegun.freeze_time("2020-06-20 10:00")
@pytest.mark.django_db
def test_view_follow_feed_success(mocker, authenticated_user, client, requests_mock):
    """
    Test entering a feed URL and following the feed
    for authenticated user
    """
    rss_url = "https://test.com/rss/xml"

    follow_url = urls.reverse("feeds:follow")
    requests_mock.get(rss_url, status_code=200, text=sample_rss_xml.FEED)
    total_items_before = Item.objects.count()
    # Authenticated user enters a feed url
    # and clicks the follow button
    resp = client.post(follow_url, {"rss_url": rss_url})
    total_items_after = Item.objects.count()

    # Verify user is re directed to myfeeds view
    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")

    # Verify user is now following the feed
    assert authenticated_user.feeds.count() == 1
    feed = authenticated_user.feeds.first()
    assert feed.title == sample_rss_xml.TITLE
    assert feed.link == sample_rss_xml.LINK
    assert feed.description == sample_rss_xml.DESCRIPTION
    assert feed.rss_url == rss_url
    assert feed.last_updated_at == dt.datetime(2020, 6, 20, 10)
    assert feed.items.count() == 2
    assert total_items_after == total_items_before + feed.items.count()
    assert list(feed.items.values_list("title", flat=True)) == [
        sample_rss_xml.ITEM1_TITLE,
        sample_rss_xml.ITEM2_TITLE,
    ]
    assert list(feed.items.values_list("unread", flat=True)) == [True, True]
    assert list(feed.items.values_list("bookmark", flat=True)) == [False, False]
    assert list(feed.items.values_list("comments", flat=True)) == [None, None]


@pytest.mark.django_db
def test_view_update_feed_success(mocker, client, requests_mock, test_feed):
    """
    Test manually updating a feed form the update confirmation
    page by clicking Confirm Feed Update button
    """
    mocker.patch(
        "apps.feeds.forms.update_feed_items.delay", side_effect=mock_update_feed
    )

    before_last_updated_at = test_feed.last_updated_at
    update_url = test_feed.get_update_url()

    # Confirm feed update
    resp = client.post(update_url, {"title": test_feed.title})

    test_feed.refresh_from_db()
    after_last_updated_at = test_feed.last_updated_at

    # Verify user is re directed to myfeeds view
    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")
    assert test_feed.items.count() == 1
    assert test_feed.items.first().title == "newitem"
    assert after_last_updated_at > before_last_updated_at


def mock_update_feed(feed_id):
    feed = Feed.objects.get(pk=feed_id)
    feed.items.all().delete()
    G(Item, title="newitem", feed=feed)
    feed.last_updated_at = dt.datetime.utcnow()
    feed.save()


@pytest.mark.django_db
def test_view_feed_detail(client, test_feed, test_item):
    """
    Test viewing feed detail view by authenticated user
    """
    feed_detail_url = test_feed.get_absolute_url()

    # Render the feed detail page
    resp = client.get(feed_detail_url)
    assert resp.status_code == 200

    # Verify the page displays the correct feed
    # and all its items
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_items = [
        item.get_text() for item in soup.select('a[href*="/feeds/item/"]')
    ]
    rendered_feed_title = soup.select("p")[1].get_text().strip()
    rendered_unread_notifications_count = int(
        soup.select("p")[3].get_text().strip().split(" ")[-1]
    )

    assert test_feed.title == rendered_feed_title
    assert rendered_unread_notifications_count == 1
    assert list(test_feed.items.values_list("title", flat=True)) == rendered_items


@pytest.mark.django_db
def test_view_item_detail(client, test_feed, test_item):
    """
    Test viewing item detail view by authenticated user
    """
    # Create some comments for the item
    comment1 = G(Comment, text="lost in yesterday", item=test_item)
    comment2 = G(Comment, text="let it happen", item=test_item)

    # Render the item detail page
    item_detail_url = test_item.get_absolute_url()
    resp = client.get(item_detail_url)

    assert resp.status_code == 200

    # Verify item is rendered as expected and
    # all comments are displayed
    soup = BeautifulSoup(resp.content, "html.parser")
    item_comments = list(test_item.comments.values_list("text", flat=True))
    rendered_comments = soup.select("#comments")[0].get_text().strip().split("\n")
    rendered_item_title = soup.select("p")[1].get_text().strip()
    rendered_item_description = soup.select("p")[2].get_text().strip()

    assert rendered_item_title == test_item.title
    assert rendered_item_description == test_item.description
    assert rendered_comments == item_comments


@pytest.mark.django_db
def test_view_item_detail_update_success(client, test_feed, test_item):
    """
    Test bookmarking & adding a comment to an item by authenticated user
    via the item detail page
    """
    comment = "hello world"

    item_detail_url = test_item.get_absolute_url()

    # Add a new comment
    resp = client.post(item_detail_url, {"comment": comment,})

    # Verify user is re directed to myfeeds view
    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")

    # Verify item has the new comment
    assert test_item.comments.count() == 1
    assert test_item.comments.first().text == comment
    assert not test_item.bookmark

    # Now, bookmark the same item
    resp = client.post(item_detail_url, {"bookmark": True,})
    # Verify user is re directed to myfeeds view
    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")

    # Verify item is bookmarked, comment still exists
    test_item.refresh_from_db()
    assert test_item.bookmark
    assert test_item.comments.count() == 1
    assert test_item.comments.first().text == comment


@pytest.mark.django_db
def test_view_update_feed(client, test_feed):
    """
    Test viewing the manually update feeds page by authenticated user
    """
    # Render the update feed view
    feed_update_url = test_feed.get_update_url()
    resp = client.get(feed_update_url)

    assert resp.status_code == 200

    # Verify the update feed page renders the
    # correct feed
    soup = BeautifulSoup(resp.content, "html.parser")
    assert test_feed.title == soup.select("#id_title")[0].get("value")


@pytest.mark.django_db
def test_view_unfollow_feed(client, test_feed):
    """
    Test viewing the unfollow feed page by authenticated user
    """
    # Render the unfollow feed view
    feed_unfollow_url = test_feed.get_unfollow_url()
    resp = client.get(feed_unfollow_url)

    assert resp.status_code == 200

    # Verify correct feed is displayed
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_feed_title = soup.select("p")[2].get_text().strip()

    assert test_feed.title in rendered_feed_title


@pytest.mark.django_db
def test_view_unfollow_feed_success(client, authenticated_user, test_feed):
    """
    Test unfollowing a feed by authenticated user
    """
    # Create another feed related to authenticated_user
    feed2 = G(Feed, title="test2", subscriber=authenticated_user)

    # Verify user is following 2 feeds
    assert authenticated_user.feeds.count() == 2
    assert list(authenticated_user.feeds.all()) == [feed2, test_feed]

    # Unfollow test_feed
    feed_unfollow_url = test_feed.get_unfollow_url()
    resp = client.post(feed_unfollow_url)

    # Verify user is re directed to myfeeds view
    assert resp.status_code == 302
    assert resp.url == urls.reverse("feeds:myfeeds")

    # Verify user is now only following feed2
    assert authenticated_user.feeds.count() == 1
    assert authenticated_user.feeds.first() == feed2


@pytest.mark.django_db
def test_view_myfeeds_notifications_count_update(authenticated_user, client):
    """
    Verify the notifcations count updates
    """
    # Create a test notification
    notification = G(Notification, title="test", user=authenticated_user)

    # Render myfeeds view
    myfeeds_url = urls.reverse("feeds:myfeeds")
    resp = client.get(myfeeds_url)
    assert resp.status_code == 200

    # Verify user has 1 unread notification
    soup = BeautifulSoup(resp.content, "html.parser")
    rendered_unread_notifications_count = int(
        soup.select('a[href*="/notifications/notification"]')[0]
        .get_text()
        .strip()
        .split(" ")[-1]
    )

    assert rendered_unread_notifications_count == 1

    # View notification
    client.get(notification.get_absolute_url())

    # Re visit the myfeeds page
    resp = client.get(myfeeds_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    notifications = (
        soup.select('a[href*="/notifications/notification"]')[0]
        .get_text()
        .strip()
        .split(" ")
    )

    # Verify no unread notifications renders
    assert len(notifications) == 1
    assert notifications[0] == "Notifications"
