from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    # Dashboard
    path('', views.purchase_dashboard, name='dashboard'),
    
    # Compras
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/edit/', views.purchase_edit, name='purchase_edit'),
    path('purchases/<int:pk>/receive/', views.purchase_receive, name='purchase_receive'),
    path('purchases/<int:pk>/receive-summary/', views.purchase_receive_summary, name='purchase_receive_summary'),
    path('purchases/<int:pk>/cancel/', views.purchase_cancel, name='purchase_cancel'),
    
    # Proveedores
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    
    # API
    path('api/products/', views.api_products, name='api_products'),
    
    # Test temporal
    path('test-debug/', views.test_form_debug, name='test_form_debug'),
]
