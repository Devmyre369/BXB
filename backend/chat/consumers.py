
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from handshake.models import Handshake
from notifications.models import Notification
from notifications.services import notify_message

from .models import Message

logger = logging.getLogger(__name__)

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Authenticated, one-to-one WebSocket chat.

    The handshake ID identifies the conversation. Only its two participants
    can connect, and only while the handshake is accepted.
    """

    async def connect(self):
        self.user = self.scope["user"]
        self.handshake_id = self.scope["url_route"]["kwargs"].get(
            "handshake_id"
        )

        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        self.handshake = await self.get_valid_handshake()

        if self.handshake is None:
            await self.close(code=4403)
            return

        self.group_name = f"chat_handshake_{self.handshake_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

        # Opening the conversation marks incoming messages as read.
        await self.mark_messages_read()

        await self.send_json({
            "type": "connection_established",
            "handshake_id": self.handshake_id,
            "user_id": self.user.pk,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        if action == "message":
            body = content.get("body", "")

            if not isinstance(body, str):
                await self.send_error("Message body must be text.")
                return

            body = body.strip()

            if not body:
                await self.send_error("Message cannot be empty.")
                return

            if len(body) > 5000:
                await self.send_error(
                    "Messages must be 5,000 characters or fewer."
                )
                return

            # Recheck authorization on every send, not just at connection.
            recipient_id = await self.get_other_participant_id()

            if recipient_id is None:
                await self.send_error(
                    "This conversation is no longer available."
                )
                await self.close(code=4403)
                return

            message_data = await self.save_message(
                recipient_id=recipient_id,
                body=body,
            )

            if message_data is None:
                await self.send_error(
                    "The message could not be saved."
                )
                return

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.message",
                    "message": message_data,
                },
            )

        elif action == "mark_read":
            await self.mark_messages_read()
            await self.send_json({"type": "read_ack"})

        else:
            await self.send_error("Unknown chat action.")

    async def chat_message(self, event):
        await self.send_json({
            "type": "message",
            **event["message"],
        })

    async def send_error(self, message):
        await self.send_json({
            "type": "error",
            "message": message,
        })

    @database_sync_to_async
    def get_valid_handshake(self):
        try:
            handshake = Handshake.objects.get(
                pk=self.handshake_id,
                status=Handshake.Status.ACCEPTED,
            )
        except (Handshake.DoesNotExist, ValueError, TypeError):
            return None

        if self.user.pk not in (
            handshake.sender_id,
            handshake.receiver_id,
        ):
            return None

        return handshake

    @database_sync_to_async
    def get_other_participant_id(self):
        try:
            handshake = Handshake.objects.get(
                pk=self.handshake_id,
                status=Handshake.Status.ACCEPTED,
            )
        except (Handshake.DoesNotExist, ValueError, TypeError):
            return None

        if handshake.sender_id == self.user.pk:
            return handshake.receiver_id

        if handshake.receiver_id == self.user.pk:
            return handshake.sender_id

        return None

    @database_sync_to_async
    def save_message(self, recipient_id, body):
        try:
            recipient = User.objects.get(pk=recipient_id)

            message = Message(
                handshake_id=self.handshake_id,
                sender=self.user,
                recipient=recipient,
                body=body,
            )
            message.full_clean()
            message.save()

            # Use BXB's centralized notification service so user preferences
            # and optional email delivery are respected.
            notify_message(
                sender=self.user,
                recipient=recipient,
                preview=body[:80],
                target=message,
            )

            return {
                "id": message.pk,
                "handshake_id": message.handshake_id,
                "sender_id": message.sender_id,
                "sender_username": self.user.get_username(),
                "recipient_id": message.recipient_id,
                "body": message.body,
                "created_at": message.created_at.isoformat(),
                "is_read": message.is_read,
            }

        except (User.DoesNotExist, ValueError):
            logger.warning("Unable to save WebSocket chat message.")
            return None
        except Exception:
            logger.exception("Unexpected error saving WebSocket message.")
            return None

    @database_sync_to_async
    def mark_messages_read(self):
        if not hasattr(self, "handshake_id"):
            return

        Message.objects.filter(
            handshake_id=self.handshake_id,
            recipient=self.user,
            is_read=False,
        ).update(is_read=True)
