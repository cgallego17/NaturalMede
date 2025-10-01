from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('sales/', views.SalesReportView.as_view(), name='sales_report'),
    path('inventory/', views.InventoryReportView.as_view(), name='inventory_report'),
    path('products/', views.ProductsReportView.as_view(), name='products_report'),
    path('customers/', views.CustomersReportView.as_view(), name='customers_report'),
    path('financial/', views.FinancialReportView.as_view(), name='financial_report'),
    path('export/<str:report_type>/', views.ReportExportView.as_view(), name='report_export'),
]







