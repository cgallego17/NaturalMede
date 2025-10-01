from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditConfiguration


class Command(BaseCommand):
    help = 'Configura la auditoría automática para todos los modelos del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disable-all',
            action='store_true',
            help='Deshabilitar auditoría para todos los modelos',
        )
        parser.add_argument(
            '--enable-all',
            action='store_true',
            help='Habilitar auditoría para todos los modelos',
        )
        parser.add_argument(
            '--models',
            nargs='+',
            help='Lista de modelos específicos a configurar',
        )

    def handle(self, *args, **options):
        if options['disable_all']:
            self.disable_all_audit()
        elif options['enable_all']:
            self.enable_all_audit()
        elif options['models']:
            self.configure_specific_models(options['models'])
        else:
            self.setup_default_audit()

    def disable_all_audit(self):
        """Deshabilita la auditoría para todos los modelos"""
        self.stdout.write('Deshabilitando auditoría para todos los modelos...')
        
        configs = AuditConfiguration.objects.all()
        for config in configs:
            config.is_enabled = False
            config.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Se deshabilitó la auditoría para {configs.count()} modelos')
        )

    def enable_all_audit(self):
        """Habilita la auditoría para todos los modelos"""
        self.stdout.write('Habilitando auditoría para todos los modelos...')
        
        # Obtener todos los content types
        content_types = ContentType.objects.all()
        
        for content_type in content_types:
            config, created = AuditConfiguration.objects.get_or_create(
                content_type=content_type,
                defaults={
                    'is_enabled': True,
                    'track_creates': True,
                    'track_updates': True,
                    'track_deletes': True,
                    'track_views': False,
                    'severity_level': 'MEDIUM',
                    'retention_days': 365,
                }
            )
            
            if not created:
                config.is_enabled = True
                config.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Se habilitó la auditoría para {content_types.count()} modelos')
        )

    def configure_specific_models(self, model_names):
        """Configura auditoría para modelos específicos"""
        self.stdout.write(f'Configurando auditoría para modelos: {", ".join(model_names)}')
        
        for model_name in model_names:
            try:
                # Buscar el content type por nombre del modelo
                content_type = ContentType.objects.filter(model=model_name.lower()).first()
                
                if not content_type:
                    self.stdout.write(
                        self.style.WARNING(f'Modelo {model_name} no encontrado')
                    )
                    continue
                
                config, created = AuditConfiguration.objects.get_or_create(
                    content_type=content_type,
                    defaults={
                        'is_enabled': True,
                        'track_creates': True,
                        'track_updates': True,
                        'track_deletes': True,
                        'track_views': False,
                        'severity_level': 'MEDIUM',
                        'retention_days': 365,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Configuración creada para {model_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Configuración ya existe para {model_name}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error configurando {model_name}: {str(e)}')
                )

    def setup_default_audit(self):
        """Configuración por defecto de auditoría para modelos importantes"""
        self.stdout.write('Configurando auditoría por defecto...')
        
        # Modelos importantes del sistema
        important_models = [
            'user',           # Usuarios
            'product',        # Productos
            'category',       # Categorías
            'brand',          # Marcas
            'customer',       # Clientes
            'order',          # Órdenes
            'orderitem',      # Items de órdenes
            'possale',        # Ventas POS
            'possaleitem',    # Items de ventas POS
            'possession',     # Sesiones POS
            'stock',          # Stock
            'stockmovement',  # Movimientos de stock
            'warehouse',      # Bodegas
            'stocktransfer',  # Transferencias de stock
            'supplier',       # Proveedores
            'purchase',       # Compras
            'purchaseitem',   # Items de compras
        ]
        
        configured_count = 0
        
        for model_name in important_models:
            try:
                content_type = ContentType.objects.filter(model=model_name.lower()).first()
                
                if not content_type:
                    continue
                
                config, created = AuditConfiguration.objects.get_or_create(
                    content_type=content_type,
                    defaults={
                        'is_enabled': True,
                        'track_creates': True,
                        'track_updates': True,
                        'track_deletes': True,
                        'track_views': False,
                        'severity_level': 'MEDIUM',
                        'retention_days': 365,
                    }
                )
                
                if created:
                    configured_count += 1
                    self.stdout.write(
                        f'[OK] Configurado: {content_type.app_label}.{content_type.model}'
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error configurando {model_name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se configuró la auditoría para {configured_count} modelos')
        )
        
        # Mostrar configuración actual
        self.show_current_config()

    def show_current_config(self):
        """Muestra la configuración actual de auditoría"""
        self.stdout.write('\n--- Configuración Actual ---')
        
        configs = AuditConfiguration.objects.filter(is_enabled=True).select_related('content_type')
        
        if not configs.exists():
            self.stdout.write('No hay modelos con auditoría habilitada')
            return
        
        for config in configs:
            self.stdout.write(
                f'[OK] {config.content_type.app_label}.{config.content_type.model} '
                f'(Retencion: {config.retention_days} dias)'
            )
        
        self.stdout.write(f'\nTotal: {configs.count()} modelos configurados')
