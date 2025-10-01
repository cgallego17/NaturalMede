from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from datetime import datetime, timedelta
import random

from audit.models import InventoryTrace
from catalog.models import Product
from inventory.models import Warehouse
from purchases.models import Supplier


class Command(BaseCommand):
    help = 'Crea datos de demostración para la trazabilidad de inventario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Número de trazas de inventario a crear (default: 100)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días hacia atrás para generar trazas (default: 30)',
        )

    def handle(self, *args, **options):
        count = options['count']
        days = options['days']
        
        self.stdout.write(f'Creando {count} trazas de inventario de los últimos {days} días...')
        
        # Obtener datos necesarios
        products = list(Product.objects.all())
        warehouses = list(Warehouse.objects.all())
        users = list(User.objects.all())
        suppliers = list(Supplier.objects.all())
        
        if not products:
            self.stdout.write('No hay productos en el sistema. Creando productos demo...')
            from catalog.management.commands.create_demo_data import Command as DemoCommand
            demo_cmd = DemoCommand()
            demo_cmd.handle()
            products = list(Product.objects.all())
        
        if not warehouses:
            self.stdout.write('No hay bodegas en el sistema. Creando bodegas demo...')
            Warehouse.objects.create(name='Bodega Principal', location='Bogotá', is_main=True)
            warehouses = list(Warehouse.objects.all())
        
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
        
        if not suppliers:
            self.stdout.write('No hay proveedores en el sistema. Creando proveedor demo...')
            Supplier.objects.create(
                name='Proveedor Demo',
                contact_name='Contacto Demo',
                email='proveedor@demo.com',
                phone='3001234567'
            )
            suppliers = list(Supplier.objects.all())
        
        # Tipos de movimiento con pesos
        movement_types = [
            ('PURCHASE', 0.3),
            ('PURCHASE_RECEIPT', 0.2),
            ('STOCK_TRANSFER', 0.15),
            ('STOCK_TRANSFER_RECEIVE', 0.15),
            ('SALE', 0.15),
            ('STOCK_ADJUSTMENT', 0.05),
        ]
        
        created_count = 0
        
        for i in range(count):
            try:
                # Fecha aleatoria en los últimos N días
                days_ago = random.randint(0, days)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                # Seleccionar datos aleatorios
                product = random.choice(products)
                warehouse = random.choice(warehouses)
                user = random.choice(users)
                supplier = random.choice(suppliers) if random.random() < 0.7 else None
                
                # Seleccionar tipo de movimiento
                movement_type = random.choices(
                    [mt[0] for mt in movement_types],
                    weights=[mt[1] for mt in movement_types]
                )[0]
                
                # Generar cantidad (positiva para entradas, negativa para salidas)
                if movement_type in ['PURCHASE', 'PURCHASE_RECEIPT', 'STOCK_TRANSFER_RECEIVE']:
                    quantity = random.randint(10, 100)
                elif movement_type in ['SALE', 'STOCK_TRANSFER']:
                    quantity = -random.randint(1, 50)
                else:  # STOCK_ADJUSTMENT
                    quantity = random.choice([-random.randint(1, 20), random.randint(1, 20)])
                
                # Generar costos
                unit_cost = random.uniform(1000, 50000)
                total_cost = abs(quantity) * unit_cost
                
                # Simular stock actual
                stock_before = random.randint(0, 200)
                stock_after = stock_before + quantity
                
                # Generar información adicional
                batch_number = f"LOTE{random.randint(1000, 9999)}" if random.random() < 0.6 else None
                expiration_date = (timezone.now() + timedelta(days=random.randint(30, 365))).date() if random.random() < 0.4 else None
                
                # Generar notas
                notes_templates = [
                    f"Movimiento generado automáticamente",
                    f"Procesado por {user.username}",
                    f"Lote: {batch_number}" if batch_number else None,
                    f"Vencimiento: {expiration_date}" if expiration_date else None,
                    f"Costo unitario: ${unit_cost:,.0f}",
                ]
                notes = ". ".join([n for n in notes_templates if n])
                
                # Crear la trazabilidad
                trace = InventoryTrace.objects.create(
                    movement_type=movement_type,
                    product=product,
                    warehouse=warehouse,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    supplier=supplier,
                    user=user,
                    batch_number=batch_number,
                    expiration_date=expiration_date,
                    notes=notes,
                    created_at=created_at,
                    status='COMPLETED'
                )
                
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'Creadas {created_count} trazas...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando traza {i+1}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {created_count} trazas de inventario')
        )
        
        # Mostrar estadísticas
        self.show_stats()

    def show_stats(self):
        """Muestra estadísticas de las trazas creadas"""
        self.stdout.write('\n--- Estadísticas de Trazabilidad ---')
        
        total_traces = InventoryTrace.objects.count()
        today_traces = InventoryTrace.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Por tipo de movimiento
        movement_stats = {}
        for movement_type, _ in InventoryTrace.MOVEMENT_TYPES:
            count = InventoryTrace.objects.filter(movement_type=movement_type).count()
            if count > 0:
                movement_stats[movement_type] = count
        
        # Por bodega
        warehouse_stats = InventoryTrace.objects.values('warehouse__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Por producto
        product_stats = InventoryTrace.objects.values('product__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        self.stdout.write(f'Total de trazas: {total_traces}')
        self.stdout.write(f'Trazas de hoy: {today_traces}')
        
        if movement_stats:
            self.stdout.write('\nPor tipo de movimiento:')
            for movement_type, count in movement_stats.items():
                percentage = (count / total_traces) * 100
                self.stdout.write(f'  {movement_type}: {count} ({percentage:.1f}%)')
        
        if warehouse_stats:
            self.stdout.write('\nPor bodega:')
            for stat in warehouse_stats:
                percentage = (stat['count'] / total_traces) * 100
                self.stdout.write(f'  {stat["warehouse__name"]}: {stat["count"]} ({percentage:.1f}%)')
        
        if product_stats:
            self.stdout.write('\nProductos más movidos (top 5):')
            for stat in product_stats:
                percentage = (stat['count'] / total_traces) * 100
                self.stdout.write(f'  {stat["product__name"]}: {stat["count"]} ({percentage:.1f}%)')
        
        # Rango de fechas
        oldest_trace = InventoryTrace.objects.order_by('created_at').first()
        newest_trace = InventoryTrace.objects.order_by('-created_at').first()
        
        if oldest_trace and newest_trace:
            self.stdout.write(f'\nRango de fechas:')
            self.stdout.write(f'  Más antiguo: {oldest_trace.created_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write(f'  Más reciente: {newest_trace.created_at.strftime("%Y-%m-%d %H:%M")}')
