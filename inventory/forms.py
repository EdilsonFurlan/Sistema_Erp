from django import forms
from .models import Material, EntradaEstoque, Cor

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'unidade', 'preco_custo', 'eh_tecido', 'largura_padrao_mm', 'tem_cor']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: mt, kg, un'}),
            'preco_custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largura_padrao_mm': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'eh_tecido': 'Marque se for tecido (permite cálculo de encaixe)',
            'tem_cor': 'Marque se este item varia de cor (ex: Zíper, Linha)',
        }

class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque
        fields = ['material', 'cor', 'quantidade', 'preco_unitario', 'fornecedor']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control'}),
            'cor': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Quantidade na Unidade de Compra (ex: Metros)'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Preço Pago por Unidade'}),
            'fornecedor': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CorForm(forms.ModelForm):
    class Meta:
        model = Cor
        fields = ['nome', 'hex_code']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Azul Marinho'}),
            'hex_code': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
        labels = {
            'hex_code': 'Cor para Visualização'
        }

class AddColorToMaterialForm(forms.Form):
    cor = forms.ModelChoiceField(
        queryset=Cor.objects.all().order_by('nome'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Escolha a Cor"
    )
