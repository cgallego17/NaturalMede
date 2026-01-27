from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('home-login/', views.home_login, name='home_login'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Productos CRUD
    path('products/', views.admin_products, name='admin_products'),
    path('products/create/', views.admin_product_create, name='admin_product_create'),
    path('products/<int:pk>/', views.admin_product_detail, name='admin_product_detail'),
    path('products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    
    # Categorías CRUD
    path('categories/', views.admin_categories, name='admin_categories'),
    path('categories/create/', views.admin_category_create, name='admin_category_create'),
    path('categories/<int:pk>/', views.admin_category_detail, name='admin_category_detail'),
    path('categories/<int:pk>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    # Marcas CRUD
    path('brands/', views.admin_brands, name='admin_brands'),
    path('brands/create/', views.admin_brand_create, name='admin_brand_create'),
    path('brands/<int:pk>/', views.admin_brand_detail, name='admin_brand_detail'),
    path('brands/<int:pk>/edit/', views.admin_brand_edit, name='admin_brand_edit'),
    path('brands/<int:pk>/delete/', views.admin_brand_delete, name='admin_brand_delete'),
    
    path('inventory/', views.admin_inventory, name='admin_inventory'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('customers/', views.admin_customers, name='admin_customers'),
    path('customers/create/', views.admin_customer_create, name='admin_customer_create'),
    path('customers/<int:pk>/', views.admin_customer_detail, name='admin_customer_detail'),
    path('customers/<int:pk>/edit/', views.admin_customer_edit, name='admin_customer_edit'),
    path('customers/<int:pk>/toggle-vip/', views.admin_customer_toggle_vip, name='admin_customer_toggle_vip'),
    path('customers/<int:pk>/toggle-status/', views.admin_customer_toggle_status, name='admin_customer_toggle_status'),
    path('customers/<int:pk>/orders/', views.admin_customer_orders, name='admin_customer_orders'),
    path('pos/', views.admin_pos, name='admin_pos'),
    path('reports/', views.admin_reports, name='admin_reports'),
    
    # POS Sales desde admin
    path('pos-sale/<int:pk>/', views.admin_pos_sale_detail, name='admin_pos_sale_detail'),
    path('pos-sale/<int:pk>/print/', views.admin_pos_sale_print, name='admin_pos_sale_print'),
    path('pos-sale/<int:pk>/email/', views.admin_pos_sale_email, name='admin_pos_sale_email'),
    
    # Gestión de Inventario
    path('inventory/adjust/<int:stock_id>/', views.admin_adjust_stock, name='admin_adjust_stock'),
    path('inventory/transfer/<int:stock_id>/', views.admin_transfer_stock, name='admin_transfer_stock'),
    path('inventory/history/<int:stock_id>/', views.admin_stock_history, name='admin_stock_history'),
    path('inventory/create-transfer/', views.admin_create_transfer, name='admin_create_transfer'),
    path('inventory/transfers/', views.admin_transfer_list, name='admin_transfer_list'),
    path('inventory/transfers/<int:transfer_id>/', views.admin_transfer_detail, name='admin_transfer_detail'),
    path('inventory/transfers/<int:transfer_id>/complete/', views.admin_complete_transfer, name='admin_complete_transfer'),
    path('inventory/warehouses/', views.admin_warehouse_management, name='admin_warehouse_management'),
    path('inventory/warehouses/create/', views.admin_create_warehouse, name='admin_create_warehouse'),
    path('inventory/warehouses/<int:warehouse_id>/', views.admin_warehouse_detail, name='admin_warehouse_detail'),
    path('inventory/warehouses/<int:warehouse_id>/edit/', views.admin_edit_warehouse, name='admin_edit_warehouse'),
    path('inventory/warehouses/<int:warehouse_id>/toggle/', views.admin_toggle_warehouse_status, name='admin_toggle_warehouse_status'),
    path('inventory/reports/', views.admin_inventory_reports, name='admin_inventory_reports'),
    
    # API endpoints
    path('api/products-with-stock/', views.api_products_with_stock, name='api_products_with_stock'),
    
    # Configuración Wompi
    path('wompi-config/', views.admin_wompi_config, name='admin_wompi_config'),
]
