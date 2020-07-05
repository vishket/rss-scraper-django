from django import urls
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView

from apps.feeds.forms import FollowFeedForm
from apps.feeds.forms import UpdateFeedForm
from apps.feeds.forms import UpdateItemForm
from apps.feeds.models import Feed
from apps.feeds.models import Item


class MyFeedList(ListView):
    def get_queryset(self):
        return Feed.objects.annotate_unread_items_count(self.request.user)


class FeedDetail(DetailView):
    model = Feed

    def get_queryset(self):
        return Feed.objects.annotate_unread_items_count(self.request.user)


class ItemBookmarkList(ListView):
    def get_queryset(self):
        return Item.objects.filter(feed__subscriber=self.request.user, bookmark=True,)


class ItemDetail(UpdateView):
    model = Item
    form_class = UpdateItemForm
    success_url = urls.reverse_lazy("feeds:myfeeds")

    def get(self, request, *args, **kwargs):
        get = super().get(request, *args, **kwargs)
        self.object.mark_as_read()
        return get

    def form_valid(self, form):
        form.update(self.request.user, self.object)
        return super().form_valid(form)


class UnfollowFeed(DeleteView):
    model = Feed
    success_url = urls.reverse_lazy("feeds:myfeeds")
    template_name = "feeds/unfollow_feed.html"


class FollowFeed(FormView):
    form_class = FollowFeedForm
    template_name = "feeds/follow_feed.html"
    success_url = urls.reverse_lazy("feeds:myfeeds")

    def form_valid(self, form):
        form.save(self.request.user)
        return super().form_valid(form)


class UpdateFeed(UpdateView):
    model = Feed
    template_name = "feeds/update_feed.html"
    form_class = UpdateFeedForm
    success_url = urls.reverse_lazy("feeds:myfeeds")

    def form_valid(self, form):
        failed = form.update(self.object)
        return super().form_valid(form)
