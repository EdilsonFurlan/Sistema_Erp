from django.contrib import admin
from sales.models import Pedido, PedidoItem, PedidoConfig

admin.site.register(Pedido)
admin.site.register(PedidoItem)
admin.site.register(PedidoConfig)
