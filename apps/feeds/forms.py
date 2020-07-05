import requests

from django import forms
from django.conf import settings

from apps.feeds.models import Comment
from apps.feeds.models import Feed
from apps.feeds.models import Item
from apps.feeds.tasks import update_feed
from apps.feeds.tasks import update_feed_items
from apps.feeds.feed_parser import ParseContentError
from apps.feeds.feed_parser import parse


class FollowFeedForm(forms.Form):
    """
    Form to allow a user to follow a feed
    by submitting a valid RSS url
    """
    rss_url = forms.URLField(label="Type in feed address")

    def clean(self):
        clean_data = super().clean()

        try:
            resp = requests.get(clean_data["rss_url"], timeout=settings.REQUEST_TIMEOUT)
        except Exception as exc:
            raise forms.ValidationError(f"Error getting RSS. Details: {exc}")

        if not resp.ok:
            raise forms.ValidationError(f"Error getting RSS. Details: {resp.reason}")
        rss = resp.text

        try:
            parsed_rss = parse(rss)
        except ParseContentError as exc:
            raise forms.ValidationError(f"Error parsing RSS. Details: {exc}")

        clean_data["parsed_rss"] = parsed_rss

        return clean_data

    def save(self, user):
        parsed_rss = self.cleaned_data["parsed_rss"]
        rss_url = self.cleaned_data["rss_url"]

        data = {
            "title": parsed_rss.feed.title,
            "link": parsed_rss.feed.link,
            "description": parsed_rss.feed.description,
            "rss_url": rss_url,
            "subscriber": user,
        }
        feed = Feed.objects.create(**data)
        update_feed(parsed_rss.entries, feed.pk)


class UpdateFeedForm(forms.ModelForm):
    """
    Form to update a feed's items asynchronously
    """
    class Meta:
        model = Feed
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs["readonly"] = True

    def update(self, feed):
        update_feed_items.delay(feed.pk)


class UpdateItemForm(forms.ModelForm):
    """
    Form to bookmark an Item or add a comment
    """
    comment = forms.CharField(required=False)

    class Meta:
        model = Item
        fields = ["bookmark"]
        widgets = {"comment": forms.Textarea}

    def update(self, user, item):
        if "bookmark" in self.changed_data:
            item.bookmark = True
            item.save()

        if "comment" in self.changed_data:
            Comment.objects.create(
                text=self.cleaned_data["comment"], item=item,
            )
