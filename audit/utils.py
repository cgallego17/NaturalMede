import os
import csv
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, AuditReport, InventoryTrace


def generate_audit_report(report):
    """
    Genera un reporte de auditoría
    """
    try:
        report.status = 'GENERATING'
        report.save()
        
        # Crear directorio de reportes si no existe
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'audit_reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generar nombre de archivo
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_report_{report.report_type}_{timestamp}.csv"
        filepath = os.path.join(reports_dir, filename)
        
        # Aplicar filtros
        filters = {}
        params = report.parameters
        
        if params.get('date_from'):
            try:
                date_from = datetime.strptime(params['date_from'], '%Y-%m-%d').date()
                filters['created_at__date__gte'] = date_from
            except ValueError:
                pass
        
        if params.get('date_to'):
            try:
                date_to = datetime.strptime(params['date_to'], '%Y-%m-%d').date()
                filters['created_at__date__lte'] = date_to
            except ValueError:
                pass
        
        if params.get('user'):
            filters['user__username__icontains'] = params['user']
        
        if params.get('action'):
            filters['action'] = params['action']
        
        if params.get('severity'):
            filters['severity'] = params['severity']
        
        # Obtener datos
        logs = AuditLog.objects.filter(**filters).order_by('-created_at')
        
        # Generar CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Escribir encabezados
            writer.writerow([
                'ID', 'Fecha', 'Usuario', 'Acción', 'Objeto', 'Severidad',
                'Estado', 'IP', 'User Agent', 'Mensaje', 'Cambios'
            ])
            
            # Escribir datos
            for log in logs:
                changes = ""
                if log.has_changes:
                    changes = log.changes_summary
                
                writer.writerow([
                    log.id,
                    log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    log.user.username if log.user else '',
                    log.get_action_display(),
                    log.object_repr or '',
                    log.get_severity_display(),
                    log.get_status_display(),
                    log.ip_address or '',
                    log.user_agent or '',
                    log.message or '',
                    changes
                ])
        
        # Actualizar reporte
        report.status = 'COMPLETED'
        report.file_path = filepath
        report.file_size = os.path.getsize(filepath)
        report.completed_at = timezone.now()
        report.save()
        
    except Exception as e:
        report.status = 'FAILED'
        report.error_message = str(e)
        report.completed_at = timezone.now()
        report.save()
        raise e


def cleanup_old_logs():
    """
    Limpia logs antiguos según la configuración de retención
    """
    configs = AuditConfiguration.objects.all()
    
    for config in configs:
        cutoff_date = timezone.now() - timedelta(days=config.retention_days)
        
        old_logs = AuditLog.objects.filter(
            content_type=config.content_type,
            created_at__lt=cutoff_date
        )
        
        count = old_logs.count()
        old_logs.delete()
        
        print(f"Eliminados {count} logs antiguos para {config.content_type}")


def get_audit_summary(days=30):
    """
    Obtiene un resumen de auditoría para los últimos N días
    """
    start_date = timezone.now() - timedelta(days=days)
    
    summary = {
        'total_events': AuditLog.objects.filter(
            created_at__gte=start_date
        ).count(),
        
        'by_action': list(AuditLog.objects.filter(
            created_at__gte=start_date
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')),
        
        'by_severity': list(AuditLog.objects.filter(
            created_at__gte=start_date
        ).values('severity').annotate(
            count=Count('id')
        )),
        
        'by_user': list(AuditLog.objects.filter(
            created_at__gte=start_date,
            user__isnull=False
        ).values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]),
        
        'critical_events': AuditLog.objects.filter(
            created_at__gte=start_date,
            severity='CRITICAL'
        ).count(),
        
        'failed_events': AuditLog.objects.filter(
            created_at__gte=start_date,
            status='FAILED'
        ).count(),
    }
    
    return summary


def log_custom_event(user, action, obj=None, message=None, severity='MEDIUM', 
                   old_values=None, new_values=None, extra_data=None, request=None):
    """
    Función helper para crear logs de auditoría personalizados
    """
    from .signals import create_audit_log
    return create_audit_log(
        user=user,
        action=action,
        obj=obj,
        message=message,
        severity=severity,
        old_values=old_values,
        new_values=new_values,
        extra_data=extra_data,
        request=request
    )


def get_model_audit_config(model_class):
    """
    Obtiene la configuración de auditoría para un modelo específico
    """
    try:
        content_type = ContentType.objects.get_for_model(model_class)
        return AuditConfiguration.objects.get(content_type=content_type)
    except AuditConfiguration.DoesNotExist:
        return None


def is_audit_enabled_for_model(model_class):
    """
    Verifica si la auditoría está habilitada para un modelo
    """
    config = get_model_audit_config(model_class)
    return config.is_enabled if config else True


def get_audit_stats():
    """
    Obtiene estadísticas generales de auditoría
    """
    return {
        'total_logs': AuditLog.objects.count(),
        'today_logs': AuditLog.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
        'this_week_logs': AuditLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'this_month_logs': AuditLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'critical_logs': AuditLog.objects.filter(severity='CRITICAL').count(),
        'failed_logs': AuditLog.objects.filter(status='FAILED').count(),
        'unique_users': AuditLog.objects.filter(
            user__isnull=False
        ).values('user').distinct().count(),
    }


def create_inventory_trace(movement_type, product, warehouse, quantity, 
                          unit_cost=None, total_cost=None, user=None,
                          purchase=None, purchase_item=None,
                          stock_transfer=None, stock_transfer_item=None,
                          pos_sale=None, pos_sale_item=None,
                          order=None, order_item=None,
                          supplier=None, batch_number=None, 
                          expiration_date=None, notes=None, **kwargs):
    """
    Función helper para crear trazabilidad de inventario
    """
    try:
        # Obtener stock actual
        from inventory.models import Stock
        stock_obj = Stock.objects.filter(
            product=product, 
            warehouse=warehouse
        ).first()
        
        stock_before = stock_obj.quantity if stock_obj else 0
        stock_after = stock_before + quantity
        
        # Crear el registro de trazabilidad
        trace = InventoryTrace.objects.create(
            movement_type=movement_type,
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            stock_before=stock_before,
            stock_after=stock_after,
            purchase=purchase,
            purchase_item=purchase_item,
            stock_transfer=stock_transfer,
            stock_transfer_item=stock_transfer_item,
            pos_sale=pos_sale,
            pos_sale_item=pos_sale_item,
            order=order,
            order_item=order_item,
            supplier=supplier,
            batch_number=batch_number,
            expiration_date=expiration_date,
            user=user,
            notes=notes,
            extra_data=kwargs.get('extra_data')
        )
        
        # Crear también un log de auditoría
        AuditLog.objects.create(
            user=user,
            action='STOCK_MOVEMENT',
            content_type=ContentType.objects.get_for_model(InventoryTrace),
            object_id=str(trace.pk),
            object_repr=str(trace),
            severity='MEDIUM',
            app_label='audit',
            model_name='inventorytrace',
            message=trace.movement_description,
            extra_data={
                'movement_type': movement_type,
                'product_id': product.id,
                'warehouse_id': warehouse.id,
                'quantity': float(quantity),
                'stock_before': float(stock_before),
                'stock_after': float(stock_after),
            }
        )
        
        return trace
        
    except Exception as e:
        # Log del error pero no fallar la operación principal
        print(f"Error creando trazabilidad de inventario: {str(e)}")
        return None
