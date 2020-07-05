from feedparser import FeedParserDict
import pytest

from django_dynamic_fixture import G

from apps.feeds import feed_parser
from apps.feeds.feed_parser import has_required_fields
from apps.feeds.feed_parser import ParseContentError
from apps.feeds.feed_parser import parse


@pytest.fixture
def rss_feed_missing_feed_title():
    """An invalid rss feed for tests"""
    item1 = {"title": "test1", "link": "https://test.com/item1"}
    item2 = {"title": "test1", "description": "foo"}
    item3 = {"title": "test3", "summary": "bar"}
    entries = [FeedParserDict(item1), FeedParserDict(item2), FeedParserDict(item3)]

    feed = FeedParserDict({"title": "test", "description": "testing"})

    rss_feed = FeedParserDict({"feed": feed, "entries": entries})
    return rss_feed


@pytest.fixture
def rss_feed_missing_item_title_and_description():
    """An invalid rss feed for tests"""
    item1 = {"title": "test1", "link": "https://test.com/item1"}
    item2 = {"link": "https://test.com/item2"}
    item3 = {"title": "test3", "summary": "bar"}
    entries = [FeedParserDict(item1), FeedParserDict(item2), FeedParserDict(item3)]

    feed = FeedParserDict(
        {"title": "test", "link": "https://test.com", "description": "testing"}
    )

    rss_feed = FeedParserDict({"feed": feed, "entries": entries})
    return rss_feed


def test_parse_rss_success(mocker, rss_feed):
    """
    Test parsing feed xml successfully
    """
    mocker.patch("apps.feeds.feed_parser.feedparser.parse", return_value=rss_feed)
    mocker.patch("apps.feeds.feed_parser.has_required_fields", return_value=True)

    parsed_data = parse("foo")

    assert parsed_data.feed == rss_feed.feed


def test_parse_rss_error(mocker):
    """
    Test exceptions are handled for error while parsing rss
    """
    feed = FeedParserDict({"bozo": True, "bozo_exception": "details",})
    mocker.patch("apps.feeds.feed_parser.feedparser.parse", return_value=feed)

    with pytest.raises(ParseContentError):
        parse("foo")

    feed = FeedParserDict({"bozo": False, "feed": "test"})
    mocker.patch("apps.feeds.feed_parser.feedparser.parse", return_value=feed)

    mocker.patch("apps.feeds.feed_parser.has_required_fields", return_value=False)
    with pytest.raises(ParseContentError):
        parse("foo")


def test_has_required_fields(
    rss_feed, rss_feed_missing_feed_title, rss_feed_missing_item_title_and_description
):
    """
    Validate missing required feed fields/attributes
    """
    assert has_required_fields(rss_feed)
    assert not has_required_fields(rss_feed_missing_feed_title)
    assert not has_required_fields(rss_feed_missing_item_title_and_description)
