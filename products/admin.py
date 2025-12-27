from django.contrib import admin
from products.models import (
    Produto, ItensMaterial, ProdutoInsumo, ProdutoConsumo
)

class ItensMaterialInline(admin.TabularInline):
    model = ItensMaterial
    extra = 1

class ProdutoInsumoInline(admin.TabularInline):
    model = ProdutoInsumo
    extra = 1

class ProdutoConsumoInline(admin.TabularInline):
    model = ProdutoConsumo
    extra = 0
    readonly_fields = ('consumo_total',)

class VariantesInline(admin.TabularInline):
    model = Produto
    fk_name = 'parent'
    extra = 0
    fields = ('sku', 'preco')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sku', 'parent', 'eh_padrao')
    list_filter = ('molde', 'eh_padrao')
    search_fields = ('nome', 'sku')
    inlines = [ItensMaterialInline, ProdutoInsumoInline, VariantesInline, ProdutoConsumoInline]
