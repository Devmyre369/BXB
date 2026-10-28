"""URL configuration for the project.

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from profiles.views import (
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
from users.views import login_view, logout_view, register, verify_otp

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("auth/login/", login_view, name="login"),
    path("auth/register/", register, name="register"),
    path("auth/verify-otp/", verify_otp, name="verify_otp"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/", include("users.urls", namespace="users")),
    path("profile/", my_profile, name="my_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("profile/u/<str:username>/", public_profile, name="public_profile"),
    path(
        "profile/u/<str:username>/followers/",
        followers_list,
        name="followers_list",
    ),
    path(
        "profile/u/<str:username>/following/",
        following_list,
        name="following_list",
    ),
    path(
        "profile/u/<str:username>/connections/",
        connections_list,
        name="connections_list",
    ),
    path("profile/u/<str:username>/posts/", user_posts, name="user_posts"),
    path("profile/follow/<str:username>/", follow_user, name="follow_user"),
    path(
        "profile/unfollow/<str:username>/",
        unfollow_user,
        name="unfollow_user",
    ),
    path("profile/", include("profiles.urls", namespace="profiles")),
    path("feed/", include("posts.urls")),
    path("search/", include("search.urls")),
    path("handshake/", include("handshake.urls")),
    path("notifications/", include("notifications.urls")),
    path("ai-studio/", include("ai_studio.urls")),
    path("events/", include("events.urls")),
    path("publish/", include("publish.urls")),
    path("vibespace/", include("vibespace.urls", namespace="vibespace")),
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    """

"""URL configuration for the project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from profiles.views import (
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
from users.views import login_view, logout_view, register, verify_otp

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("auth/login/", login_view, name="login"),
    path("auth/register/", register, name="register"),
    path("auth/verify-otp/", verify_otp, name="verify_otp"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/", include("users.urls", namespace="users")),
    path("profile/", my_profile, name="my_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("profile/u/<str:username>/", public_profile, name="public_profile"),
    path(
        "profile/u/<str:username>/followers/",
        followers_list,
        name="followers_list",
    ),
    path(
        "profile/u/<str:username>/following/",
        following_list,
        name="following_list",
    ),
    path(
        "profile/u/<str:username>/connections/",
        connections_list,
        name="connections_list",
    ),
    path("profile/u/<str:username>/posts/", user_posts, name="user_posts"),
    path("profile/follow/<str:username>/", follow_user, name="follow_user"),
    path(
        "profile/unfollow/<str:username>/",
        unfollow_user,
        name="unfollow_user",
    ),
    path("profile/", include("profiles.urls", namespace="profiles")),
    path("feed/", include("posts.urls")),
    path("search/", include("search.urls")),
    path("handshake/", include("handshake.urls")),
    path("messages/", include("chat.urls", namespace="chat")),
    path("notifications/", include("notifications.urls")),
    path("ai-studio/", include("ai_studio.urls")),
    path("events/", include("events.urls")),
    path("publish/", include("publish.urls")),
    path("vibespace/", include("vibespace.urls", namespace="vibespace")),
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)