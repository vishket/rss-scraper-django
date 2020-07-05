import pytest
from feedparser import FeedParserDict

from django.contrib.auth import get_user_model
from django_dynamic_fixture import G


@pytest.fixture
def authenticated_user(client):
    """
    Create an authenticated user for tests
    """
    user = G(get_user_model(), username="test_user")
    user.set_password("password123")
    user.save()
    client.login(username="test_user", password="password123")
    return user


@pytest.fixture
def rss_feed():
    """
    Create a rss FeedParserDict obj for tests
    """
    item1 = {"title": "test1", "link": "https://test.com/item1"}
    item2 = {"title": "test2", "description": "foo"}
    item3 = {"title": "test3", "summary": "bar"}
    entries = [FeedParserDict(item1), FeedParserDict(item2), FeedParserDict(item3)]

    feed = FeedParserDict(
        {"title": "test", "link": "https://test.com", "description": "testing"}
    )

    rss_feed = FeedParserDict({"feed": feed, "entries": entries, "bozo": 0})
    return rss_feed


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "amqp://guest:guest@rabbit:5672//",
        "result_backend": "rpc://",
    }
