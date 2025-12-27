from django import forms
from django.forms import inlineformset_factory
from .models import Pedido, PedidoItem
from products.models import Produto

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'cliente_cadastro']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Cliente (Avulso)'}),
            'cliente_cadastro': forms.Select(attrs={'class': 'form-control'}),
        }

class PedidoItemForm(forms.ModelForm):
    class Meta:
        model = PedidoItem
        fields = ['produto', 'quantidade', 'preco_unitario']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control item-product-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control item-qty', 'min': '1'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control item-price', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Improve label for product
        self.fields['produto'].queryset = Produto.objects.filter(parent__isnull=False).select_related('parent').all()
        self.fields['produto'].label_from_instance = lambda obj: obj.nome_comercial if obj.nome_comercial else f"{obj.parent.nome} ({obj.sku or 'S/ SKU'})"

PedidoItemFormSet = inlineformset_factory(
    Pedido, 
    PedidoItem, 
    form=PedidoItemForm,
    extra=1,
    can_delete=True,
    widgets={
        'DELETE': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)
