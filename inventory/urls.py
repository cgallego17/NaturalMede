from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('stock/', views.StockListView.as_view(), name='stock_list'),
    path('stock/low/', views.LowStockListView.as_view(), name='low_stock_list'),
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/add/', views.StockMovementCreateView.as_view(), name='movement_create'),
    path('transfers/', views.StockTransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.StockTransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.StockTransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/complete/', views.StockTransferCompleteView.as_view(), name='transfer_complete'),
]













