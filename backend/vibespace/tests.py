import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import VibeCreateForm
from .models import Vibe, VibeComment, VibeLike, VibeTag


class VibeSpaceTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.addCleanup(self.media_directory.cleanup)

        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="test-password",
        )
        self.other_user = user_model.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="test-password",
        )

    def create_vibe(self, **kwargs):
        defaults = {
            "author": self.author,
            "media": SimpleUploadedFile(
                "vibe.jpg",
                b"test image",
                content_type="image/jpeg",
            ),
            "caption": "A campus moment",
            "description": "A test Vibe description.",
        }
        defaults.update(kwargs)
        return Vibe.objects.create(**defaults)

    def test_explore_shows_public_vibes_and_tag_filter(self):
        public_vibe = self.create_vibe()
        private_vibe = self.create_vibe(
            media=SimpleUploadedFile(
                "private.jpg", b"private image", content_type="image/jpeg"
            ),
            is_public=False,
        )
        tag = VibeTag.objects.create(name="Campus", slug="campus")
        public_vibe.tags.add(tag)
        private_vibe.tags.add(tag)

        response = self.client.get(
            reverse("vibespace:explore"),
            {"tag": tag.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A campus moment")
        self.assertEqual(
            [vibe.pk for vibe in response.context["vibes"]],
            [public_vibe.pk],
        )

    def test_private_vibe_is_only_visible_to_its_author(self):
        vibe = self.create_vibe(is_public=False)

        self.assertEqual(
            self.client.get(
                reverse("vibespace:detail", args=[vibe.pk])
            ).status_code,
            404,
        )

        self.client.force_login(self.other_user)
        self.assertEqual(
            self.client.get(
                reverse("vibespace:detail", args=[vibe.pk])
            ).status_code,
            404,
        )

        self.client.force_login(self.author)
        self.assertEqual(
            self.client.get(
                reverse("vibespace:detail", args=[vibe.pk])
            ).status_code,
            200,
        )

    def test_detail_and_my_vibes_render_like_and_comment_counts(self):
        vibe = self.create_vibe()
        VibeLike.objects.create(vibe=vibe, user=self.other_user)
        VibeComment.objects.create(
            vibe=vibe,
            user=self.other_user,
            text="Great!",
        )
        self.client.force_login(self.author)

        detail_response = self.client.get(
            reverse("vibespace:detail", args=[vibe.pk])
        )
        collection_response = self.client.get(reverse("vibespace:my_vibes"))

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.context["vibe"].like_count, 1)
        self.assertEqual(detail_response.context["vibe"].comment_count, 1)
        self.assertEqual(collection_response.status_code, 200)
        self.assertEqual(collection_response.context["vibes"][0].like_count, 1)
        self.assertEqual(collection_response.context["vibes"][0].comment_count, 1)

    def test_create_form_requires_description_and_rejects_overlong_tags(self):
        form_data = {
            "caption": "Test",
            "description": "",
            "tag_names": "x" * 41,
            "target_audience": Vibe.TargetAudience.EVERYONE,
            "is_campus_event": "",
            "campus_event_name": "",
            "is_public": "on",
        }
        upload = SimpleUploadedFile(
            "vibe.jpg", b"test image", content_type="image/jpeg"
        )

        form = VibeCreateForm(form_data, {"media": upload})

        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("tag_names", form.errors)
        self.assertEqual(Vibe.objects.count(), 0)

    def test_create_and_edit_pages_render_existing_form_data(self):
        self.client.force_login(self.author)
        vibe = self.create_vibe()
        tag = VibeTag.objects.create(name="Campus", slug="campus")
        vibe.tags.add(tag)

        create_response = self.client.get(reverse("vibespace:create"))
        edit_response = self.client.get(
            reverse("vibespace:edit", args=[vibe.pk])
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "Share your vibe")
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, "Edit your vibe")
        self.assertContains(edit_response, "value=\"Campus\"")
        self.assertContains(edit_response, vibe.media.url)

    def test_create_and_edit_flow_saves_tags_and_visibility(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("vibespace:create"),
            {
                "caption": "First Vibe",
                "description": "A description.",
                "tag_names": "coding, #Hackathon",
                "target_audience": Vibe.TargetAudience.EVERYONE,
                "is_campus_event": "",
                "campus_event_name": "",
                "is_public": "on",
                "media": SimpleUploadedFile(
                    "vibe.jpg", b"test image", content_type="image/jpeg"
                ),
            },
        )

        vibe = Vibe.objects.get()
        self.assertRedirects(
            response,
            reverse("vibespace:detail", args=[vibe.pk]),
        )
        self.assertTrue(vibe.is_public)
        self.assertSetEqual(
            set(vibe.tags.values_list("slug", flat=True)),
            {"coding", "hackathon"},
        )

        edit_response = self.client.post(
            reverse("vibespace:edit", args=[vibe.pk]),
            {
                "caption": "Updated Vibe",
                "description": "Updated description.",
                "tag_names": "design",
                "target_audience": Vibe.TargetAudience.DESIGNERS,
                "is_campus_event": "",
                "campus_event_name": "",
            },
        )

        vibe.refresh_from_db()
        self.assertRedirects(
            edit_response,
            reverse("vibespace:detail", args=[vibe.pk]),
        )
        self.assertEqual(vibe.caption, "Updated Vibe")
        self.assertFalse(vibe.is_public)
        self.assertSetEqual(
            set(vibe.tags.values_list("slug", flat=True)),
            {"design"},
        )

    def test_like_and_comment_actions_update_public_vibe(self):
        vibe = self.create_vibe()
        self.client.force_login(self.other_user)
        like_url = reverse("vibespace:like", args=[vibe.pk])
        comment_url = reverse("vibespace:comment", args=[vibe.pk])

        self.client.post(like_url)
        self.assertTrue(
            VibeLike.objects.filter(vibe=vibe, user=self.other_user).exists()
        )
        self.client.post(like_url)
        self.assertFalse(
            VibeLike.objects.filter(vibe=vibe, user=self.other_user).exists()
        )

        self.client.post(comment_url, {"text": "   "})
        self.assertFalse(VibeComment.objects.filter(vibe=vibe).exists())
        self.client.post(comment_url, {"text": "Nice!"})
        self.assertEqual(
            VibeComment.objects.filter(vibe=vibe).values_list(
                "text", flat=True
            ).get(),
            "Nice!",
        )

    def test_only_author_can_edit_or_delete_vibes(self):
        vibe = self.create_vibe()
        self.client.force_login(self.other_user)

        self.assertEqual(
            self.client.get(
                reverse("vibespace:edit", args=[vibe.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("vibespace:delete", args=[vibe.pk])
            ).status_code,
            404,
        )
        self.assertTrue(Vibe.objects.filter(pk=vibe.pk).exists())

    def test_delete_requires_confirmation_and_post(self):
        vibe = self.create_vibe()
        self.client.force_login(self.author)
        delete_url = reverse("vibespace:delete", args=[vibe.pk])

        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.assertTrue(Vibe.objects.filter(pk=vibe.pk).exists())

        response = self.client.post(delete_url)

        self.assertRedirects(response, reverse("vibespace:my_vibes"))
        self.assertFalse(Vibe.objects.filter(pk=vibe.pk).exists())
