from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from posts.models import Post
from users.models import User


class PostNotificationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="test-password",
        )
        self.actor = User.objects.create_user(
            username="actor",
            email="actor@example.com",
            password="test-password",
        )
        self.post = Post.objects.create(author=self.author, content="Hello")
        self.client.force_login(self.actor)

    def test_post_actions_create_one_notification(self):
        cases = (
            ("like_post", {}, Notification.NotificationType.LIKE),
            (
                "comment_post",
                {"content": "Nice post"},
                Notification.NotificationType.COMMENT,
            ),
            ("repost_post", {}, Notification.NotificationType.REPOST),
        )

        for view_name, data, notification_type in cases:
            with self.subTest(action=view_name):
                response = self.client.post(
                    reverse(view_name, args=[self.post.pk]),
                    data,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    Notification.objects.filter(
                        recipient=self.author,
                        actor=self.actor,
                        notification_type=notification_type,
                    ).count(),
                    1,
                )
