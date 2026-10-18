from django.urls import path

from .views import (
    connections_list,
    edit_profile,
    followers_list,
    follow_user,
    following_list,
    my_profile,
    public_profile,
    unfollow_user,
    user_posts,
)

app_name = "profiles"

urlpatterns = [
    path("", my_profile, name="my_profile"),
    path("edit/", edit_profile, name="edit_profile"),
    path("u/<str:username>/followers/", followers_list, name="followers_list"),
    path("u/<str:username>/following/", following_list, name="following_list"),
    path("u/<str:username>/connections/", connections_list, name="connections_list"),
    path("u/<str:username>/posts/", user_posts, name="user_posts"),
    path("u/<str:username>/", public_profile, name="public_profile"),
    path("follow/<str:username>/", follow_user, name="follow_user"),
    path("unfollow/<str:username>/", unfollow_user, name="unfollow_user"),
]
