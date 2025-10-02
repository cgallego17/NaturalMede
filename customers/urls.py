from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='customer_list'),
    path('create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('<int:pk>/addresses/', views.CustomerAddressListView.as_view(), name='customer_address_list'),
    path('<int:pk>/addresses/create/', views.CustomerAddressCreateView.as_view(), name='customer_address_create'),
    path('addresses/<int:pk>/edit/', views.CustomerAddressUpdateView.as_view(), name='customer_address_update'),
    path('addresses/<int:pk>/delete/', views.CustomerAddressDeleteView.as_view(), name='customer_address_delete'),
    path('vip/', views.VIPCustomerListView.as_view(), name='vip_customer_list'),
]











