from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from stronghold.decorators import public

import rss_scraper.views

urlpatterns = [
    path("", public(rss_scraper.views.Home.as_view()), name="home"),
    path("admin/", admin.site.urls),
    path("feeds/", include("apps.feeds.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("user/", include("apps.user.urls")),
]
