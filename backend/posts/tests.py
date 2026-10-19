from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from profiles.models import Follow
from vibespace.models import Vibe, VibeComment, VibeLike, VibeRepost

from .models import Post


class MainFeedTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="feeduser",
            email="feeduser@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_feed_merges_public_vibes_and_posts_by_creation_time(self):
        older_post = Post.objects.create(
            author=self.user,
            content="An older post",
        )
        public_vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/public.jpg",
            caption="A public Vibe",
            description="A Vibe now visible in the main feed.",
        )
        newer_post = Post.objects.create(
            author=self.user,
            content="The newest post",
        )
        Vibe.objects.create(
            author=self.user,
            media="vibes/private.jpg",
            caption="A private Vibe",
            is_public=False,
        )

        now = timezone.now()
        Post.objects.filter(pk=older_post.pk).update(
            created_at=now - timedelta(days=3)
        )
        Vibe.objects.filter(pk=public_vibe.pk).update(
            created_at=now - timedelta(days=2)
        )
        Post.objects.filter(pk=newer_post.pk).update(
            created_at=now - timedelta(days=1)
        )

        response = self.client.get(reverse("feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The newest post")
        self.assertContains(response, "A public Vibe")
        self.assertContains(response, "A Vibe now visible in the main feed.")
        self.assertNotContains(response, "A private Vibe")
        self.assertEqual(
            [
                (item["type"], item["object"].pk)
                for item in response.context["feed_items"]
            ],
            [
                ("post", newer_post.pk),
                ("vibe", public_vibe.pk),
                ("post", older_post.pk),
            ],
        )

    def test_feed_displays_vibes_when_there_are_no_posts(self):
        Vibe.objects.create(
            author=self.user,
            media="vibes/only.jpg",
            caption="Only a Vibe",
        )

        response = self.client.get(reverse("feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only a Vibe")
        self.assertNotContains(response, "Your community starts here.")

    def test_feed_renders_follow_control_for_vibe_creators(self):
        creator = get_user_model().objects.create_user(
            username="vibecreator",
            email="vibecreator@example.com",
            password="test-password",
        )
        vibe = Vibe.objects.create(
            author=creator,
            media="vibes/creator.jpg",
            caption="Follow this creator",
        )

        response = self.client.get(reverse("feed"))

        self.assertContains(
            response,
            reverse("vibespace:follow", args=[vibe.pk]),
        )
        self.assertContains(response, "+ Follow")

        Follow.objects.create(follower=self.user, following=creator)
        response = self.client.get(reverse("feed"))

        self.assertContains(response, "Following")
        self.assertIn(creator.pk, response.context["following_creator_ids"])

    def test_feed_renders_inline_vibe_like_and_comment_controls(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/interactive.jpg",
            caption="Interactive Vibe",
        )

        response = self.client.get(reverse("feed"))

        self.assertContains(
            response,
            reverse("vibespace:like", args=[vibe.pk]),
        )
        self.assertContains(
            response,
            reverse("vibespace:comment", args=[vibe.pk]),
        )
        self.assertContains(response, f'id="vibe-comments-{vibe.pk}"')

    def test_feed_renders_revibe_control_and_count(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/revibe.jpg",
            caption="Revibable Vibe",
        )
        VibeRepost.objects.create(vibe=vibe, user=self.user)

        response = self.client.get(reverse("feed"))

        self.assertContains(response, "Revibe")
        self.assertContains(
            response,
            reverse("vibespace:revibe", args=[vibe.pk]),
        )
        self.assertContains(response, 'data-count="vibe-repost">1</span>')
        self.assertContains(response, 'aria-pressed="true"')

    def test_vibe_revibe_toggles_and_returns_count_for_feed(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/revibe.jpg",
            caption="Revibable Vibe",
        )
        revibe_url = reverse("vibespace:revibe", args=[vibe.pk])

        first_response = self.client.post(
            revibe_url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            first_response.json(),
            {"success": True, "is_reposted": True, "repost_count": 1},
        )
        self.assertTrue(
            VibeRepost.objects.filter(vibe=vibe, user=self.user).exists()
        )

        second_response = self.client.post(
            revibe_url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            second_response.json(),
            {"success": True, "is_reposted": False, "repost_count": 0},
        )
        self.assertFalse(
            VibeRepost.objects.filter(vibe=vibe, user=self.user).exists()
        )

    def test_vibe_like_and_comment_return_json_for_feed_requests(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/interactive.jpg",
            caption="Interactive Vibe",
        )
        ajax_headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

        like_response = self.client.post(
            reverse("vibespace:like", args=[vibe.pk]),
            **ajax_headers,
        )

        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(
            like_response.json(),
            {"success": True, "is_liked": True, "like_count": 1},
        )
        self.assertTrue(
            VibeLike.objects.filter(vibe=vibe, user=self.user).exists()
        )

        comment_response = self.client.post(
            reverse("vibespace:comment", args=[vibe.pk]),
            {"text": "Looks great!"},
            **ajax_headers,
        )

        self.assertEqual(comment_response.status_code, 200)
        self.assertEqual(comment_response.json()["comment_count"], 1)
        self.assertEqual(
            comment_response.json()["comment"]["text"],
            "Looks great!",
        )
        self.assertEqual(VibeComment.objects.filter(vibe=vibe).count(), 1)

    def test_ajax_vibe_comment_reports_validation_errors(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/interactive.jpg",
            caption="Interactive Vibe",
        )

        response = self.client.post(
            reverse("vibespace:comment", args=[vibe.pk]),
            {"text": " "},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(VibeComment.objects.filter(vibe=vibe).count(), 0)
