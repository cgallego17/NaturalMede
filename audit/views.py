from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
import json
import csv

from .models import AuditLog, AuditConfiguration, AuditReport
from .utils import generate_audit_report


class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar registros de auditoría
    """
    model = AuditLog
    template_name = 'audit/audit_log_list.html'
    context_object_name = 'audit_logs'
    permission_required = 'audit.view_auditlog'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type').order_by('-created_at')
        
        # Filtros
        user_filter = self.request.GET.get('user')
        action_filter = self.request.GET.get('action')
        severity_filter = self.request.GET.get('severity')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(object_repr__icontains=search) |
                Q(message__icontains=search) |
                Q(ip_address__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        context['stats'] = {
            'total_logs': AuditLog.objects.count(),
            'today_logs': AuditLog.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'critical_logs': AuditLog.objects.filter(
                severity='CRITICAL'
            ).count(),
            'failed_logs': AuditLog.objects.filter(
                status='FAILED'
            ).count(),
        }
        
        # Filtros disponibles
        context['action_choices'] = AuditLog.ACTION_CHOICES
        context['severity_choices'] = AuditLog.SEVERITY_CHOICES
        
        return context


class AuditLogDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Vista para mostrar detalles de un registro de auditoría
    """
    model = AuditLog
    template_name = 'audit/audit_log_detail.html'
    context_object_name = 'audit_log'
    permission_required = 'audit.view_auditlog'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Intentar obtener el objeto relacionado
        if self.object.content_object:
            context['related_object'] = self.object.content_object
        
        return context


@login_required
@permission_required('audit.view_auditlog')
def audit_dashboard(request):
    """
    Dashboard de auditoría con estadísticas
    """
    # Estadísticas generales
    total_logs = AuditLog.objects.count()
    today_logs = AuditLog.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    # Logs por acción
    action_stats = AuditLog.objects.values('action').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Logs por severidad
    severity_stats = AuditLog.objects.values('severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Logs por usuario (últimos 30 días)
    user_stats = AuditLog.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Logs por día (últimos 30 días)
    daily_stats = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        count = AuditLog.objects.filter(
            created_at__date=date
        ).count()
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_stats.reverse()
    
    # Eventos críticos recientes
    critical_events = AuditLog.objects.filter(
        severity='CRITICAL'
    ).order_by('-created_at')[:10]
    
    # Eventos fallidos recientes
    failed_events = AuditLog.objects.filter(
        status='FAILED'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_logs': total_logs,
        'today_logs': today_logs,
        'action_stats': action_stats,
        'severity_stats': severity_stats,
        'user_stats': user_stats,
        'daily_stats': daily_stats,
        'critical_events': critical_events,
        'failed_events': failed_events,
    }
    
    return render(request, 'audit/dashboard.html', context)


@login_required
@permission_required('audit.view_auditlog')
def audit_export(request):
    """
    Exportar registros de auditoría a CSV
    """
    # Obtener filtros de la request
    filters = {}
    if request.GET.get('user'):
        filters['user__username__icontains'] = request.GET.get('user')
    if request.GET.get('action'):
        filters['action'] = request.GET.get('action')
    if request.GET.get('severity'):
        filters['severity'] = request.GET.get('severity')
    if request.GET.get('date_from'):
        try:
            date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d').date()
            filters['created_at__date__gte'] = date_from
        except ValueError:
            pass
    if request.GET.get('date_to'):
        try:
            date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d').date()
            filters['created_at__date__lte'] = date_to
        except ValueError:
            pass
    
    # Obtener registros
    logs = AuditLog.objects.filter(**filters).order_by('-created_at')
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Usuario', 'Acción', 'Objeto', 'Severidad', 
        'Estado', 'IP', 'Mensaje'
    ])
    
    for log in logs:
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else '',
            log.get_action_display(),
            log.object_repr or '',
            log.get_severity_display(),
            log.get_status_display(),
            log.ip_address or '',
            log.message or '',
        ])
    
    return response


@login_required
@permission_required('audit.add_auditreport')
def generate_report(request):
    """
    Generar reporte de auditoría
    """
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        parameters = {
            'date_from': request.POST.get('date_from'),
            'date_to': request.POST.get('date_to'),
            'user': request.POST.get('user'),
            'action': request.POST.get('action'),
            'severity': request.POST.get('severity'),
        }
        
        # Crear registro de reporte
        report = AuditReport.objects.create(
            name=f"Reporte {report_type} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            report_type=report_type,
            parameters=parameters,
            created_by=request.user,
            status='PENDING'
        )
        
        # Generar reporte en background (aquí podrías usar Celery)
        try:
            generate_audit_report(report)
            return JsonResponse({'success': True, 'report_id': report.id})
        except Exception as e:
            report.status = 'FAILED'
            report.error_message = str(e)
            report.save()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'audit/generate_report.html')


@login_required
@permission_required('audit.view_auditlog')
def audit_api(request):
    """
    API para obtener datos de auditoría (para gráficos)
    """
    chart_type = request.GET.get('chart_type')
    
    if chart_type == 'daily':
        # Datos diarios para gráfico
        days = int(request.GET.get('days', 30))
        data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            count = AuditLog.objects.filter(created_at__date=date).count()
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        data.reverse()
        return JsonResponse({'data': data})
    
    elif chart_type == 'actions':
        # Estadísticas por acción
        data = list(AuditLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count'))
        return JsonResponse({'data': data})
    
    elif chart_type == 'severity':
        # Estadísticas por severidad
        data = list(AuditLog.objects.values('severity').annotate(
            count=Count('id')
        ))
        return JsonResponse({'data': data})
    
    return JsonResponse({'error': 'Invalid chart type'})
