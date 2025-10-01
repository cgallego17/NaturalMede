from django.contrib import admin
from .models import Order, OrderItem, ShippingRate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'iva_percentage', 'subtotal', 'iva_amount', 'total']
    readonly_fields = ['subtotal', 'iva_amount', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'paid_at', 'shipped_at', 'delivered_at']
    search_fields = ['order_number', 'customer__user__first_name', 'customer__user__last_name', 'customer__user__email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Información de la orden', {
            'fields': ('order_number', 'customer', 'status', 'payment_method')
        }),
        ('Totales', {
            'fields': ('subtotal', 'iva_amount', 'shipping_cost', 'total')
        }),
        ('Información de envío', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_phone', 'shipping_notes')
        }),
        ('Notas', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer__user')


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['city', 'min_weight', 'max_weight', 'cost', 'estimated_days', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'created_at']
    search_fields = ['city']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['city', 'min_weight']

