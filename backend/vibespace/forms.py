
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
                        "video/quicktime,video/x-m4v"
                    ),
                    "class": "vibe-file-input",
                }
            ),
            "caption": forms.TextInput(
                attrs={
                    "placeholder": "Write a caption or a text Vibe...",
                    "maxlength": 500,
                    "class": "vibe-caption-input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Share your thoughts, a story, a meme caption, "
                        "or the context behind your media..."
                    ),
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

        # Media is optional for new text-only Vibes.
        self.fields["media"].required = False

        if not self.instance.pk:
            self.fields["description"].required = False
        elif "tag_names" not in self.initial:
            self.initial["tag_names"] = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_media(self):
        media = self.cleaned_data.get("media")

        # Existing media can be retained when editing.
        if not media and not self.instance.pk:
            return None

        return media

    def clean_caption(self):
        return self.cleaned_data.get("caption", "").strip()

    def clean_description(self):
        return self.cleaned_data.get("description", "").strip()

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

        media = cleaned_data.get("media")
        caption = cleaned_data.get("caption", "")
        description = cleaned_data.get("description", "")
        is_campus_event = cleaned_data.get("is_campus_event")
        campus_event_name = cleaned_data.get("campus_event_name", "")

        # A new Vibe must contain media or text.
        # An existing Vibe may retain its already-saved media.
        has_existing_media = bool(
            self.instance.pk and self.instance.media
        )
        has_media = bool(media) or has_existing_media
        has_text = bool(caption or description)

        if not has_media and not has_text:
            raise forms.ValidationError(
                "Write something or upload an image, GIF, or video "
                "before publishing."
            )

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
