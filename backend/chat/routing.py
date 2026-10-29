
'''
from django.urls import path

from .consumers import ChatConsumer


websocket_urlpatterns = [
    path(
        "ws/chat/<int:handshake_id>/",
        ChatConsumer.as_asgi(),
        name="chat_websocket",
    ),
]
'''

from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path(
        "ws/chat/<int:handshake_id>/",
        ChatConsumer.as_asgi(),
        name="chat_websocket",
    ),
]