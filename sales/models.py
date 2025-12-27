from django.db import models
from molds.models import Molde, MoldeDetalhe
from inventory.models import Material, Cor
from products.models import Produto
from clients.models import Cliente

class Pedido(models.Model):
    cliente = models.CharField(max_length=200)
    cliente_cadastro = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    data = models.DateTimeField(auto_now_add=True)
    data_entrega = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente}"
    
    # Financial fields
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    @property
    def status_info(self):
        items = list(self.itens.all())
        total_items = len(items)
        if total_items == 0:
            return {
                'display': "Vazio",
                'color': "#bdc3c7", # Grey
                'pending_msg': ""
            }
            
        # Count statuses
        liberados = sum(1 for i in items if i.status in ['LIBERADO_PRODUCAO', 'EM_PRODUCAO', 'CONCLUIDO'])
        
        if liberados == total_items:
            return {
                'display': "LIBERADO PRODUÇÃO",
                'color': "#27ae60", # Green
                'pending_msg': ""
            }
        elif liberados == 0:
            return {
                'display': "PENDENTE TÉCNICO",
                'color': "#f39c12", # Orange/Yellow
                'pending_msg': f"{total_items} itens pendentes"
            }
        else:
            pendentes = total_items - liberados
            return {
                'display': "PARCIAL",
                'color': "#3498db", # Blue
                'pending_msg': f"{pendentes} de {total_items} itens pendentes"
            }

    @property
    def status_display(self):
        return self.status_info['display']

    @property
    def status_color(self):
        return self.status_info['color']

    @property
    def pending_msg(self):
        return self.status_info['pending_msg']

class PedidoItem(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE_CADASTRO', 'Pendente Cadastro Técnico'),
        ('LIBERADO_PRODUCAO', 'Liberado para Produção'),
        ('EM_PRODUCAO', 'Em Produção'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    molde = models.ForeignKey(Molde, on_delete=models.PROTECT, null=True, blank=True)
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, help_text="SKU selecionado")
    quantidade = models.IntegerField(default=1)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDENTE_CADASTRO')

    # Financial fields
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        if self.preco_unitario and self.quantidade:
            self.subtotal = self.preco_unitario * self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        molde_nome = self.molde.nome if self.molde else "(Sem Molde)"
        produto_nome = self.produto.nome if self.produto else "(Sem Produto)"
        return f"{self.quantidade}x {molde_nome or produto_nome}"

class PedidoConfig(models.Model):
    """
    Configuração de qual tecido/cor usar para cada peça do molde neste pedido.
    """
    pedido_item = models.ForeignKey(PedidoItem, on_delete=models.CASCADE, related_name='configuracoes')
    molde_peca = models.ForeignKey(MoldeDetalhe, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT, null=True, blank=True)
    cor = models.ForeignKey(Cor, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('pedido_item', 'molde_peca')

    def __str__(self):
        mat_nome = self.material.nome if self.material else "N/A"
        return f"{self.molde_peca.nome_original} -> {mat_nome} {self.cor.nome}"
