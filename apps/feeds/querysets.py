from django.db import models
from django.db.models import Count
from django.db.models import Prefetch
from django.db.models import Q


class FeedQuerySet(models.QuerySet):
    def annotate_unread_items_count(self, user):
        """
        Annotate given user's count of items that are
        marked as unread and return a title ordered
        queryset
        """
        from apps.feeds.models import Item

        return (
            self.filter(subscriber=user)
            .prefetch_related(
                Prefetch("items", queryset=Item.objects.defer("comments"))
            )
            .annotate(
                unread=Count("items", distinct=True, filter=Q(items__unread=True))
            )
            .order_by("title")
        )
