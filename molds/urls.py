from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.molde_list, name='molde_list'),
    path('<int:molde_id>/', views.molde_detail, name='molde_detail'),
    path('<int:molde_id>/delete/', views.molde_delete, name='molde_delete'),
]
