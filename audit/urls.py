from django.urls import path
from . import views, inventory_views

app_name = 'audit'

urlpatterns = [
    # Dashboard
    path('', views.audit_dashboard, name='dashboard'),
    
    # Lista de logs
    path('logs/', views.AuditLogListView.as_view(), name='log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    
    # Exportar
    path('export/', views.audit_export, name='export'),
    
    # Reportes
    path('reports/generate/', views.generate_report, name='generate_report'),
    
    # API
    path('api/', views.audit_api, name='api'),
    
    # Trazabilidad de Inventario
    path('inventory/', inventory_views.inventory_trace_dashboard, name='inventory_trace_dashboard'),
    path('inventory/traces/', inventory_views.InventoryTraceListView.as_view(), name='inventory_trace_list'),
    path('inventory/traces/<int:pk>/', inventory_views.InventoryTraceDetailView.as_view(), name='inventory_trace_detail'),
    path('inventory/traces/export/', inventory_views.inventory_trace_export, name='inventory_trace_export'),
    path('inventory/traces/api/', inventory_views.inventory_trace_api, name='inventory_trace_api'),
    path('inventory/product/<int:product_id>/', inventory_views.product_trace_report, name='product_trace_report'),
]
