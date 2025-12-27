from django.urls import path
from . import views
from . import views_os

urlpatterns = [
    # Product Management
    path('dashboard/', views.integrated_view, name='integrated_view'),
    path('products/', views.product_list, name='product_list'),
    path('products/create/<int:molde_id>/', views.product_create, name='product_create'),
    path('products/<int:product_id>/detail/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Molde Management
    path('moldes/import/', views.molde_import, name='molde_import'),
    
    # Variant Management / SKU
    path('products/<int:reference_id>/sku/create/', views.sku_create, name='sku_create'),
    path('products/sku/<int:sku_id>/delete/', views.sku_delete, name='sku_delete'),
    path('products/<int:reference_id>/variants/', views.get_ref_variants, name='get_ref_variants'),

    # Engineering / OS
    path('engineering/', views_os.engineering_dashboard, name='engineering_dashboard'),
    path('os/<int:os_id>/', views_os.os_detail, name='os_detail'),
]
