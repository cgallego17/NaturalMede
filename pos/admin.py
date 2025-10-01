from django.contrib import admin
from .models import POSSession, POSSale, POSSaleItem


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'warehouse', 'status', 'opening_cash', 'closing_cash', 'total_sales', 'opened_at']
    list_filter = ['status', 'warehouse', 'opened_at', 'closed_at']
    search_fields = ['session_id', 'user__username', 'warehouse__name']
    readonly_fields = ['session_id', 'opened_at', 'closed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'warehouse')


class POSSaleItemInline(admin.TabularInline):
    model = POSSaleItem
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'iva_percentage', 'discount_percentage', 'subtotal', 'iva_amount', 'discount_amount', 'total']
    readonly_fields = ['subtotal', 'iva_amount', 'discount_amount', 'total']


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'session', 'customer', 'payment_method', 'total', 'created_at']
    list_filter = ['payment_method', 'created_at', 'session__warehouse']
    search_fields = ['sale_number', 'session__session_id', 'customer__user__first_name', 'customer__user__last_name']
    readonly_fields = ['sale_number', 'created_at', 'updated_at']
    inlines = [POSSaleItemInline]
    
    fieldsets = (
        ('Información de la venta', {
            'fields': ('sale_number', 'session', 'customer', 'payment_method')
        }),
        ('Totales', {
            'fields': ('subtotal', 'iva_amount', 'discount_amount', 'total')
        }),
        ('Información adicional', {
            'fields': ('notes', 'barcode_scanned')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'customer__user')







