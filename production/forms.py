from django import forms
from .models import Maquina

class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = ['nome', 'setor', 'topico_mqtt']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CNC 01'}),
            'setor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Corte'}),
            'topico_mqtt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'maquina/xxx/status'}),
        }
