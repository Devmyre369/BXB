
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
                        "image/gif"
                    ),
                    "class": "vibe-file-input",
                }
            ),
            "caption": forms.TextInput(
                attrs={
                    "placeholder": "Write a caption for your Vibe...",
                    "maxlength": 500,
                    "class": "vibe-caption-input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Share your thoughts, a story, or context for your Vibe..."
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

        self.fields["media"].required = True
        self.fields["description"].required = True

        if not self.instance.pk:
            pass
        elif "tag_names" not in self.initial:
            self.initial["tag_names"] = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_media(self):
        media = self.cleaned_data.get("media")
        if not media and not self.instance.pk:
            raise forms.ValidationError("Upload an image or GIF for your Vibe.")
        if not media and self.instance.pk and self.instance.media:
            return self.instance.media
        return media

    def clean_caption(self):
        return self.cleaned_data.get("caption", "").strip()

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()

        if not description:
            raise forms.ValidationError(
                "Add a description for your Vibe."
            )

        return description

    def clean_tag_names(self):
        raw_tags = self.cleaned_data.get("tag_names", "")

        for raw_tag in raw_tags.split(","):
            name = raw_tag.strip().lstrip("#").strip()

            if name and len(name) > 40:
                raise forms.ValidationError(
                    f"Tag '{name[:40]}â€¦' is too long. "
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

        has_media = bool(media) or bool(self.instance.pk and self.instance.media)
        has_text = bool(description.strip() or caption.strip())

        if not has_media or not has_text:
            raise forms.ValidationError(
                "Upload an image or GIF and add text to create a Vibe."
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
