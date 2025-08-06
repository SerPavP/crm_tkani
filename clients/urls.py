from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('search/', views.client_search_ajax, name='client_search_ajax'),
    path('create/', views.client_create, name='client_create'),
    path('<int:client_id>/', views.client_detail, name='client_detail'),
    path('<int:client_id>/edit/', views.client_edit, name='client_edit'),
    path('<int:client_id>/delete/', views.client_delete, name='client_delete'),
]

