from django.contrib import admin
from .models import Warehouse, Stock, StockMovement, StockTransfer, StockTransferItem


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'is_active', 'is_main', 'created_at']
    list_filter = ['is_active', 'is_main', 'city', 'created_at']
    search_fields = ['name', 'code', 'city', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'min_stock', 'is_low_stock', 'is_out_of_stock']
    list_filter = ['warehouse', 'created_at', 'updated_at']
    search_fields = ['product__name', 'product__sku', 'warehouse__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Stock bajo'
    
    def is_out_of_stock(self, obj):
        return obj.is_out_of_stock
    is_out_of_stock.boolean = True
    is_out_of_stock.short_description = 'Sin stock'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'movement_type', 'quantity', 'reference', 'user', 'created_at']
    list_filter = ['movement_type', 'warehouse', 'created_at']
    search_fields = ['product__name', 'product__sku', 'reference', 'user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'warehouse', 'user')


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 1
    fields = ['product', 'quantity', 'notes']


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ['reference', 'from_warehouse', 'to_warehouse', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'from_warehouse', 'to_warehouse', 'created_at']
    search_fields = ['reference', 'from_warehouse__name', 'to_warehouse__name', 'created_by__username']
    readonly_fields = ['created_at', 'completed_at']
    inlines = [StockTransferItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_warehouse', 'to_warehouse', 'created_by')

