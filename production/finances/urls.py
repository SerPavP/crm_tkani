from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('', views.financial_dashboard, name='financial_dashboard'),
    path('settings/', views.system_settings, name='system_settings'),
    path('change-user-password/', views.change_user_password, name='change_user_password'),
    path('change-admin-password/', views.change_admin_password, name='change_admin_password'),
    path('change-user-password-page/', views.change_user_password_page, name='change_user_password_page'),
    path('change-admin-password-page/', views.change_admin_password_page, name='change_admin_password_page'),
    path('update-fabric-prices/', views.update_fabric_prices, name='update_fabric_prices'),
    path('get-markup-percentage/', views.get_markup_percentage, name='get_markup_percentage'),
    path('set-fabric-cost-price/', views.set_fabric_cost_price, name='set_fabric_cost_price'),
    path('get-period-data/', views.get_period_data, name='get_period_data'),
]

