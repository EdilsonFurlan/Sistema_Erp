from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CPF/CNPJ")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
