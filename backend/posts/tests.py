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

    def test_feed_shows_public_vibes_but_not_regular_posts(self):
        older_vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/older.jpg",
            caption="An older Vibe",
        )
        public_vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/public.jpg",
            caption="A public Vibe",
            description="A Vibe now visible in the main feed.",
        )
        newer_vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/newer.jpg",
            caption="The newest Vibe",
        )
        Post.objects.create(
            author=self.user,
            content="A regular post excluded from the feed",
        )
        Vibe.objects.create(
            author=self.user,
            media="vibes/private.jpg",
            caption="A private Vibe",
            is_public=False,
        )

        now = timezone.now()
        Vibe.objects.filter(pk=older_vibe.pk).update(
            created_at=now - timedelta(days=3)
        )
        Vibe.objects.filter(pk=public_vibe.pk).update(
            created_at=now - timedelta(days=2)
        )
        Vibe.objects.filter(pk=newer_vibe.pk).update(
            created_at=now - timedelta(days=1)
        )

        response = self.client.get(reverse("community_feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The newest Vibe")
        self.assertContains(response, "A public Vibe")
        self.assertContains(response, "A Vibe now visible in the main feed.")
        self.assertNotContains(response, "A private Vibe")
        self.assertNotContains(response, "A regular post excluded from the feed")
        self.assertEqual(
            [
                (item["type"], item["object"].pk)
                for item in response.context["feed_items"]
            ],
            [
                ("vibe", newer_vibe.pk),
                ("vibe", public_vibe.pk),
                ("vibe", older_vibe.pk),
            ],
        )

    def test_feed_displays_vibes_when_there_are_no_posts(self):
        Vibe.objects.create(
            author=self.user,
            media="vibes/only.jpg",
            caption="Only a Vibe",
        )

        response = self.client.get(reverse("community_feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only a Vibe")
        self.assertNotContains(response, "Your community starts here.")

    def test_home_feed_shows_profile_stats_without_post_composer(self):
        follower = get_user_model().objects.create_user(
            username="follower",
            email="follower@example.com",
            password="test-password",
        )
        following = get_user_model().objects.create_user(
            username="following",
            email="following@example.com",
            password="test-password",
        )
        Follow.objects.create(follower=follower, following=self.user)
        Follow.objects.create(follower=self.user, following=following)
        Post.objects.create(author=self.user, content="Profile post")
        Vibe.objects.create(
            author=self.user,
            media="vibes/home-hidden.jpg",
            caption="A Vibe not shown on Home",
        )

        response = self.client.get(reverse("feed"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Share a text update with the BxB community")
        self.assertNotContains(response, "Share text update")
        self.assertNotContains(response, "A Vibe not shown on Home")
        self.assertContains(response, "Welcome to BxB")
        self.assertContains(response, "Your Profile")
        self.assertContains(response, "Explore the community feed")
        self.assertEqual(
            response.context["profile_stats"],
            {"posts": 1, "followers": 1, "following": 1},
        )

    def test_home_feed_rejects_post_requests_without_creating_vibes(self):
        response = self.client.post(
            reverse("feed"),
            {
                "content_type": "vibe",
                "description": "A text-only home feed update",
                "target_audience": "everyone",
                "is_public": "true",
            },
        )

        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            Vibe.objects.filter(
                description="A text-only home feed update"
            ).exists()
        )

    def test_feed_renders_open_vibe_and_revibe_controls_for_text_updates(self):
        vibe = Vibe.objects.create(
            author=self.user,
            description="A text-only Vibe",
        )

        response = self.client.get(reverse("community_feed"))

        self.assertContains(response, "Open Vibe")
        self.assertContains(
            response,
            reverse("vibespace:detail", args=[vibe.pk]),
        )
        self.assertContains(response, "Revibe")
        self.assertContains(
            response,
            reverse("vibespace:revibe", args=[vibe.pk]),
        )

    def test_open_vibe_displays_text_update_details(self):
        vibe = Vibe.objects.create(
            author=self.user,
            description="The full text of this Vibe",
        )

        response = self.client.get(
            reverse("vibespace:detail", args=[vibe.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The full text of this Vibe")
        self.assertContains(response, "Text update")

    def test_post_revibe_toggles_and_returns_count_for_feed(self):
        post = Post.objects.create(
            author=self.user,
            content="Revibable text post",
        )
        revibe_url = reverse("repost_post", args=[post.pk])
        ajax_headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

        first_response = self.client.post(revibe_url, **ajax_headers)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            first_response.json(),
            {"success": True, "is_reposted": True, "repost_count": 1},
        )

        second_response = self.client.post(revibe_url, **ajax_headers)

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            second_response.json(),
            {"success": True, "is_reposted": False, "repost_count": 0},
        )

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

        response = self.client.get(reverse("community_feed"))

        self.assertContains(
            response,
            reverse("vibespace:follow", args=[vibe.pk]),
        )
        self.assertContains(response, "+ Follow")

        Follow.objects.create(follower=self.user, following=creator)
        response = self.client.get(reverse("community_feed"))

        self.assertContains(response, "Following")
        self.assertIn(creator.pk, response.context["following_creator_ids"])

    def test_feed_renders_inline_vibe_like_and_comment_controls(self):
        vibe = Vibe.objects.create(
            author=self.user,
            media="vibes/interactive.jpg",
            caption="Interactive Vibe",
        )

        response = self.client.get(reverse("community_feed"))

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

        response = self.client.get(reverse("community_feed"))

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
