from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.POSDashboardView.as_view(), name='dashboard'),
    path('session/', views.POSSessionView.as_view(), name='session'),
    path('session/open/', views.POSSessionOpenView.as_view(), name='session_open'),
    path('session/close/<int:pk>/', views.POSSessionCloseView.as_view(), name='session_close'),
    path('sale/', views.POSSaleView.as_view(), name='sale'),
    path('sale/create/', views.POSSaleCreateView.as_view(), name='sale_create'),
    path('sale/<int:pk>/', views.POSSaleDetailView.as_view(), name='sale_detail'),
    path('sale/<int:pk>/print/', views.POSSalePrintView.as_view(), name='sale_print'),
    path('sale/<int:pk>/email/', views.POSSaleEmailView.as_view(), name='sale_email'),
    path('barcode/', views.BarcodeScanView.as_view(), name='barcode_scan'),
    path('quick-sale/', views.QuickSaleView.as_view(), name='quick_sale'),
]

