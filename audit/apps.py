from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Sistema de Auditoría'
    
    def ready(self):
        # Importar señales cuando la app esté lista
        import audit.signals
        import audit.inventory_signals
