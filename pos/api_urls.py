from django.urls import path
from . import api_views

urlpatterns = [
    path('sales/create/', api_views.POSSaleCreateAPIView.as_view(), name='api_pos_sale_create'),
    path('sales/', api_views.pos_sales_list, name='api_pos_sales_list'),
    path('sales/<int:pk>/', api_views.pos_sale_detail, name='api_pos_sale_detail'),
    path('session/open/', api_views.POSSessionOpenAPIView.as_view(), name='api_pos_session_open'),
    path('session/close/', api_views.POSSessionCloseAPIView.as_view(), name='api_pos_session_close'),
    path('session/status/', api_views.pos_session_status, name='api_pos_session_status'),
    path('warehouses/', api_views.warehouses_list, name='api_pos_warehouses'),
]
