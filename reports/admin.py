from django.contrib import admin
from .models import ReportTemplate, ReportSchedule


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'frequency', 'is_active', 'last_run', 'next_run', 'created_by']
    list_filter = ['frequency', 'is_active', 'last_run', 'created_at']
    search_fields = ['name', 'template__name', 'created_by__username', 'email_recipients']
    readonly_fields = ['last_run', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'created_by')











