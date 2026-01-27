from django.urls import path
from . import api_views

app_name = 'customers_api'

urlpatterns = [
    path('customers/', api_views.CustomerListAPIView.as_view(), name='customer_list'),
    path('customers/create/', api_views.CustomerCreateAPIView.as_view(), name='customer_create'),
]










