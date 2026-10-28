
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Message(models.Model):
    """A private message exchanged by users with an accepted handshake."""

    handshake = models.ForeignKey(
        "handshake.Handshake",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="direct_messages_sent",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="direct_messages_received",
    )
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["handshake", "created_at"],
                name="msg_handshake_time_idx",
            ),
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="msg_recipient_read_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.handshake_id or not self.sender_id or not self.recipient_id:
            return

        if self.sender_id == self.recipient_id:
            raise ValidationError("You cannot message yourself.")

        participants = {
            self.handshake.sender_id,
            self.handshake.receiver_id,
        }

        if (
            self.sender_id not in participants
            or self.recipient_id not in participants
        ):
            raise ValidationError(
                "Both users must belong to this handshake."
            )

        if self.handshake.status != "accepted":
            raise ValidationError(
                "Messaging requires an accepted handshake."
            )

    def __str__(self):
        return f"Message #{self.pk}: {self.sender} → {self.recipient}"
