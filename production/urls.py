from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.production_dashboard, name='production_dashboard'),
    path('generate-op/<int:sku_id>/', views.create_op, name='create_op'),
    path('create/', views.create_op_screen, name='create_op_screen'),
    path('create-bulk/', views.create_op_bulk, name='create_op_bulk'),
    path('ops/', views.op_list, name='op_list'),
    path('iot/', views.iot_dashboard, name='iot_dashboard'),
    path('iot/status/', views.iot_dashboard_status, name='iot_dashboard_status'),
    path('status-change/<int:pk>/<str:status>/', views.op_change_status, name='op_change_status'),
    path('allocation/<int:pk>/', views.op_allocation, name='op_allocation'),
    
    # Maquinas
    path('machines/', views.maquina_list, name='maquina_list'),
    path('machines/create/', views.maquina_create, name='maquina_create'),
    path('machines/update/<int:pk>/', views.maquina_update, name='maquina_update'),
    path('machines/delete/<int:pk>/', views.maquina_delete, name='maquina_delete'),
]
