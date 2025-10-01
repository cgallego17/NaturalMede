from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from audit.models import AuditLog, AuditConfiguration


class Command(BaseCommand):
    help = 'Limpia logs de auditoría antiguos según la configuración de retención'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Días de retención (sobrescribe configuración)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular limpieza sin eliminar registros',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar limpieza sin confirmación',
        )

    def handle(self, *args, **options):
        days = options.get('days')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se eliminarán registros')
            )
        
        # Obtener configuraciones
        configs = AuditConfiguration.objects.filter(is_enabled=True)
        
        if not configs.exists():
            self.stdout.write('No hay configuraciones de auditoría activas')
            return
        
        total_deleted = 0
        
        for config in configs:
            retention_days = days if days else config.retention_days
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            # Buscar logs antiguos para este modelo
            old_logs = AuditLog.objects.filter(
                content_type=config.content_type,
                created_at__lt=cutoff_date
            )
            
            count = old_logs.count()
            
            if count > 0:
                self.stdout.write(
                    f'{config.content_type.app_label}.{config.content_type.model}: '
                    f'{count} logs anteriores a {cutoff_date.strftime("%Y-%m-%d")} '
                    f'(retención: {retention_days} días)'
                )
                
                if not dry_run:
                    if not force:
                        confirm = input(f'¿Eliminar {count} logs? (y/N): ')
                        if confirm.lower() != 'y':
                            self.stdout.write('Cancelado')
                            continue
                    
                    deleted_count = old_logs.delete()[0]
                    total_deleted += deleted_count
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Eliminados {deleted_count} logs')
                    )
                else:
                    total_deleted += count
                    self.stdout.write(
                        self.style.WARNING(f'  (simulado) Se eliminarían {count} logs')
                    )
            else:
                self.stdout.write(
                    f'{config.content_type.app_label}.{config.content_type.model}: '
                    'No hay logs antiguos'
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\nSIMULACIÓN COMPLETADA: Se eliminarían {total_deleted} logs')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nLIMPIEZA COMPLETADA: Se eliminaron {total_deleted} logs')
            )
        
        # Mostrar estadísticas actuales
        self.show_current_stats()

    def show_current_stats(self):
        """Muestra estadísticas actuales de logs"""
        self.stdout.write('\n--- Estadísticas Actuales ---')
        
        total_logs = AuditLog.objects.count()
        today_logs = AuditLog.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Logs por severidad
        severity_stats = {}
        for severity, _ in AuditLog.SEVERITY_CHOICES:
            count = AuditLog.objects.filter(severity=severity).count()
            if count > 0:
                severity_stats[severity] = count
        
        self.stdout.write(f'Total de logs: {total_logs}')
        self.stdout.write(f'Logs de hoy: {today_logs}')
        
        if severity_stats:
            self.stdout.write('Por severidad:')
            for severity, count in severity_stats.items():
                self.stdout.write(f'  {severity}: {count}')
        
        # Logs más antiguos
        oldest_log = AuditLog.objects.order_by('created_at').first()
        if oldest_log:
            self.stdout.write(f'Log más antiguo: {oldest_log.created_at.strftime("%Y-%m-%d")}')
        
        # Logs más recientes
        newest_log = AuditLog.objects.order_by('-created_at').first()
        if newest_log:
            self.stdout.write(f'Log más reciente: {newest_log.created_at.strftime("%Y-%m-%d %H:%M")}')
