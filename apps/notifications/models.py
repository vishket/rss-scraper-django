from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse


class Notification(models.Model):
    """
    A notification/message sent to a user
    """
    title = models.CharField(max_length=255)
    details = models.TextField()
    user = models.ForeignKey(
        get_user_model(), related_name="notifications", on_delete=models.CASCADE
    )
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("notifications:notification_detail", args=[str(self.id)])

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()
