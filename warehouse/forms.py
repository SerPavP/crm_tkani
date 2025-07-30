from django import forms
from fabrics.models import FabricRoll
from fabrics.models import FabricColor


class CreateBarcodeForm(forms.ModelForm):
    """Форма для создания рулона с штрих-кодом"""

    class Meta:
        model = FabricRoll
        fields = ['fabric_color', 'width_meters']
        widgets = {
            'fabric_color': forms.Select(attrs={
                'class': 'form-select',
            }),
            'width_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Ширина в метрах'
            }),
        }
        labels = {
            'fabric_color': 'Ткань и цвет',
            'width_meters': 'Ширина рулона (м)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Группируем цвета по тканям для удобного отображения
        fabric_colors = FabricColor.objects.select_related('fabric').order_by('fabric__name', 'color_name')
        choices = [('', 'Выберите ткань и цвет')]

        current_fabric = None
        for color in fabric_colors:
            if current_fabric != color.fabric.name:
                if current_fabric is not None:
                    choices.append(('', '---'))
                current_fabric = color.fabric.name

            choice_label = f"{color.fabric.name} - {color.color_name}"
            choices.append((color.id, choice_label))

        self.fields['fabric_color'].choices = choices


class ScanBarcodeForm(forms.Form):
    """Форма для сканирования штрих-кода"""
    barcode = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Отсканируйте или введите штрих-код',
            'autofocus': True,
        }),
        label='Штрих-код'
    )

