from django.contrib import admin
from .models import OrdemProducao, OrdemProducaoItem, Maquina, RegistroProducao

@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'produto', 'quantidade_total', 'status', 'data_criacao')
    list_filter = ('status',)
    autocomplete_fields = ('produto',)

admin.site.register(OrdemProducaoItem)

@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'topico_mqtt', 'status_atual', 'op_atual', 'ultima_atualizacao')
    list_editable = ('op_atual',) 
    search_fields = ('nome', 'topico_mqtt')

@admin.register(RegistroProducao)
class RegistroProducaoAdmin(admin.ModelAdmin):
    list_display = ('maquina', 'op', 'inicio', 'fim', 'duracao_segundos', 'finalizado')
    list_filter = ('maquina', 'finalizado', 'op__status')
    readonly_fields = ('duracao_segundos',)
