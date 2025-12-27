from django.db import models

class Cor(models.Model):
    nome = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, default="#FFFFFF", help_text="Cor hexadecimal para visualização")

    def __str__(self):
        return self.nome

class Material(models.Model):
    """
    Aviamentos e insumos gerais unificados.
    Pode ser Tecido (tem largura) ou Acessório (unidade variada).
    """
    nome = models.CharField(max_length=200)
    unidade = models.CharField(max_length=50, help_text="Ex: mt, un, kg, par")
    
    # Preços
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Preço atual de referência (Última Compra)")
    preco_medio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Média ponderada do estoque")
    estoque_atual = models.FloatField(default=0.0)
    
    # Campos Específicos de Tecido
    eh_tecido = models.BooleanField(default=False, help_text="Marque se este material for usado para corte (Tecido)")
    largura_padrao_mm = models.IntegerField(default=1500, blank=True, null=True, help_text="Apenas para tecidos")

    # Campos Específicos de Acessórios com Variação
    tem_cor = models.BooleanField(default=False, help_text="Se marcado, exige escolha de cor na Variante")

    def is_unidade_medida(self):
        """Verifica se a unidade é de comprimento (metro, cm, mm)"""
        u = self.unidade.lower().strip()
        return u in ['mt', 'm', 'mts', 'metro', 'metros', 'cm', 'centimetro', 'mm', 'milimetro']

    def get_valor_display(self, valor_base):
        """
        Converte o valor do banco (ex: 800 mm) para o valor de exibição (ex: 0.8 mt).
        Assume que se for medida, o banco está em MM.
        """
        if not valor_base:
            return 0.0
            
        if self.is_unidade_medida():
            u = self.unidade.lower().strip()
            if u in ['mt', 'm', 'mts', 'metro', 'metros']:
                return valor_base / 1000.0
            elif u in ['cm', 'centimetro']:
                return valor_base / 10.0
        
        return valor_base

    def to_db_value(self, valor_input):
        """
        Converte o valor de entrada (ex: Metros) para o valor de banco (ex: MM).
        """
        if not valor_input:
            return 0.0
            
        if self.is_unidade_medida():
            u = self.unidade.lower().strip()
            if u in ['mt', 'm', 'mts', 'metro', 'metros']:
                return valor_input * 1000.0
            elif u in ['cm', 'centimetro']:
                return valor_input * 10.0
        
        return valor_input

    def get_unidade_display(self):
        return self.unidade

    def __str__(self):
        return f"{self.nome} ({self.unidade})"

class EstoqueMaterial(models.Model):
    """
    Controla o estoque atual de cada Material + Cor.
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='estoques')
    cor = models.ForeignKey(Cor, on_delete=models.PROTECT, null=True, blank=True)
    quantidade = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('material', 'cor')
    
    def __str__(self):
        cor_nome = self.cor.nome if self.cor else "Sem Cor"
        qtd_fmt = self.material.get_valor_display(self.quantidade)
        return f"{self.material.nome} - {cor_nome}: {qtd_fmt:.2f} {self.material.unidade}"

class EntradaEstoque(models.Model):
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='entradas')
    cor = models.ForeignKey(Cor, on_delete=models.PROTECT, null=True, blank=True, help_text="Cor do material que está entrando")
    data = models.DateField(auto_now_add=True)
    quantidade = models.FloatField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fornecedor = models.CharField(max_length=200, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Converte a quantidade inserida (Display Unit) para Storage Unit (DB)
        # Ex: User digita 100 (metros) -> Salvamos 100000 (mm)
        # NOTA: Isso assume que 'self.quantidade' vem do form na unidade de visualização.
        # Precisamos ter cuidado para não reconverter se já estiver convertido.
        # Na prática, save() é chamado após form.save(). O form joga o valor inputado.
        
        # IMPORTANTE: Se formos editar uma entrada antiga, nao devemos multiplicar de novo.
        # Por simplificação, assumiremos que EntradaEstoque é imutavel via sistema ou 
        # que o save() lida apenas com a criação dos estoques agregados.
        
        # Para evitar dupla conversão em updates, vamos calcular o valor "real" apenas para somar no estoque.
        # Mas persistem os dados originais de entrada? 
        # Estratégia: O campo 'quantidade' da EntradaEstoque será SEMPRE o valor digitado (Histórico fiel).
        # O campo 'EstoqueMaterial.quantidade' e 'Material.estoque_atual' serão convertidos.
        
        qtd_db = self.material.to_db_value(self.quantidade)
        
        super().save(*args, **kwargs)
        
        if is_new:
            # 1. Atualiza Preço de Custo (Referência) no Material Pai
            self.material.preco_custo = self.preco_unitario
            
            # 2. Atualiza Estoque Geral
            self.material.estoque_atual += qtd_db
            self.material.save()
            
            # 3. Atualiza ou Cria o Estoque Específico
            estoque_esp, created = EstoqueMaterial.objects.get_or_create(
                material=self.material,
                cor=self.cor,
                defaults={'quantidade': 0}
            )
            estoque_esp.quantidade += qtd_db
            estoque_esp.save()

    def __str__(self):
        cor_nome = self.cor.nome if self.cor else "S/ Cor"
        qtd_fmt = self.material.get_valor_display(self.quantidade)
        return f"{self.data} - {self.material.nome} ({cor_nome}): {qtd_fmt:.2f} {self.material.unidade}"
