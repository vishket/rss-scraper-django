import feedparser


class ParseContentError(Exception):
    pass


def parse(feed):
    parsed_feed = feedparser.parse(feed)
    if parsed_feed.bozo:
        raise ParseContentError(f"{parsed_feed.bozo_exception}")

    if not has_required_fields(parsed_feed):
        raise ParseContentError(f"Feed missing a required XML channel element.")

    return parsed_feed


def has_required_fields(parsed_feed):
    """
    Check if parsed feed contains all required channel attributes
    as per rss 2.0 specification:
    https://validator.w3.org/feed/docs/rss2.html#requiredChannelElements

    :param parse_feed: FeedParserDict
    :return: Boolean
    """
    feed = parsed_feed.feed
    if not all(
        [hasattr(feed, "title"), hasattr(feed, "link"), hasattr(feed, "description")]
    ):
        return False

    entries = parsed_feed.entries

    for entry in entries:
        if not any([hasattr(entry, "title"), hasattr(entry, "description")]):
            return False
    return True
