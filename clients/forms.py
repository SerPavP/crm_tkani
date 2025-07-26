from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    """Форма для создания/редактирования клиента"""
    
    class Meta:
        model = Client
        fields = ["nickname", "full_name", "phone", "email", "address", "notes"]
        widgets = {
            "nickname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Никнейм / Название компании"
            }),
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Полное имя или ФИО контактного лица"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Номер телефона"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Электронная почта"
            }),
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Адрес"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Дополнительные примечания",
                "rows": 3
            }),
        }
        labels = {
            "nickname": "Никнейм / Компания",
            "full_name": "Полное имя / Контактное лицо",
            "phone": "Телефон",
            "email": "Email",
            "address": "Адрес",
            "notes": "Примечания",
        }

