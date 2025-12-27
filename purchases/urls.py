from django.urls import path
from . import views

urlpatterns = [
    path('purchase/planning/', views.purchase_planning, name='purchase_planning'),
    path('purchase/create/preview/', views.visualize_purchase_creation, name='visualize_purchase_creation'),
    path('purchase/create/finish/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase/list/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase/<int:oc_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase/<int:oc_id>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('purchase/<int:oc_id>/recalculate/', views.purchase_order_recalculate, name='purchase_order_recalculate'),
]
