from django.contrib import admin
from .models import Order, OrderItem, ShippingRate, WompiConfig


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
        ('Información Wompi', {
            'fields': ('wompi_transaction_id', 'wompi_reference', 'wompi_status'),
            'classes': ('collapse',)
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


@admin.register(WompiConfig)
class WompiConfigAdmin(admin.ModelAdmin):
    list_display = ['environment', 'is_active', 'has_public_key', 'has_private_key', 'has_events_secret', 'has_integrity_secret', 'updated_at']
    list_filter = ['environment', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('environment', 'is_active')
        }),
        ('Credenciales', {
            'fields': ('public_key', 'private_key', 'events_secret', 'integrity_secret'),
            'description': 'Credenciales obtenidas desde el panel de Wompi: https://comercios.wompi.co/'
        }),
        ('Información', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una instancia
        return not WompiConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
    
    def has_public_key(self, obj):
        return bool(obj.public_key)
    has_public_key.boolean = True
    has_public_key.short_description = 'Clave Pública'
    
    def has_private_key(self, obj):
        return bool(obj.private_key)
    has_private_key.boolean = True
    has_private_key.short_description = 'Clave Privada'

    def has_events_secret(self, obj):
        return bool(obj.events_secret)
    has_events_secret.boolean = True
    has_events_secret.short_description = 'Secreto Eventos'
    
    def has_integrity_secret(self, obj):
        return bool(obj.integrity_secret)
    has_integrity_secret.boolean = True
    has_integrity_secret.short_description = 'Secreto Integridad'

