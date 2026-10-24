
from django import forms
from django.utils.text import slugify

from .models import Vibe, VibeTag


class VibeCreateForm(forms.ModelForm):
    tag_names = forms.CharField(
        required=False,
        max_length=300,
        label="Tags",
        help_text=(
            "Separate tags with commas, e.g. coding, hackathon, collegefest."
        ),
        widget=forms.TextInput(
            attrs={
                "placeholder": "coding, hackathon, collegefest",
                "class": "vibe-caption-input",
            }
        ),
    )

    class Meta:
        model = Vibe
        fields = [
            "media",
            "caption",
            "description",
            "is_campus_event",
            "campus_event_name",
            "target_audience",
            "is_public",
        ]
        widgets = {
            "media": forms.ClearableFileInput(
                attrs={
                    "accept": (
                        "image/jpeg,image/png,image/webp,"
                        "image/gif,video/mp4,video/webm,"
                        "video/quicktime"
                    ),
                    "class": "vibe-file-input",
                }
            ),
            "caption": forms.TextInput(
                attrs={
                    "placeholder": "Give your Vibe a short caption",
                    "maxlength": 500,
                    "class": "vibe-caption-input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "What's on your mind?",
                    "rows": 4,
                    "maxlength": 1500,
                    "class": "vibe-caption-input",
                }
            ),
            "is_campus_event": forms.CheckboxInput(
                attrs={"class": "vibe-checkbox"}
            ),
            "campus_event_name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Annual College Fest",
                    "maxlength": 200,
                    "class": "vibe-caption-input",
                }
            ),
            "target_audience": forms.Select(
                attrs={"class": "vibe-caption-input"}
            ),
            "is_public": forms.CheckboxInput(
                attrs={"class": "vibe-checkbox"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Media is optional: users can publish text-only Vibes.
        self.fields["media"].required = False

        # Populate existing tags when editing a Vibe.
        if self.instance.pk:
            if "tag_names" not in self.initial:
                self.initial["tag_names"] = ", ".join(
                    self.instance.tags.values_list("name", flat=True)
                )

    def clean_media(self):
        # A missing upload is valid. On edits, Django can retain
        # the existing file when no replacement is uploaded.
        return self.cleaned_data.get("media")

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        media = self.cleaned_data.get("media")
        caption = self.cleaned_data.get("caption", "").strip()

        # Require content, but allow text-only or media-only Vibes.
        if not media and not description and not caption:
            raise forms.ValidationError(
                "Write something or upload an image, GIF, or video."
            )

        return description

    def clean_tag_names(self):
        raw_tags = self.cleaned_data.get("tag_names", "")

        for raw_tag in raw_tags.split(","):
            name = raw_tag.strip().lstrip("#").strip()

            if name and len(name) > 40:
                raise forms.ValidationError(
                    f"Tag '{name[:40]}…' is too long. "
                    "Each tag must be at most 40 characters."
                )

        return raw_tags

    def clean(self):
        cleaned_data = super().clean()

        is_campus_event = cleaned_data.get("is_campus_event")
        campus_event_name = cleaned_data.get("campus_event_name", "")

        if not is_campus_event:
            cleaned_data["campus_event_name"] = ""
        elif not campus_event_name.strip():
            self.add_error(
                "campus_event_name",
                "Enter the campus event name.",
            )

        return cleaned_data

    def save(self, commit=True):
        vibe = super().save(commit=commit)

        if commit:
            self.save_tags(vibe)

        return vibe

    def save_tags(self, vibe):
        tags = []
        seen = set()

        for raw_tag in self.cleaned_data.get("tag_names", "").split(","):
            name = raw_tag.strip().lstrip("#").strip()
            slug = slugify(name)

            if not name or not slug or slug in seen:
                continue

            seen.add(slug)

            tag, _ = VibeTag.objects.get_or_create(
                slug=slug,
                defaults={"name": name.lower()},
            )
            tags.append(tag)

        vibe.tags.set(tags)
