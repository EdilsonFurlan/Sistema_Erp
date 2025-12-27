from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('new/', views.client_create, name='client_create'),
    path('<int:client_id>/edit/', views.client_update, name='client_update'),
    path('<int:client_id>/delete/', views.client_delete, name='client_delete'),
]
