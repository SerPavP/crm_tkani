from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('', views.financial_dashboard, name='financial_dashboard'),
    path('settings/', views.system_settings, name='system_settings'),
    path('set-fabric-cost/', views.set_fabric_cost_price, name='set_fabric_cost_price'),
    path('change-password/', views.change_password, name='change_password'),
    path('update-user-name/', views.update_user_name, name='update_user_name'),
    path('recreate-user/', views.recreate_user, name='recreate_user'),
    path('change-user-password/', views.change_user_password, name='change_user_password'),
    path('update-fabric-prices/', views.update_fabric_prices, name='update_fabric_prices'),
    path('get-markup-percentage/', views.get_markup_percentage, name='get_markup_percentage'),
    path('get-period-data/', views.get_period_data, name='get_period_data'),
]

