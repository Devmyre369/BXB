
from django.urls import path
from . import views

app_name = "vibespace"

urlpatterns = [
    path("", views.explore_vibes, name="explore"),
    path("create/", views.create_vibe, name="create"),
    path("explore/", views.explore_vibes, name="explore_list"),
    path("my/", views.my_vibes, name="my_vibes"),

    path("<int:pk>/edit/", views.edit_vibe, name="edit"),
    path("<int:pk>/delete/", views.delete_vibe, name="delete"),
    path("<int:pk>/like/", views.toggle_vibe_like, name="like"),
    path("<int:pk>/revibe/", views.toggle_vibe_repost, name="revibe"),
    path("<int:pk>/comment/", views.add_vibe_comment, name="comment"),
    path("<int:pk>/follow/", views.toggle_creator_follow, name="follow"),

    path("<int:pk>/", views.vibe_detail, name="detail"),
]
