import pytest

from django import forms
from django import urls
from django.contrib.auth import get_user_model
from django_dynamic_fixture import G

from apps.feeds.forms import FollowFeedForm
from apps.feeds.forms import UpdateFeedForm
from apps.feeds.forms import UpdateItemForm
from apps.feeds.models import Feed
from apps.feeds.models import Item
from apps.feeds.feed_parser import ParseContentError
from apps.feeds.tests.utils import mock_update_feed


@pytest.mark.parametrize("input_url", [(""), ("foo"), ("foo.com"),])
@pytest.mark.django_db
def test_feed_form_invalid_rss_link_input(input_url):
    """
    Verify the FollowFeedForm handles exceptions when
    user enters an invalid rss url
    """
    form = FollowFeedForm(data={"rss_url": input_url})
    assert not form.is_valid()


@pytest.mark.django_db
def test_feed_form_error_getting_rss_feed(mocker, requests_mock):
    """
    Verify the FollowFeedForm handles exceptions when
    getting rss feed
    """
    rss_url = "https://test.com/rss/xml"
    requests_mock.get(rss_url, exc=Exception("error"))

    form = FollowFeedForm(data={"rss_url": rss_url})
    assert not form.is_valid()

    rss_url = "https://test.com/rss/xml"
    requests_mock.get(rss_url, status_code=403, text="forbidden")

    form = FollowFeedForm(data={"rss_url": rss_url})
    assert not form.is_valid()


@pytest.mark.django_db
def test_feed_form_error_parsing_rss_feed(mocker, requests_mock):
    """
    Verify the FollowFeedForm handles exceptions when
    getting rss feed
    """
    mocker.patch("apps.feeds.forms.parse", side_effect=ParseContentError())
    rss_url = "https://test.com/rss/xml"

    form = FollowFeedForm(data={"rss_url": rss_url})
    assert not form.is_valid()


@pytest.mark.django_db
def test_update_item_form_success(mocker, requests_mock):
    """
    Verify succesfully updating an item
    """
    # Create a test user, related feeds and items
    user = G(get_user_model(), username="test")
    feed = G(Feed, title="testfeed", subscriber=user)
    item = G(Item, title="test", feed=feed)
    comment = "lol"
    form = UpdateItemForm(data={"comment": comment})

    # Verify item has no existing comments
    assert not item.comments.exists()

    # Add Comment
    assert form.is_valid()
    form.update(user, item)

    # Verify item updated with comment
    assert item.comments.count() == 1
    assert item.comments.first().text == comment

    # Verify Item is not bookmarked
    assert not item.bookmark

    # Bookmark item
    form = UpdateItemForm(data={"bookmark": True})

    assert form.is_valid()
    form.update(user, item)

    # Verify item is bookmarked
    assert item.bookmark


@pytest.mark.django_db
def test_update_feed_form_success(mocker):
    """
    Verify a user succesfully updating a feed
    by clicking and confirming via the update button
    """
    mocker.patch(
        "apps.feeds.forms.update_feed_items.delay", side_effect=mock_update_feed
    )

    # Create some existing feeds and items
    feed = G(Feed, title="fake")
    item = G(Item, title="item", feed=feed)
    before_last_updated_at = feed.last_updated_at

    assert feed.items.count() == 1
    assert feed.items.first().title == "item"

    # Confirm feed to be updated
    form = UpdateFeedForm(data={"title": feed.title})

    assert form.is_valid()

    # Update feeds
    form.update(feed)

    # Verify feed now has new items
    # and the last updated at timestamp is updated
    feed.refresh_from_db()

    after_last_updated_at = feed.last_updated_at

    assert feed.items.count() == 1
    assert feed.items.first().title == "newitem"
    assert after_last_updated_at > before_last_updated_at
