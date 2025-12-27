from django.urls import path
from . import views

urlpatterns = [
    path('order/create/', views.create_order, name='create_order'),
    path('order/<int:item_id>/configure/', views.configure_order_item, name='configure_order_item'),
    path('order/<int:item_id>/visualize/', views.visualize_order, name='visualize_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/materials/', views.order_materials, name='order_materials'),
    
    # New ERP Routes
    path('orders/new/', views.order_upsert, name='sales_order_create'),
    path('orders/<int:pk>/edit/', views.order_upsert, name='sales_order_update'),
    path('items/<int:item_id>/release/', views.release_item, name='release_item'),
]
