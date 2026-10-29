
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from handshake.models import Handshake
from notifications.services import notify_message

from .models import Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.handshake_id = self.scope["url_route"]["kwargs"]["handshake_id"]
        self.group_name = f"chat_handshake_{self.handshake_id}"

        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        handshake = await self.get_accepted_handshake()

        if handshake is None:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        # Mark messages addressed to this user as read on opening the chat.
        await self.mark_messages_read()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        if action == "message":
            await self.handle_message(content)
        elif action == "mark_read":
            await self.mark_messages_read()
            await self.send_json({"type": "read", "success": True})
        else:
            await self.send_json({
                "type": "error",
                "message": "Unknown chat action.",
            })

    async def handle_message(self, content):
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

        try:
            message, recipient = await self.create_message(body)
        except PermissionError:
            await self.send_error(
                "Messaging requires an accepted handshake."
            )
            await self.close(code=4403)
            return
        except ValidationError as exc:
            await self.send_error("; ".join(exc.messages))
            return
        except Exception:
            logger.exception("Failed to create a chat message")
            await self.send_error(
                "Could not send your message. Please try again."
            )
            return

        # Notifications must not prevent a saved message from being delivered.
        try:
            await self.create_message_notification(message, recipient)
        except Exception:
            logger.exception(
                "Message saved, but its notification could not be created"
            )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": {
                    "id": message.pk,
                    "sender_id": message.sender_id,
                    "sender_username": message.sender.username,
                    "recipient_id": message.recipient_id,
                    "body": message.body,
                    "created_at": message.created_at.isoformat(),
                    "is_read": message.is_read,
                },
            },
        )

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
    def get_accepted_handshake(self):
        try:
            handshake = (
                Handshake.objects
                .select_related("sender", "receiver")
                .get(
                    pk=self.handshake_id,
                    status=Handshake.Status.ACCEPTED,
                )
            )
        except Handshake.DoesNotExist:
            return None

        if self.user.pk not in (
            handshake.sender_id,
            handshake.receiver_id,
        ):
            return None

        return handshake

    @database_sync_to_async
    def create_message(self, body):
        with transaction.atomic():
            try:
                handshake = (
                    Handshake.objects
                    .select_related("sender", "receiver")
                    .get(
                        pk=self.handshake_id,
                        status=Handshake.Status.ACCEPTED,
                    )
                )
            except Handshake.DoesNotExist:
                raise PermissionError(
                    "The handshake is no longer accepted."
                )

            if self.user.pk == handshake.sender_id:
                recipient = handshake.receiver
            elif self.user.pk == handshake.receiver_id:
                recipient = handshake.sender
            else:
                raise PermissionError(
                    "You are not a participant in this handshake."
                )

            message = Message(
                handshake=handshake,
                sender=self.user,
                recipient=recipient,
                body=body,
            )
            message.full_clean()
            message.save()

        return message, recipient

    @database_sync_to_async
    def create_message_notification(self, message, recipient):
        return notify_message(
            sender=message.sender,
            recipient=recipient,
            preview=message.body[:80],
            target=message,
        )

    @database_sync_to_async
    def mark_messages_read(self):
        # Only mark messages belonging to this accepted handshake,
        # addressed to the authenticated user.
        if not Handshake.objects.filter(
            pk=self.handshake_id,
            status=Handshake.Status.ACCEPTED,
        ).filter(
            # The authenticated user must be a participant.
            sender_id=self.user.pk,
        ).exists() and not Handshake.objects.filter(
            pk=self.handshake_id,
            status=Handshake.Status.ACCEPTED,
            receiver_id=self.user.pk,
        ).exists():
            return

        Message.objects.filter(
            handshake_id=self.handshake_id,
            recipient_id=self.user.pk,
            is_read=False,
        ).update(is_read=True)
