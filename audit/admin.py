from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, AuditConfiguration, AuditReport, InventoryTrace


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'action', 'object_repr', 
        'severity', 'status', 'has_changes_display'
    ]
    list_filter = [
        'action', 'severity', 'status', 'app_label', 
        'model_name', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'object_repr', 
        'message', 'ip_address'
    ]
    readonly_fields = [
        'created_at', 'content_type', 'object_id', 
        'object_repr', 'has_changes', 'changes_summary'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'action', 'severity', 'status', 'created_at')
        }),
        ('Objeto Afectado', {
            'fields': ('content_type', 'object_id', 'object_repr')
        }),
        ('Cambios', {
            'fields': ('old_values', 'new_values', 'has_changes', 'changes_summary'),
            'classes': ('collapse',)
        }),
        ('Contexto', {
            'fields': ('message', 'ip_address', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('app_label', 'model_name', 'extra_data'),
            'classes': ('collapse',)
        }),
    )
    
    def has_changes_display(self, obj):
        """Muestra si hay cambios registrados"""
        if obj.has_changes:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')
    has_changes_display.short_description = 'Cambios'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'user', 'content_type'
        )
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar solo a superusuarios"""
        return request.user.is_superuser


@admin.register(InventoryTrace)
class InventoryTraceAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'movement_type', 'product', 'warehouse', 
        'quantity', 'stock_before', 'stock_after', 'user', 'status'
    ]
    list_filter = [
        'movement_type', 'status', 'warehouse', 'created_at'
    ]
    search_fields = [
        'product__name', 'product__sku', 'batch_number', 
        'notes', 'user__username'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'stock_before', 'stock_after'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('movement_type', 'status', 'product', 'warehouse', 'user', 'created_at')
        }),
        ('Cantidades', {
            'fields': ('quantity', 'unit_cost', 'total_cost', 'stock_before', 'stock_after')
        }),
        ('Documentos Origen', {
            'fields': ('purchase', 'purchase_item', 'stock_transfer', 'stock_transfer_item', 
                      'pos_sale', 'pos_sale_item', 'order', 'order_item'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('supplier', 'batch_number', 'expiration_date', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('extra_data', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'product', 'warehouse', 'user', 'supplier',
            'purchase', 'stock_transfer', 'pos_sale', 'order'
        )
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar solo a superusuarios"""
        return request.user.is_superuser


@admin.register(AuditConfiguration)
class AuditConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'content_type', 'is_enabled', 'track_creates', 
        'track_updates', 'track_deletes', 'severity_level'
    ]
    list_filter = ['is_enabled', 'track_creates', 'track_updates', 'track_deletes', 'severity_level']
    search_fields = ['content_type__model', 'content_type__app_label']
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('content_type', 'is_enabled', 'severity_level', 'retention_days')
        }),
        ('Eventos a Rastrear', {
            'fields': ('track_creates', 'track_updates', 'track_deletes', 'track_views')
        }),
        ('Campos', {
            'fields': ('track_fields', 'exclude_fields'),
            'description': 'track_fields: campos específicos a auditar (vacío = todos). exclude_fields: campos a excluir.'
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('content_type')


@admin.register(AuditReport)
class AuditReportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'status', 'created_by', 
        'created_at', 'file_size_display'
    ]
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at', 'completed_at', 'duration_display']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'report_type', 'status', 'created_by')
        }),
        ('Parámetros', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Archivo', {
            'fields': ('file_path', 'file_size_display'),
            'classes': ('collapse',)
        }),
        ('Tiempos', {
            'fields': ('created_at', 'completed_at', 'duration_display'),
            'classes': ('collapse',)
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Muestra el tamaño del archivo de forma legible"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = 'Tamaño'
    
    def duration_display(self, obj):
        """Muestra la duración de generación"""
        if obj.duration:
            total_seconds = obj.duration.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f} segundos"
            elif total_seconds < 3600:
                return f"{total_seconds / 60:.1f} minutos"
            else:
                return f"{total_seconds / 3600:.1f} horas"
        return "-"
    duration_display.short_description = 'Duración'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('created_by')
    
    def has_change_permission(self, request, obj=None):
        """Solo permitir editar reportes pendientes"""
        if obj and obj.status not in ['PENDING', 'FAILED']:
            return False
        return super().has_change_permission(request, obj)
