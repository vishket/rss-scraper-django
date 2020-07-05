from django.urls import path

from apps.feeds import views

app_name = "feeds"
urlpatterns = [
    path("myfeeds/", views.MyFeedList.as_view(), name="myfeeds"),
    path("bookmarks/", views.ItemBookmarkList.as_view(), name="bookmarks"),
    path("follow/", views.FollowFeed.as_view(), name="follow"),
    path("feed/<int:pk>", views.FeedDetail.as_view(), name="feed_detail"),
    path("updatefeeds/<int:pk>", views.UpdateFeed.as_view(), name="update_async"),
    path("unfollow/<int:pk>", views.UnfollowFeed.as_view(), name="unfollow"),
    path("item/<int:pk>", views.ItemDetail.as_view(), name="item_detail"),
]
