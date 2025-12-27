from django import forms
from molds.models import Molde

class MoldeUploadForm(forms.ModelForm):
    class Meta:
        model = Molde
        fields = ['nome', 'arquivo_json']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Molde (opcional - usa nome do arquivo se vazio)'}),
            'arquivo_json': forms.FileInput(attrs={'class': 'form-control', 'accept': '.mld, .json'})
        }
        labels = {
            'arquivo_json': 'Arquivo de Molde (.mld, .json)'
        }
