from django.db import models
from products.models import Produto

class OrdemProducao(models.Model):
    STATUS_CHOICES = [
        ('PLANEJADA', 'Planejada'),
        ('EM_PRODUCAO', 'Em Produção'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANEJADA')
    
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='ordens_producao')
    quantidade_total = models.IntegerField(default=0)
    
    maquinas = models.ManyToManyField('Maquina', related_name='ops', blank=True, help_text="Máquinas planejadas para esta OP")

    # Metadata
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"OP #{self.id} - {self.produto} ({self.quantidade_total} pçs)"


class OrdemProducaoItem(models.Model):
    """
    Rastreabilidade: Qual item de pedido está sendo atendido nesta OP?
    """
    op = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, related_name='itens_origem')
    pedido_item = models.ForeignKey('sales.PedidoItem', on_delete=models.PROTECT, related_name='producoes')
    
    quantidade = models.IntegerField(default=0, help_text="Quantidade deste item de pedido atendida nesta OP")

    def __str__(self):
        return f"OP #{self.op.id} <- PedidoItem #{self.pedido_item.id}"

class Maquina(models.Model):
    nome = models.CharField(max_length=100)
    setor = models.CharField(max_length=50, blank=True, null=True)
    topico_mqtt = models.CharField(max_length=200, help_text="Tópico MQTT que esta máquina publica (ex: maquina/001/status)")
    
    # Estado Atual
    status_atual = models.CharField(max_length=20, default='DESLIGADO', choices=[('LIGADO', 'Ligado'), ('DESLIGADO', 'Desligado')])
    op_atual = models.ForeignKey(OrdemProducao, on_delete=models.SET_NULL, null=True, blank=True, related_name='maquinas_alocadas', help_text="Qual OP esta máquina está trabalhando no momento")
    
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nome} ({self.status_atual})"

class RegistroProducao(models.Model):
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE, related_name='registros')
    op = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, related_name='registros_tempo')
    
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    duracao_segundos = models.FloatField(default=0.0)
    
    finalizado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.fim and self.inicio:
            delta = self.fim - self.inicio
            self.duracao_segundos = delta.total_seconds()
            self.finalizado = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.maquina} na OP {self.op} ({self.duracao_segundos}s)"
