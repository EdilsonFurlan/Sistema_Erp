from django.db import models
from molds.models import Molde
from inventory.models import Material, Cor

class Produto(models.Model):
    """
    Entidade industrial/comercial. 
    Pode ser uma Referência técnica (pai) ou uma Variante/SKU (filho).
    """
    nome = models.CharField(max_length=200)
    molde = models.ForeignKey(Molde, on_delete=models.PROTECT)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='variantes', help_text="Se preenchido, este produto é uma VARIANTE/SKU.")
    
    eh_padrao = models.BooleanField(default=False, help_text="Indica se é a Referência Padrão do Molde.")
    
    # Atributos de SKU (Preenchidos se for variante ou se SKU for único)
    sku = models.CharField(max_length=50, blank=True, null=True)
    nome_comercial = models.CharField(max_length=200, blank=True, null=True)
    
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Preço base ou preço do SKU")
    
    # Metadata
    data_criacao = models.DateTimeField(auto_now_add=True)

    @property
    def production_blocked(self):
        return self.variantes.exists()

    def __str__(self):
        if self.sku:
            return f"{self.nome} - {self.sku}"
        return self.nome

class ItensMaterial(models.Model):
    """
    Define materiais e insumos para este produto.
    """
    TIPO_CHOICES = [
        ('tecido_padrao', 'Tecido Padrão'),
        ('insumo', 'Insumo / Aviamento'),
    ]
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='itens_material')
    molde_detalhe = models.ForeignKey('molds.MoldeDetalhe', on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cor = models.ForeignKey(Cor, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.FloatField(default=0.0)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='insumo')
    
    def __str__(self):
        detalhe = f" ({self.molde_detalhe.nome_original})" if self.molde_detalhe else ""
        cor_nome = f" - {self.cor.nome}" if self.cor else ""
        return f"{self.produto.nome} - {self.material.nome}{cor_nome}{detalhe}"

class ProdutoInsumo(models.Model):
    """
    Insumos/Aviamentos globais do produto.
    """
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='insumos')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cor = models.ForeignKey(Cor, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.FloatField(default=0.0)
    
    def __str__(self):
        cor_nome = f" - {self.cor.nome}" if self.cor else ""
        return f"{self.produto.nome} - {self.material.nome}{cor_nome}"

class ProdutoConsumo(models.Model):
    """
    Cache de consumo por material/cor.
    """
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='consumos')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cor = models.ForeignKey(Cor, on_delete=models.SET_NULL, null=True, blank=True) 
    consumo_total = models.FloatField(default=0.0)
    
    def __str__(self):
         return f"{self.produto.nome} - {self.material.nome}"

class OrdemServicoTecnica(models.Model):
    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA')
    
    # Produto resultante (opcional no início, preenchido ao final)
    produto_resultante = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='os_origem')

    def __str__(self):
        return f"OS #{self.id} - {self.get_status_display()}"

class OrdemServicoItem(models.Model):
    """
    Linha da OS que vincula um item do Pedido.
    """
    os = models.ForeignKey(OrdemServicoTecnica, on_delete=models.CASCADE, related_name='itens')
    # Evitar import circular usando string 'app.Model'
    pedido_item = models.OneToOneField('sales.PedidoItem', on_delete=models.PROTECT, related_name='os_tecnica', null=True, blank=True)

    def __str__(self):
        return f"Item OS #{self.os.id} -> Item Pedido #{self.pedido_item.id if self.pedido_item else '?'}"
