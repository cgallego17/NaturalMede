from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from catalog.models import Product, Category, Brand
from customers.models import Customer
from orders.models import Order, OrderItem
from pos.models import POSSale, POSSaleItem
from inventory.models import Stock, Warehouse


class Command(BaseCommand):
    help = 'Crea datos demo para reportes'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos demo...')
        
        # Crear usuario demo si no existe
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Usuario',
                'last_name': 'Demo'
            }
        )
        
        # Crear cliente demo
        import uuid
        demo_document = str(uuid.uuid4())[:8]  # Generar número único
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={
                'customer_type': 'normal',
                'phone': '1234567890',
                'document_type': 'cedula',
                'document_number': demo_document
            }
        )
        
        # Obtener productos existentes
        products = list(Product.objects.all())
        if not products:
            self.stdout.write('No hay productos disponibles. Creando productos demo...')
            self.create_demo_products()
            products = list(Product.objects.all())
        
        # Crear órdenes web demo (últimos 30 días)
        self.create_demo_web_orders(customer, products)
        
        # Las ventas POS ya existen, no necesitamos crear más
        
        self.stdout.write(
            self.style.SUCCESS('Datos demo creados exitosamente!')
        )

    def create_demo_products(self):
        """Crear productos demo si no existen"""
        # Crear categorías
        categories_data = [
            {'name': 'Vitaminas', 'description': 'Suplementos vitamínicos'},
            {'name': 'Minerales', 'description': 'Suplementos minerales'},
            {'name': 'Plantas Medicinales', 'description': 'Extractos herbales'},
            {'name': 'Proteínas', 'description': 'Suplementos proteicos'},
            {'name': 'Omega 3', 'description': 'Ácidos grasos esenciales'},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(cat)
        
        # Crear marcas
        brands_data = [
            {'name': 'NaturalMed', 'description': 'Marca premium'},
            {'name': 'HerbalLife', 'description': 'Productos herbales'},
            {'name': 'VitaMax', 'description': 'Vitaminas y minerales'},
            {'name': 'PureNature', 'description': 'Productos naturales'},
        ]
        
        brands = []
        for brand_data in brands_data:
            brand, created = Brand.objects.get_or_create(
                name=brand_data['name'],
                defaults={'description': brand_data['description']}
            )
            brands.append(brand)
        
        # Crear productos
        products_data = [
            {'name': 'Vitamina C 1000mg', 'price': 25000, 'category': categories[0], 'brand': brands[0]},
            {'name': 'Magnesio 400mg', 'price': 18000, 'category': categories[1], 'brand': brands[1]},
            {'name': 'Echinacea 500mg', 'price': 22000, 'category': categories[2], 'brand': brands[2]},
            {'name': 'Proteína Whey', 'price': 45000, 'category': categories[3], 'brand': brands[3]},
            {'name': 'Omega 3 1000mg', 'price': 32000, 'category': categories[4], 'brand': brands[0]},
            {'name': 'Vitamina D3', 'price': 28000, 'category': categories[0], 'brand': brands[1]},
            {'name': 'Zinc 50mg', 'price': 15000, 'category': categories[1], 'brand': brands[2]},
            {'name': 'Ginseng Coreano', 'price': 35000, 'category': categories[2], 'brand': brands[3]},
        ]
        
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'price': prod_data['price'],
                    'category': prod_data['category'],
                    'brand': prod_data['brand'],
                    'short_description': f'Suplemento {prod_data["name"]}',
                    'description': f'Descripción detallada de {prod_data["name"]}',
                    'is_active': True
                }
            )

    def create_demo_web_orders(self, customer, products):
        """Crear órdenes web demo"""
        # Crear órdenes en los últimos 30 días
        for i in range(15):  # 15 órdenes
            # Fecha aleatoria en los últimos 30 días
            days_ago = random.randint(1, 30)
            order_date = timezone.now() - timedelta(days=days_ago)
            
            # Crear orden
            order = Order.objects.create(
                customer=customer,
                status=random.choice(['paid', 'shipped', 'delivered']),
                payment_method='bank_transfer',
                subtotal=Decimal('0'),
                iva_amount=Decimal('0'),
                shipping_cost=Decimal('5000'),  # Costo de envío fijo
                total=Decimal('0'),
                shipping_address='Dirección demo 123',
                shipping_city='Bogotá',
                shipping_phone='1234567890',
                created_at=order_date,
                updated_at=order_date
            )
            
            # Agregar items aleatorios
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            order_total = Decimal('0')
            for product in selected_products:
                quantity = random.randint(1, 3)
                price = product.price
                total = price * quantity
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=price,
                    iva_percentage=Decimal('19.00'),
                    subtotal=total,
                    iva_amount=total * Decimal('0.19'),
                    total=total * Decimal('1.19')
                )
                
                order_total += total * Decimal('1.19')  # Incluir IVA
            
            # Actualizar totales de la orden
            iva = order_total * Decimal('0.19')  # 19% IVA
            order.subtotal = order_total
            order.iva_amount = iva
            order.total = order_total + iva + order.shipping_cost
            order.save()

    def create_demo_pos_sales(self, products):
        """Crear ventas POS demo adicionales si es necesario"""
        current_pos_count = POSSale.objects.count()
        if current_pos_count < 20:  # Si hay menos de 20 ventas POS
            # Crear ventas adicionales
            for i in range(10):
                days_ago = random.randint(1, 30)
                sale_date = timezone.now() - timedelta(days=days_ago)
                
                # Crear venta POS
                sale = POSSale.objects.create(
                    customer=None,  # Venta sin cliente específico
                    subtotal=Decimal('0'),
                    iva_amount=Decimal('0'),
                    discount_amount=Decimal('0'),
                    total=Decimal('0'),
                    created_at=sale_date
                )
                
                # Agregar items aleatorios
                num_items = random.randint(1, 3)
                selected_products = random.sample(products, min(num_items, len(products)))
                
                sale_total = Decimal('0')
                for product in selected_products:
                    quantity = random.randint(1, 2)
                    price = product.price
                    total = price * quantity
                    
                    POSSaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price,
                        total=total
                    )
                    
                    sale_total += total
                
                # Actualizar totales de la venta
                iva = sale_total * Decimal('0.19')
                sale.subtotal = sale_total
                sale.iva_amount = iva
                sale.total = sale_total + iva
                sale.save()
