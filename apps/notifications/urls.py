from django.urls import path

from apps.notifications import views


app_name = "notifications"
urlpatterns = [
    path("notifications/", views.NotificationList.as_view(), name="notifications",),
    path(
        "notification/<int:pk>",
        views.NotificationDetail.as_view(),
        name="notification_detail",
    ),
]
