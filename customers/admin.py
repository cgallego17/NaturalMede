from django.contrib import admin
from .models import Customer, CustomerAddress


class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    extra = 1
    fields = ['name', 'address', 'city', 'phone', 'is_default', 'notes']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'customer_type', 'document_number', 'phone', 'city', 'is_active', 'created_at']
    list_filter = ['customer_type', 'is_active', 'city', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'document_number', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CustomerAddressInline]
    
    fieldsets = (
        ('Información personal', {
            'fields': ('user', 'customer_type', 'document_type', 'document_number')
        }),
        ('Contacto', {
            'fields': ('phone', 'address', 'city')
        }),
        ('Información adicional', {
            'fields': ('birth_date', 'notes')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'name', 'city', 'is_default', 'created_at']
    list_filter = ['is_default', 'city', 'created_at']
    search_fields = ['customer__user__first_name', 'customer__user__last_name', 'name', 'address', 'city']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer__user')











