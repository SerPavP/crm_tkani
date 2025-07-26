from django import forms
from .models import Deal, DealItem
from clients.models import Client
from fabrics.models import FabricColor, Fabric


class DealForm(forms.ModelForm):
    """Форма для создания/редактирования сделки"""
    
    class Meta:
        model = Deal
        fields = ['client']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'client': 'Клиент',
        }


class DealItemForm(forms.ModelForm):
    """Форма для добавления позиции в сделку"""
    fabric = forms.ModelChoiceField(
        queryset=Fabric.objects.all(),
        empty_label="Выберите ткань",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'fabric_select',
        }),
        label='Ткань'
    )
    
    class Meta:
        model = DealItem
        fields = ['fabric', 'fabric_color', 'width_meters', 'price_per_meter']
        widgets = {
            'fabric_color': forms.Select(attrs={
                'class': 'form-select',
                'id': 'fabric_color_select',
                'disabled': True,
            }),
            'width_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Количество метров'
            }),
            'price_per_meter': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Цена за метр'
            }),
        }
        labels = {
            'fabric_color': 'Цвет',
            'width_meters': 'Количество метров',
            'price_per_meter': 'Цена за метр (₸)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fabric_color'].queryset = FabricColor.objects.none()
        self.fields['fabric_color'].choices = [('', 'Сначала выберите ткань')]
        
        if 'fabric' in self.data:
            try:
                fabric_id = int(self.data.get('fabric'))
                self.fields['fabric_color'].queryset = FabricColor.objects.filter(fabric_id=fabric_id).order_by('color_name')
                self.fields['fabric_color'].widget.attrs.pop('disabled', None)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.fabric_color_id:
            fabric_id = self.instance.fabric_color.fabric_id
            self.fields['fabric'].initial = fabric_id
            self.fields['fabric_color'].queryset = FabricColor.objects.filter(fabric_id=fabric_id).order_by('color_name')
            self.fields['fabric_color'].widget.attrs.pop('disabled', None)

