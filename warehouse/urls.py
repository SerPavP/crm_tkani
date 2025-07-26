from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.view_rolls, name='view_rolls'),
    path('manage/', views.manage_rolls, name='manage_rolls'),
    path('create-barcode/', views.create_barcode, name='create_barcode'),
    path('scan-barcode/', views.scan_barcode, name='scan_barcode'),
    path('print/<str:barcode>/', views.barcode_print, name='barcode_print'),
    path('print-pending/', views.print_pending_barcodes, name='print_pending_barcodes'),
    path('delete-roll/', views.delete_roll, name='delete_roll'),
    path('api/fabric-colors/', views.get_fabric_colors_api, name='get_fabric_colors_api'),
    path('api/rolls-by-color/', views.get_rolls_by_color_api, name='get_rolls_by_color_api'),
    path('api/search-barcodes/', views.search_barcodes_api, name='search_barcodes_api'),
    path('api/scan-barcode-image/', views.scan_barcode_function_view, name='scan_barcode_image'), # логика для сканирование штрих кода
]

