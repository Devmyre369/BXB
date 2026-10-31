
from django.urls import path

from . import views

app_name = "hubs"

urlpatterns = [
    path("create/", views.create_hub, name="create_hub"),
    path("<slug:slug>/", views.hub_detail, name="hub_detail"),
]
