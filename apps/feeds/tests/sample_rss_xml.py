TITLE = "NU - Algemeen"
LINK = "https://www.nu.nl/algemeen"
DESCRIPTION = "Het laatste nieuws het eerst op NU.nl"
ITEM1_TITLE = "Liveblog corona | Wereldwijd meer dan 11 miljoen besmettingen"
ITEM2_TITLE = "foobar | Wereldwijd meer dan 11 miljoen besmettingen"
FEED = (
    f'<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0" xmlns:atom='
    f'"http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/"'
    f' xmlns:media="http://search.yahoo.com/mrss/"><channel><title>{TITLE}'
    f"</title><link>{LINK}</link><description>{DESCRIPTION}</description>"
    f"<item><title>{ITEM1_TITLE}</title></item>"
    f"<item><title>{ITEM2_TITLE}</title></item>"
    f"</channel></rss>"
)
