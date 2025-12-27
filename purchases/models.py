from django.db import models
from sales.models import Pedido
from inventory.models import Material, Cor

class OrdemCompra(models.Model):
    """
    Agrupamento de pedidos para compra unificada de materiais.
    """
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('enviada', 'Enviada ao Fornecedor'),
        ('recebida', 'Recebida'),
        ('cancelada', 'Cancelada'),
    ]

    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')
    pedidos = models.ManyToManyField(Pedido, related_name='ordens_compra', blank=True, help_text="Pedidos contemplados nesta ordem de compra")

    def __str__(self):
        return f"OC #{self.id} - {self.get_status_display()} ({self.data_criacao.strftime('%d/%m/%Y')})"

class OrdemCompraItem(models.Model):
    """
    Item individual da ordem de compra (ex: 50m de Tecido X Preto).
    """
    ordem_compra = models.ForeignKey(OrdemCompra, on_delete=models.CASCADE, related_name='itens')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cor = models.ForeignKey(Cor, on_delete=models.PROTECT, null=True, blank=True)
    
    quantidade_necessaria = models.FloatField(default=0.0, help_text="Soma da necessidade real dos pedidos")
    quantidade_estoque_na_epoca = models.FloatField(default=0.0, help_text="Quanto havia em estoque no momento da geração")
    quantidade_comprar = models.FloatField(default=0.0, help_text="Quantidade sugerida para compra (Necessária - Estoque)")

    def __str__(self):
        cor_name = self.cor.nome if self.cor else "S/ Cor"
        return f"{self.material.nome} ({cor_name}): {self.quantidade_comprar} {self.material.unidade}"
