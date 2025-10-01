from django.contrib import admin
from .models import Supplier, Purchase, PurchaseItem, PurchaseReceipt


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    fields = ['product', 'quantity', 'unit_cost', 'tax_percentage', 'discount_percentage', 'total']
    readonly_fields = ['total']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_number', 'supplier', 'order_date', 'status', 'payment_status', 'total', 'created_by', 'created_at']
    list_filter = ['status', 'payment_status', 'order_date', 'created_at']
    search_fields = ['purchase_number', 'supplier__name', 'notes']
    readonly_fields = ['purchase_number', 'created_by', 'created_at', 'updated_at']
    inlines = [PurchaseItemInline]
    ordering = ['-created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'product', 'quantity', 'unit_cost', 'total']
    list_filter = ['purchase__status', 'product__category']
    search_fields = ['product__name', 'purchase__purchase_number']
    readonly_fields = ['subtotal', 'tax_amount', 'discount_amount', 'total']


@admin.register(PurchaseReceipt)
class PurchaseReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'purchase', 'received_by', 'received_at']
    list_filter = ['received_at']
    search_fields = ['receipt_number', 'purchase__purchase_number']
    readonly_fields = ['received_by', 'received_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.received_by = request.user
        super().save_model(request, obj, form, change)