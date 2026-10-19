from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vibespace.models import Vibe, VibeTag


class VibeSearchTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="vibecreator",
            email="creator@example.com",
            password="test-password",
        )

    def create_vibe(self, **kwargs):
        defaults = {
            "author": self.user,
            "media": "vibes/searchable.jpg",
            "caption": "Campus robotics night",
            "description": "Building something together.",
        }
        defaults.update(kwargs)
        return Vibe.objects.create(**defaults)

    def test_search_results_include_public_vibes_matching_content_and_tags(self):
        vibe = self.create_vibe()
        private_vibe = self.create_vibe(
            media="vibes/private-searchable.jpg",
            caption="Private robotics moment",
            is_public=False,
        )
        tag = VibeTag.objects.create(name="Robotics", slug="robotics")
        vibe.tags.add(tag)
        private_vibe.tags.add(tag)

        response = self.client.get(reverse("search"), {"q": "robotics"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campus robotics night")
        self.assertContains(response, reverse("vibespace:detail", args=[vibe.pk]))
        self.assertNotContains(response, "Private robotics moment")
        self.assertEqual(
            list(response.context["vibes"].values_list("pk", flat=True)),
            [vibe.pk],
        )

    def test_vibes_search_filter_only_returns_vibes(self):
        vibe = self.create_vibe()
        self.create_vibe(
            author=self.user,
            media="vibes/other.jpg",
            caption="Sculpture in studio",
        )

        response = self.client.get(
            reverse("search"),
            {"q": "campus", "type": "vibes"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_type"], "vibes")
        self.assertEqual(
            list(response.context["vibes"].values_list("pk", flat=True)),
            [vibe.pk],
        )
        self.assertContains(response, "Vibes")

    def test_search_suggestions_include_public_vibes_and_direct_link(self):
        vibe = self.create_vibe(
            caption="Robotics showcase",
            description="Prototype demonstrations.",
        )
        self.create_vibe(
            media="vibes/private-robotics.jpg",
            caption="Robotics private draft",
            is_public=False,
        )

        response = self.client.get(
            reverse("search_suggestions"),
            {"q": "robotics"},
        )

        self.assertEqual(response.status_code, 200)
        vibe_suggestions = [
            item for item in response.json()["results"]
            if item["type"] == "vibe"
        ]
        self.assertEqual(len(vibe_suggestions), 1)
        self.assertEqual(vibe_suggestions[0]["title"], "Robotics showcase")
        self.assertEqual(
            vibe_suggestions[0]["url"],
            reverse("vibespace:detail", args=[vibe.pk]),
        )
