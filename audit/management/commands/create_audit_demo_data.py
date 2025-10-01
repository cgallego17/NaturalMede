from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
import random

from audit.models import AuditLog
from catalog.models import Product, Category, Brand
from customers.models import Customer
from orders.models import Order
from pos.models import POSSale, POSSession
from inventory.models import Stock, Warehouse


class Command(BaseCommand):
    help = 'Crea datos de demostración para el sistema de auditoría'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Número de logs de auditoría a crear (default: 100)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días hacia atrás para generar logs (default: 30)',
        )

    def handle(self, *args, **options):
        count = options['count']
        days = options['days']
        
        self.stdout.write(f'Creando {count} logs de auditoría de los últimos {days} días...')
        
        # Obtener usuarios
        users = list(User.objects.all())
        if not users:
            self.stdout.write('No hay usuarios en el sistema. Creando usuario demo...')
            user = User.objects.create_user(
                username='demo_user',
                email='demo@example.com',
                password='demo123',
                first_name='Usuario',
                last_name='Demo'
            )
            users = [user]
        
        # Obtener modelos para auditar
        models_to_audit = [
            (Product, 'CREATE', 'Producto creado'),
            (Product, 'UPDATE', 'Producto actualizado'),
            (Category, 'CREATE', 'Categoría creada'),
            (Brand, 'CREATE', 'Marca creada'),
            (Customer, 'CREATE', 'Cliente creado'),
            (Customer, 'UPDATE', 'Cliente actualizado'),
            (Order, 'CREATE', 'Orden creada'),
            (Order, 'UPDATE', 'Orden actualizada'),
            (POSSale, 'CREATE', 'Venta POS creada'),
            (Stock, 'UPDATE', 'Stock actualizado'),
        ]
        
        # Acciones del sistema
        system_actions = [
            ('LOGIN', 'Usuario inició sesión'),
            ('LOGOUT', 'Usuario cerró sesión'),
            ('VIEW', 'Usuario visualizó información'),
            ('EXPORT', 'Usuario exportó datos'),
            ('PRINT', 'Usuario imprimió documento'),
            ('EMAIL', 'Usuario envió email'),
        ]
        
        # Severidades
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        severity_weights = [0.4, 0.4, 0.15, 0.05]  # Más logs de severidad baja/media
        
        # Estados
        statuses = ['SUCCESS', 'FAILED']
        status_weights = [0.9, 0.1]  # 90% exitosos, 10% fallidos
        
        created_count = 0
        
        for i in range(count):
            try:
                # Fecha aleatoria en los últimos N días
                days_ago = random.randint(0, days)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                # Usuario aleatorio
                user = random.choice(users)
                
                # Decidir si es acción de modelo o sistema
                if random.random() < 0.7:  # 70% acciones de modelo
                    model_class, action, message = random.choice(models_to_audit)
                    
                    # Intentar obtener un objeto existente
                    try:
                        obj = model_class.objects.order_by('?').first()
                        if obj:
                            content_type = ContentType.objects.get_for_model(model_class)
                            object_id = obj.pk
                            object_repr = str(obj)
                            app_label = model_class._meta.app_label
                            model_name = model_class._meta.model_name
                        else:
                            # Si no hay objetos, crear log sin objeto
                            content_type = None
                            object_id = None
                            object_repr = None
                            app_label = model_class._meta.app_label
                            model_name = model_class._meta.model_name
                    except:
                        content_type = None
                        object_id = None
                        object_repr = None
                        app_label = model_class._meta.app_label
                        model_name = model_class._meta.model_name
                else:  # 30% acciones del sistema
                    action, message = random.choice(system_actions)
                    content_type = None
                    object_id = None
                    object_repr = None
                    app_label = 'system'
                    model_name = 'system'
                
                # Severidad aleatoria
                severity = random.choices(severities, weights=severity_weights)[0]
                
                # Estado aleatorio
                status = random.choices(statuses, weights=status_weights)[0]
                
                # IP aleatoria
                ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                
                # User agent aleatorio
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    'Mozilla/5.0 (Android 10; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
                ]
                user_agent = random.choice(user_agents)
                
                # Crear el log
                log = AuditLog.objects.create(
                    user=user,
                    action=action,
                    content_type=content_type,
                    object_id=object_id,
                    object_repr=object_repr,
                    severity=severity,
                    status=status,
                    message=message,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_key=f"session_{random.randint(100000, 999999)}",
                    app_label=app_label,
                    model_name=model_name,
                    created_at=created_at,
                )
                
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'Creados {created_count} logs...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando log {i+1}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {created_count} logs de auditoría')
        )
        
        # Mostrar estadísticas
        self.show_stats()

    def show_stats(self):
        """Muestra estadísticas de los logs creados"""
        self.stdout.write('\n--- Estadísticas de Auditoría ---')
        
        total_logs = AuditLog.objects.count()
        today_logs = AuditLog.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Por severidad
        severity_stats = {}
        for severity, _ in AuditLog.SEVERITY_CHOICES:
            count = AuditLog.objects.filter(severity=severity).count()
            if count > 0:
                severity_stats[severity] = count
        
        # Por acción
        action_stats = {}
        for action, _ in AuditLog.ACTION_CHOICES:
            count = AuditLog.objects.filter(action=action).count()
            if count > 0:
                action_stats[action] = count
        
        # Por usuario
        user_stats = AuditLog.objects.filter(
            user__isnull=False
        ).values('user__username').distinct().count()
        
        self.stdout.write(f'Total de logs: {total_logs}')
        self.stdout.write(f'Logs de hoy: {today_logs}')
        self.stdout.write(f'Usuarios únicos: {user_stats}')
        
        if severity_stats:
            self.stdout.write('\nPor severidad:')
            for severity, count in severity_stats.items():
                percentage = (count / total_logs) * 100
                self.stdout.write(f'  {severity}: {count} ({percentage:.1f}%)')
        
        if action_stats:
            self.stdout.write('\nPor acción (top 5):')
            sorted_actions = sorted(action_stats.items(), key=lambda x: x[1], reverse=True)[:5]
            for action, count in sorted_actions:
                percentage = (count / total_logs) * 100
                self.stdout.write(f'  {action}: {count} ({percentage:.1f}%)')
        
        # Rango de fechas
        oldest_log = AuditLog.objects.order_by('created_at').first()
        newest_log = AuditLog.objects.order_by('-created_at').first()
        
        if oldest_log and newest_log:
            self.stdout.write(f'\nRango de fechas:')
            self.stdout.write(f'  Más antiguo: {oldest_log.created_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write(f'  Más reciente: {newest_log.created_at.strftime("%Y-%m-%d %H:%M")}')
