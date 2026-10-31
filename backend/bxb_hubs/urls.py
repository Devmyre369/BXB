'''
from django.urls import path

from . import views

app_name = "hubs"

urlpatterns = [
    # Hub creation
    path("create/", views.create_hub, name="create_hub"),

    # Join request actions
    path(
        "join-requests/<int:request_id>/accept/",
        views.accept_join_request,
        name="accept_join_request",
    ),
    path(
        "join-requests/<int:request_id>/reject/",
        views.reject_join_request,
        name="reject_join_request",
    ),

    # Individual Hub actions
    path(
        "<slug:slug>/join/",
        views.request_to_join,
        name="request_to_join",
    ),
    path(
        "<slug:slug>/cancel-join/",
        views.cancel_join_request,
        name="cancel_join_request",
    ),

    # Keep the detail route last because it is the general slug route.
    path("<slug:slug>/", views.hub_detail, name="hub_detail"),
]
'''

from django.urls import path

from . import views

app_name = "hubs"

urlpatterns = [
    # Hub directory
    path("", views.hub_list, name="hub_list"),

    # Hub creation
    path("create/", views.create_hub, name="create_hub"),

    # Join request actions
    path(
        "join-requests/<int:request_id>/accept/",
        views.accept_join_request,
        name="accept_join_request",
    ),
    path(
        "join-requests/<int:request_id>/reject/",
        views.reject_join_request,
        name="reject_join_request",
    ),

    # Individual Hub actions
    path("<slug:slug>/join/", views.request_to_join, name="request_to_join"),
    path(
        "<slug:slug>/cancel-join/",
        views.cancel_join_request,
        name="cancel_join_request",
    ),

    # Hub detail — keep this last
    path("<slug:slug>/", views.hub_detail, name="hub_detail"),
]
