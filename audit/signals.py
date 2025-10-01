from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import json

from .models import AuditLog, AuditConfiguration


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """
    Captura eventos de creación y actualización
    """
    # Evitar auditoría de nuestros propios modelos para evitar recursión
    if sender.__name__ in ['AuditLog', 'AuditConfiguration', 'AuditReport']:
        return
    
    # Verificar si la auditoría está habilitada para este modelo
    try:
        content_type = ContentType.objects.get_for_model(sender)
        config = AuditConfiguration.objects.get(content_type=content_type)
        
        if not config.is_enabled:
            return
            
        # Verificar si debemos rastrear este tipo de evento
        if created and not config.track_creates:
            return
        if not created and not config.track_updates:
            return
            
    except AuditConfiguration.DoesNotExist:
        # Si no hay configuración específica, usar configuración por defecto
        pass
    
    # Determinar la acción
    action = 'CREATE' if created else 'UPDATE'
    
    # Obtener valores actuales
    new_values = {}
    if hasattr(instance, '_audit_fields'):
        # Si el modelo especifica campos a auditar
        for field in instance._audit_fields:
            if hasattr(instance, field):
                value = getattr(instance, field)
                new_values[field] = str(value) if value is not None else None
    else:
        # Auditar todos los campos del modelo
        for field in instance._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at']:
                value = getattr(instance, field.name)
                new_values[field.name] = str(value) if value is not None else None
    
    # Obtener valores anteriores si es una actualización
    old_values = {}
    if not created and hasattr(instance, '_audit_old_values'):
        old_values = instance._audit_old_values
    
    # Crear el registro de auditoría
    AuditLog.objects.create(
        action=action,
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance),
        old_values=old_values if old_values else None,
        new_values=new_values if new_values else None,
        severity=getattr(config, 'severity_level', 'MEDIUM') if 'config' in locals() else 'MEDIUM',
        app_label=sender._meta.app_label,
        model_name=sender._meta.model_name,
        message=f"{action} de {sender._meta.verbose_name}: {str(instance)}"
    )


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """
    Captura valores anteriores antes de la actualización
    """
    # Evitar auditoría de nuestros propios modelos
    if sender.__name__ in ['AuditLog', 'AuditConfiguration', 'AuditReport']:
        return
    
    # Solo para actualizaciones (no creaciones)
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            old_values = {}
            
            # Capturar valores anteriores
            for field in instance._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at']:
                    value = getattr(old_instance, field.name)
                    old_values[field.name] = str(value) if value is not None else None
            
            # Almacenar valores anteriores en la instancia
            instance._audit_old_values = old_values
            
        except sender.DoesNotExist:
            pass


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """
    Captura eventos de eliminación
    """
    # Evitar auditoría de nuestros propios modelos
    if sender.__name__ in ['AuditLog', 'AuditConfiguration', 'AuditReport']:
        return
    
    # Verificar si la auditoría está habilitada para este modelo
    try:
        content_type = ContentType.objects.get_for_model(sender)
        config = AuditConfiguration.objects.get(content_type=content_type)
        
        if not config.is_enabled or not config.track_deletes:
            return
            
    except AuditConfiguration.DoesNotExist:
        pass
    
    # Obtener valores del objeto eliminado
    old_values = {}
    for field in instance._meta.fields:
        if field.name not in ['id', 'created_at', 'updated_at']:
            value = getattr(instance, field.name)
            old_values[field.name] = str(value) if value is not None else None
    
    # Crear el registro de auditoría
    AuditLog.objects.create(
        action='DELETE',
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance),
        old_values=old_values,
        new_values=None,
        severity=getattr(config, 'severity_level', 'MEDIUM') if 'config' in locals() else 'MEDIUM',
        app_label=sender._meta.app_label,
        model_name=sender._meta.model_name,
        message=f"DELETE de {sender._meta.verbose_name}: {str(instance)}"
    )


@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """
    Captura eventos de inicio de sesión
    """
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        content_type=None,
        object_id=None,
        object_repr=f"Usuario: {user.username}",
        severity='LOW',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        session_key=request.session.session_key,
        app_label='auth',
        model_name='user',
        message=f"Usuario {user.username} inició sesión"
    )


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """
    Captura eventos de cierre de sesión
    """
    AuditLog.objects.create(
        user=user,
        action='LOGOUT',
        content_type=None,
        object_id=None,
        object_repr=f"Usuario: {user.username}",
        severity='LOW',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        session_key=request.session.session_key,
        app_label='auth',
        model_name='user',
        message=f"Usuario {user.username} cerró sesión"
    )


def get_client_ip(request):
    """
    Obtiene la IP del cliente desde la request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, obj=None, message=None, severity='MEDIUM', 
                    old_values=None, new_values=None, extra_data=None, request=None):
    """
    Función helper para crear registros de auditoría manualmente
    """
    log_data = {
        'user': user,
        'action': action,
        'severity': severity,
        'message': message,
        'old_values': old_values,
        'new_values': new_values,
        'extra_data': extra_data,
        'content_type': None,
        'object_id': None,
        'object_repr': None,
        'app_label': 'system',
        'model_name': 'system',
    }
    
    if obj:
        log_data.update({
            'content_type': ContentType.objects.get_for_model(obj),
            'object_id': str(obj.pk),
            'object_repr': str(obj),
            'app_label': obj._meta.app_label,
            'model_name': obj._meta.model_name,
        })
    
    if request:
        log_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_key': request.session.session_key,
        })
    
    return AuditLog.objects.create(**log_data)
