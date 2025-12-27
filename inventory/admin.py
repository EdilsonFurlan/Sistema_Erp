from django.contrib import admin
from inventory.models import Material, Cor, EstoqueMaterial, EntradaEstoque

admin.site.register(Material)
admin.site.register(Cor)
admin.site.register(EstoqueMaterial)

@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
    list_display = ('data', 'material', 'cor', 'quantidade', 'preco_unitario', 'fornecedor')
    list_filter = ('material', 'cor', 'data')
