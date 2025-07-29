from django import forms
from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    """Форма для редактирования системных настроек"""

    class Meta:
        model = SystemSettings
        fields = ["markup_percentage"]
        widgets = {
            "markup_percentage": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.00",
                "placeholder": "Автоматическая наценка в процентах"
            }),
        }
        labels = {
            "markup_percentage": "Автоматическая наценка (%)",
        }


