from django.urls import path

from .views import (
    feed,
    delete_post,
    post_detail,
    like_post,
    save_post,
    comment_post,
    repost_post,
)


urlpatterns = [

    path(
        '',
        feed,
        name='feed'
    ),

    path(
        '<int:post_id>/',
        post_detail,
        name='post_detail'
    ),

    path(
        'delete/<int:post_id>/',
        delete_post,
        name='delete_post'
    ),

    path(
        '<int:post_id>/like/',
        like_post,
        name='like_post'
    ),

    path(
        '<int:post_id>/save/',
        save_post,
        name='save_post'
    ),

    path(
        '<int:post_id>/comment/',
        comment_post,
        name='comment_post'
    ),

    path(
        '<int:post_id>/repost/',
        repost_post,
        name='repost_post'
    ),
]