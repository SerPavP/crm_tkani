from django.urls import path
from . import views

app_name = 'deals'

urlpatterns = [
    path('', views.deal_list, name='deal_list'),
    path('create/', views.deal_create, name='deal_create'),
    path('<int:deal_id>/', views.deal_detail, name='deal_detail'),
    path('<int:deal_id>/edit/', views.deal_edit, name='deal_edit'),
    path('<int:deal_id>/delete/', views.deal_delete, name='deal_delete'),
    path('<int:deal_id>/change-status/', views.deal_change_status, name='deal_change_status'),
    path('<int:deal_id>/add-item/', views.add_deal_item, name='add_deal_item'),
    path('<int:deal_id>/edit-item/<int:item_id>/', views.edit_deal_item, name='edit_deal_item'),
    path('<int:deal_id>/remove-item/<int:item_id>/', views.delete_deal_item, name='remove_deal_item'),
    path('api/fabric-colors/', views.get_fabric_colors, name='get_fabric_colors'),
    path('api/fabric-color-price/', views.get_fabric_color_price, name='get_fabric_color_price'),
    path('api/fabric-color-details/', views.get_fabric_color_details, name='get_fabric_color_details'),
    path('<int:deal_id>/export/pdf/', views.export_deal_pdf, name='export_deal_pdf'),
    path('<int:deal_id>/export/excel/', views.export_deal_excel, name='export_deal_excel'),
    path('<int:deal_id>/print/warehouse/', views.print_deal_warehouse, name='print_deal_warehouse'),
]


