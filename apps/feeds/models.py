from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from apps.feeds.querysets import FeedQuerySet


class Feed(models.Model):
    """
    A news/article feed that users can subscribe to.
    A feed consists of multiple items
    """
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    description = models.TextField()
    rss_url = models.URLField(max_length=255, blank=True)
    subscriber = models.ForeignKey(
        get_user_model(), related_name="feeds", on_delete=models.CASCADE, blank=True
    )
    last_updated_at = models.DateTimeField(auto_now=True, blank=True)

    objects = FeedQuerySet.as_manager()

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("feeds:feed_detail", args=[str(self.id)])

    def get_update_url(self):
        return reverse("feeds:update_async", args=[str(self.id)])

    def get_unfollow_url(self):
        return reverse("feeds:unfollow", args=[str(self.id)])


class Item(models.Model):
    """
    An entity within a Feed.
    An item can have multiple comments
    """
    title = models.CharField(max_length=255, null=True, blank=True)
    link = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    unread = models.BooleanField(default=True, blank=True)
    bookmark = models.BooleanField(default=False, blank=True)
    feed = models.ForeignKey(
        Feed, on_delete=models.CASCADE, related_name="items", null=True,
    )
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("feeds:item_detail", args=[str(self.id)])

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()


class Comment(models.Model):
    """
    A text blob entered by a user in
    reference to a feed item
    """
    text = models.TextField(blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.text}"


class Profile(models.Model):
    """
    A user's profile representation.
    Extends the django User model
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    def get_unread_notifications_count(self):
        return self.user.notifications.filter(unread=True).count()


# Ensure user & profile are in sync
@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
