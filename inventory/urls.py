from django.urls import path
from . import views

urlpatterns = [
    # Materiais
    path('materials/', views.material_list, name='material_list'),
    path('materials/new/', views.material_create, name='material_create'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('materials/<int:pk>/add-color/', views.material_add_color, name='material_add_color'),
    
    # Cores
    path('colors/', views.color_list, name='color_list'),
    path('colors/new/', views.color_create, name='color_create'),
    
    # Movimentação
    path('entry/new/', views.stock_entry_create, name='stock_entry_create'),
    path('movements/', views.movement_list, name='movement_list'),
]
