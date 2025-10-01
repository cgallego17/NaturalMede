from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditLog


class Command(BaseCommand):
    help = 'Corrige logs de auditoría con datos inconsistentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular corrección sin hacer cambios',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se harán cambios')
            )
        
        # Buscar logs con object_id inválido (strings en lugar de números)
        problematic_logs = []
        
        for log in AuditLog.objects.all():
            try:
                # Intentar convertir object_id a entero si no es None
                if log.object_id is not None:
                    int(log.object_id)
            except (ValueError, TypeError):
                problematic_logs.append(log)
        
        self.stdout.write(f'Encontrados {len(problematic_logs)} logs problemáticos')
        
        if not problematic_logs:
            self.stdout.write('No se encontraron logs problemáticos')
            return
        
        # Mostrar logs problemáticos
        for log in problematic_logs[:10]:  # Mostrar solo los primeros 10
            self.stdout.write(
                f'Log ID {log.id}: object_id="{log.object_id}" '
                f'(tipo: {type(log.object_id).__name__})'
            )
        
        if len(problematic_logs) > 10:
            self.stdout.write(f'... y {len(problematic_logs) - 10} más')
        
        if not dry_run:
            # Corregir logs problemáticos
            corrected_count = 0
            
            for log in problematic_logs:
                try:
                    # Para logs de login/logout, limpiar object_id
                    if log.action in ['LOGIN', 'LOGOUT']:
                        log.object_id = None
                        log.content_type = None
                        log.object_repr = f"Usuario: {log.user.username if log.user else 'Sistema'}"
                        log.app_label = 'auth'
                        log.model_name = 'user'
                        log.save()
                        corrected_count += 1
                    
                    # Para otros logs, intentar determinar el tipo correcto
                    elif log.object_id and isinstance(log.object_id, str):
                        # Si es una clave de sesión, limpiar
                        if len(log.object_id) > 20:  # Las claves de sesión son largas
                            log.object_id = None
                            log.content_type = None
                            log.object_repr = 'Sistema'
                            log.app_label = 'system'
                            log.model_name = 'system'
                            log.save()
                            corrected_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error corrigiendo log {log.id}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Se corrigieron {corrected_count} logs')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Se corregirían {len(problematic_logs)} logs')
            )
        
        # Mostrar estadísticas finales
        self.show_stats()

    def show_stats(self):
        """Muestra estadísticas de logs"""
        self.stdout.write('\n--- Estadísticas de Logs ---')
        
        total_logs = AuditLog.objects.count()
        valid_logs = 0
        invalid_logs = 0
        
        for log in AuditLog.objects.all():
            try:
                if log.object_id is not None:
                    int(log.object_id)
                valid_logs += 1
            except (ValueError, TypeError):
                invalid_logs += 1
        
        self.stdout.write(f'Total de logs: {total_logs}')
        self.stdout.write(f'Logs válidos: {valid_logs}')
        self.stdout.write(f'Logs inválidos: {invalid_logs}')
        
        if invalid_logs > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Aún hay {invalid_logs} logs con problemas')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos los logs están correctos')
            )
