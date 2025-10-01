from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from catalog.models import Product, Category, Brand
from customers.models import Customer
from orders.models import Order, OrderItem
from pos.models import POSSale, POSSaleItem, POSSession
from inventory.models import Stock, Warehouse


class Command(BaseCommand):
    help = 'Agrega datos demo específicos para reportes'

    def handle(self, *args, **options):
        self.stdout.write('Agregando datos demo para reportes...')
        
        # Usar la primera sesión POS disponible
        session = POSSession.objects.first()
        if not session:
            session = POSSession.objects.create(
                opening_cash=Decimal('100000'),
                closing_cash=Decimal('100000'),
                opened_at=timezone.now() - timedelta(days=1),
                closed_at=timezone.now() - timedelta(days=1),
                is_active=False
            )
        
        # Obtener productos existentes
        products = list(Product.objects.all())
        if not products:
            self.stdout.write('No hay productos disponibles.')
            return
        
        # Crear algunas ventas POS demo adicionales
        self.create_pos_sales_demo(session, products)
        
        # Crear algunas órdenes web demo adicionales
        self.create_web_orders_demo(products)
        
        self.stdout.write(
            self.style.SUCCESS('Datos demo para reportes agregados exitosamente!')
        )

    def create_pos_sales_demo(self, session, products):
        """Crear ventas POS demo adicionales"""
        # Crear 10 ventas POS adicionales
        for i in range(10):
            days_ago = random.randint(1, 30)
            sale_date = timezone.now() - timedelta(days=days_ago)
            
            # Crear venta POS
            sale = POSSale.objects.create(
                session=session,
                customer=None,
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
                    unit_price=price,
                    iva_percentage=Decimal('19.00'),
                    discount_percentage=Decimal('0.00'),
                    subtotal=total,
                    iva_amount=total * Decimal('0.19'),
                    discount_amount=Decimal('0.00'),
                    total=total * Decimal('1.19')
                )
                
                sale_total += total * Decimal('1.19')
            
            # Actualizar totales de la venta
            iva = sale_total * Decimal('0.19')
            sale.subtotal = sale_total
            sale.iva_amount = iva
            sale.total = sale_total + iva
            sale.save()

    def create_web_orders_demo(self, products):
        """Crear órdenes web demo adicionales"""
        # Obtener o crear cliente demo
        user, created = User.objects.get_or_create(
            username='demo_reports_user',
            defaults={
                'email': 'demo_reports@example.com',
                'first_name': 'Usuario',
                'last_name': 'Reportes'
            }
        )
        
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={
                'customer_type': 'normal',
                'phone': '9876543210',
                'document_type': 'cedula',
                'document_number': '87654321'
            }
        )
        
        # Crear 5 órdenes web adicionales
        for i in range(5):
            days_ago = random.randint(1, 30)
            order_date = timezone.now() - timedelta(days=days_ago)
            
            # Crear orden
            order = Order.objects.create(
                customer=customer,
                status=random.choice(['paid', 'shipped', 'delivered']),
                payment_method='bank_transfer',
                subtotal=Decimal('0'),
                iva_amount=Decimal('0'),
                shipping_cost=Decimal('5000'),
                total=Decimal('0'),
                shipping_address='Dirección demo reportes 456',
                shipping_city='Medellín',
                shipping_phone='9876543210',
                created_at=order_date,
                updated_at=order_date
            )
            
            # Agregar items aleatorios
            num_items = random.randint(1, 3)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            order_total = Decimal('0')
            for product in selected_products:
                quantity = random.randint(1, 2)
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
                
                order_total += total * Decimal('1.19')
            
            # Actualizar totales de la orden
            iva = order_total * Decimal('0.19')
            order.subtotal = order_total
            order.iva_amount = iva
            order.total = order_total + order.shipping_cost
            order.save()
