from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/edit/', views.OrderUpdateView.as_view(), name='order_update'),
    path('<int:pk>/status/<str:status>/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('<int:pk>/invoice/', views.OrderInvoiceView.as_view(), name='order_invoice'),
    path('shipping-rates/', views.ShippingRateListView.as_view(), name='shipping_rate_list'),
    path('shipping-rates/create/', views.ShippingRateCreateView.as_view(), name='shipping_rate_create'),
    path('shipping-rates/<int:pk>/edit/', views.ShippingRateUpdateView.as_view(), name='shipping_rate_update'),
    path('shipping-rates/<int:pk>/delete/', views.ShippingRateDeleteView.as_view(), name='shipping_rate_delete'),
]











