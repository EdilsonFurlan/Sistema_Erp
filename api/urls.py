from django.urls import path
from . import views

urlpatterns = [
    path('materiais/', views.list_materials, name='api_materiais'),
    path('insumos/', views.list_insumos, name='api_insumos'),
    path('moldes/', views.create_molde, name='api_create_molde'),
    path('produtos-padrao/', views.create_produto_padrao, name='api_create_produto'),
    path('moldes/<int:pk>/', views.get_molde, name='api_get_molde'),
    path('produtos-padrao/<int:pk>/', views.get_produto_padrao, name='api_get_produto'),
]
