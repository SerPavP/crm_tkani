from django import forms
from .models import Fabric, FabricColor


class FabricForm(forms.ModelForm):
    """Форма для создания/редактирования ткани"""
    
    class Meta:
        model = Fabric
        fields = ['name', 'cost_price', 'selling_price']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название ткани'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Себестоимость в тенге',
                'step': '0.01',
                'min': '0'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Цена продажи (рассчитается автоматически)',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'name': 'Название ткани',
            'cost_price': 'Себестоимость (₸)',
            'selling_price': 'Цена продажи (₸)',
        }


class FabricColorForm(forms.ModelForm):
    """Форма для создания/редактирования цвета ткани"""
    
    class Meta:
        model = FabricColor
        fields = ['color_name']
        widgets = {
            'color_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название цвета (например, желтый)'
            }),
        }
        labels = {
            'color_name': 'Название цвета',
        }

