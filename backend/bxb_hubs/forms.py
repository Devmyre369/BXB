
from django import forms

from .models import Hub


class HubCreateForm(forms.ModelForm):
    class Meta:
        model = Hub
        fields = [
            "name",
            "description",
            "category",
            "institution",
            "is_public",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your Hub name",
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "What is this Hub about?",
                    "rows": 4,
                    "class": "form-control",
                }
            ),
            "category": forms.Select(
                attrs={"class": "form-control"}
            ),
            "institution": forms.TextInput(
                attrs={
                    "placeholder": "College, organization, or institution (optional)",
                    "class": "form-control",
                }
            ),
            "is_public": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
