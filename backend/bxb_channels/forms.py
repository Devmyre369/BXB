from django import forms

from .models import Channel


class ChannelCreateForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = [
            "name",
            "description",
            "category",
            "college",
            "is_public",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. BxB Developers Club",
                "maxlength": 100,
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "What is this Channel about?",
                "rows": 4,
            }),
            "category": forms.Select(attrs={
                "class": "form-control",
            }),
            "college": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "College or university (optional)",
            }),
            "is_public": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "Channel name cannot be empty."
            )

        return name