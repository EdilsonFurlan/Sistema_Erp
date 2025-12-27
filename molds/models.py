from django.db import models
from django.core.validators import FileExtensionValidator
from inventory.models import Material

class Molde(models.Model):
    nome = models.CharField(max_length=200)
    arquivo_json = models.FileField(
        upload_to='moldes/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['mld', 'json'])],
        help_text="Arquivo de molde (.mld preferencialmente ou .json)"
    )
    imagem = models.ImageField(upload_to='moldes/thumbs/', blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class MoldeDetalhe(models.Model):
    """
    Antigo MoldePeca. Representa as peças do molde (geometria).
    """
    molde = models.ForeignKey(Molde, on_delete=models.CASCADE, related_name='detalhes')
    nome_original = models.CharField(max_length=200) # Nome que veio do JSON
    tipo_geom = models.CharField(max_length=50) # pol, rect, circle
    
    # Updated Fields for Tech Pack
    area_base_mm2 = models.FloatField(default=0.0, help_text="Área líquida da peça")
    largura_mm = models.FloatField(default=0.0, help_text="Largura do bounding box (mm)")
    altura_mm = models.FloatField(default=0.0, help_text="Altura do bounding box (mm)")
    # material_padrao removed
    
    qtd_padrao = models.IntegerField(default=1)
    rotacao_fixa = models.BooleanField(default=False, help_text="Se marcado, a peça não pode ser rotacionada (respeitar fio)")
    orientacao_fio = models.CharField(max_length=50, blank=True, null=True, help_text="Orientação do fio (ex: vertical, horizontal)")
    geometria_json = models.JSONField(help_text="Dados completos da geometria para desenho")

    def __str__(self):
        return f"{self.nome_original} ({self.molde.nome})"
