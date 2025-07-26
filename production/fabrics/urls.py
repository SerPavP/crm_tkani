from django.urls import path
from . import views

app_name = 'fabrics'

urlpatterns = [
    path('', views.fabric_list, name='fabric_list'),
    path('create/', views.fabric_create, name='fabric_create'),
    path('<int:fabric_id>/', views.fabric_detail, name='fabric_detail'),
    path('<int:fabric_id>/edit/', views.fabric_edit, name='fabric_edit'),
    path('<int:fabric_id>/delete/', views.fabric_delete, name='fabric_delete'),
    path('<int:fabric_id>/colors/create/', views.color_create, name='color_create'),
    path('colors/<int:color_id>/edit/', views.color_edit, name='color_edit'),
    path('api/<int:fabric_id>/colors/', views.get_fabric_colors, name='get_fabric_colors'),
    path("get-colors-by-fabric/", views.get_colors_by_fabric, name="get_colors_by_fabric"),
]

