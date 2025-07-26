from django import forms
from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    """Форма для редактирования системных настроек"""

    class Meta:
        model = SystemSettings
        fields = ["vat_rate", "markup_percentage"]
        widgets = {
            "vat_rate": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.00",
                "placeholder": "Ставка НДС в процентах"
            }),
            "markup_percentage": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.00",
                "placeholder": "Автоматическая наценка в процентах"
            }),
        }
        labels = {
            "vat_rate": "Ставка НДС (%)",
            "markup_percentage": "Автоматическая наценка (%)",
        }


