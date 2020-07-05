from django.views.generic import DetailView
from django.views.generic import ListView

from apps.notifications.models import Notification


class NotificationList(ListView):
    model = Notification


class NotificationDetail(DetailView):
    model = Notification

    def get(self, request, *args, **kwargs):
        get = super().get(request, *args, **kwargs)
        self.object.mark_as_read()
        return get
