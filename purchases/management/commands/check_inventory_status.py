from django.core.management.base import BaseCommand
from django.db.models import Sum, F
from inventory.models import Warehouse, Stock, StockMovement
from catalog.models import Product
from purchases.models import Purchase, PurchaseItem


class Command(BaseCommand):
    help = 'Verifica el estado del inventario y la integración con compras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--warehouse',
            type=str,
            help='Código de la bodega a verificar (por defecto: bodega principal)',
        )
        parser.add_argument(
            '--product',
            type=str,
            help='SKU del producto a verificar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== VERIFICACIÓN DE INVENTARIO ==='))
        
        # Verificar bodega principal
        warehouse_code = options.get('warehouse')
        if warehouse_code:
            try:
                warehouse = Warehouse.objects.get(code=warehouse_code)
            except Warehouse.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Bodega con código {warehouse_code} no encontrada'))
                return
        else:
            warehouse = Warehouse.objects.filter(is_main=True, is_active=True).first()
            if not warehouse:
                self.stdout.write(self.style.ERROR('No se encontró bodega principal'))
                return
        
        self.stdout.write(f'Bodega verificada: {warehouse.name} ({warehouse.code})')
        
        # Verificar producto específico si se especifica
        product_sku = options.get('product')
        if product_sku:
            try:
                product = Product.objects.get(sku=product_sku)
                self.check_product_inventory(product, warehouse)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Producto con SKU {product_sku} no encontrado'))
        else:
            self.check_all_inventory(warehouse)
        
        # Verificar integración con compras
        self.check_purchase_integration(warehouse)

    def check_product_inventory(self, product, warehouse):
        """Verifica el inventario de un producto específico"""
        self.stdout.write(f'\n--- Inventario de {product.name} ({product.sku}) ---')
        
        try:
            stock = Stock.objects.get(product=product, warehouse=warehouse)
            self.stdout.write(f'Stock actual: {stock.quantity} unidades')
            self.stdout.write(f'Stock mínimo: {stock.min_stock} unidades')
            
            if stock.is_low_stock:
                self.stdout.write(self.style.WARNING('WARNING: STOCK BAJO'))
            if stock.is_out_of_stock:
                self.stdout.write(self.style.ERROR('ERROR: SIN STOCK'))
            
            # Verificar movimientos recientes
            recent_movements = StockMovement.objects.filter(
                product=product,
                warehouse=warehouse
            ).order_by('-created_at')[:5]
            
            if recent_movements:
                self.stdout.write('\nÚltimos movimientos:')
                for movement in recent_movements:
                    self.stdout.write(f'  {movement.created_at.strftime("%Y-%m-%d %H:%M")} - '
                                    f'{movement.get_movement_type_display()}: {movement.quantity} '
                                    f'({movement.reference})')
            else:
                self.stdout.write('No hay movimientos registrados')
                
        except Stock.DoesNotExist:
            self.stdout.write(self.style.ERROR('ERROR: No hay registro de stock para este producto'))

    def check_all_inventory(self, warehouse):
        """Verifica el inventario general"""
        self.stdout.write(f'\n--- Inventario General en {warehouse.name} ---')
        
        # Productos con stock
        stocks = Stock.objects.filter(warehouse=warehouse).order_by('product__name')
        total_products = stocks.count()
        low_stock_products = stocks.filter(quantity__lte=F('min_stock')).count()
        out_of_stock_products = stocks.filter(quantity=0).count()
        
        self.stdout.write(f'Total productos con stock: {total_products}')
        self.stdout.write(f'Productos con stock bajo: {low_stock_products}')
        self.stdout.write(f'Productos sin stock: {out_of_stock_products}')
        
        # Top 10 productos con más stock
        top_stocks = stocks.order_by('-quantity')[:10]
        if top_stocks:
            self.stdout.write('\nTop 10 productos con más stock:')
            for stock in top_stocks:
                status = 'WARNING' if stock.is_low_stock else 'OK'
                self.stdout.write(f'  [{status}] {stock.product.name}: {stock.quantity} unidades')

    def check_purchase_integration(self, warehouse):
        """Verifica la integración con el módulo de compras"""
        self.stdout.write(f'\n--- Integración con Compras ---')
        
        # Compras recibidas en los últimos 30 días
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_purchases = Purchase.objects.filter(
            status='received',
            received_date__gte=thirty_days_ago
        )
        
        self.stdout.write(f'Compras recibidas (últimos 30 días): {recent_purchases.count()}')
        
        # Verificar que los movimientos de stock coincidan con las compras
        for purchase in recent_purchases[:5]:  # Solo las primeras 5
            self.stdout.write(f'\nCompra #{purchase.purchase_number}:')
            for item in purchase.items.all():
                try:
                    stock = Stock.objects.get(product=item.product, warehouse=warehouse)
                    movements = StockMovement.objects.filter(
                        product=item.product,
                        warehouse=warehouse,
                        reference=f'Compra #{purchase.purchase_number}'
                    )
                    
                    if movements.exists():
                        total_movement = movements.aggregate(total=Sum('quantity'))['total']
                        self.stdout.write(f'  [OK] {item.product.name}: {item.quantity} recibidos, '
                                        f'{total_movement} en movimientos')
                    else:
                        self.stdout.write(f'  [ERROR] {item.product.name}: {item.quantity} recibidos, '
                                        f'pero no hay movimientos registrados')
                except Stock.DoesNotExist:
                    self.stdout.write(f'  [ERROR] {item.product.name}: Sin registro de stock')
