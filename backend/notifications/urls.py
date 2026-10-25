'''

from django.urls import path

from .views import (
    notification_list,
    unread_count,
    mark_as_read,
    mark_all_as_read,
)


urlpatterns = [

    path(
        "",
        notification_list,
        name="notification_list"
    ),

    path(
        "unread-count/",
        unread_count,
        name="unread_count"
    ),

    path(
        "read/<int:notification_id>/",
        mark_as_read,
        name="mark_as_read"
    ),

    path(
        "read-all/",
        mark_all_as_read,
        name="mark_all_as_read"
    ),

]

'''

from django.urls import path

from .views import (
    notification_list,
    notification_preferences,
    unread_count,
    mark_as_read,
    mark_all_as_read,
    record_post_share,
    record_vibe_share,
)


urlpatterns = [

    path(
        "",
        notification_list,
        name="notification_list"
    ),

    path(
        "unread-count/",
        unread_count,
        name="unread_count"
    ),

    path(
        "read/<int:notification_id>/",
        mark_as_read,
        name="mark_as_read"
    ),

    path(
        "read-all/",
        mark_all_as_read,
        name="mark_all_as_read"
    ),

    path(
        "preferences/",
        notification_preferences,
        name="notification_preferences"
    ),

    path(
        "share/post/<int:post_id>/",
        record_post_share,
        name="record_post_share"
    ),

    path(
        "share/vibe/<int:pk>/",
        record_vibe_share,
        name="record_vibe_share"
    ),

]