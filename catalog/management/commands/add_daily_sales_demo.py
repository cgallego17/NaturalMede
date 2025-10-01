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


class Command(BaseCommand):
    help = 'Agrega ventas demo específicas para los últimos 7 días'

    def handle(self, *args, **options):
        self.stdout.write('Agregando ventas demo para los últimos 7 días...')
        
        # Usar la primera sesión POS disponible
        session = POSSession.objects.first()
        if not session:
            session = POSSession.objects.create(
                opening_cash=Decimal('100000'),
                closing_cash=Decimal('100000'),
                opened_at=timezone.now() - timedelta(days=7),
                closed_at=timezone.now() - timedelta(days=7),
                is_active=False
            )
        
        # Obtener productos existentes
        products = list(Product.objects.all())
        if not products:
            self.stdout.write('No hay productos disponibles.')
            return
        
        # Obtener o crear cliente demo
        user, created = User.objects.get_or_create(
            username='daily_sales_demo_user',
            defaults={
                'email': 'daily_sales@example.com',
                'first_name': 'Usuario',
                'last_name': 'Ventas Diarias'
            }
        )
        
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={
                'customer_type': 'normal',
                'phone': '1111111111',
                'document_type': 'cedula',
                'document_number': '11111111'
            }
        )
        
        # Crear ventas para los últimos 7 días
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            
            # Crear 1-3 ventas POS por día
            num_pos_sales = random.randint(1, 3)
            for j in range(num_pos_sales):
                self.create_pos_sale(session, products, date)
            
            # Crear 1-2 órdenes web por día
            num_web_orders = random.randint(1, 2)
            for k in range(num_web_orders):
                self.create_web_order(customer, products, date)
        
        self.stdout.write(
            self.style.SUCCESS('Ventas demo para los últimos 7 días agregadas exitosamente!')
        )

    def create_pos_sale(self, session, products, date):
        """Crear una venta POS"""
        sale = POSSale.objects.create(
            session=session,
            customer=None,
            subtotal=Decimal('0'),
            iva_amount=Decimal('0'),
            discount_amount=Decimal('0'),
            total=Decimal('0'),
            created_at=date
        )
        
        # Agregar 1-2 productos
        num_items = random.randint(1, 2)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        sale_total = Decimal('0')
        for product in selected_products:
            quantity = random.randint(1, 3)
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
        
        # Actualizar totales
        iva = sale_total * Decimal('0.19')
        sale.subtotal = sale_total
        sale.iva_amount = iva
        sale.total = sale_total
        sale.save()

    def create_web_order(self, customer, products, date):
        """Crear una orden web"""
        order = Order.objects.create(
            customer=customer,
            status=random.choice(['paid', 'shipped', 'delivered']),
            payment_method='bank_transfer',
            subtotal=Decimal('0'),
            iva_amount=Decimal('0'),
            shipping_cost=Decimal('5000'),
            total=Decimal('0'),
            shipping_address='Dirección demo ventas diarias 789',
            shipping_city='Cali',
            shipping_phone='2222222222',
            created_at=date,
            updated_at=date
        )
        
        # Agregar 1-3 productos
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
        
        # Actualizar totales
        iva = order_total * Decimal('0.19')
        order.subtotal = order_total
        order.iva_amount = iva
        order.total = order_total + order.shipping_cost
        order.save()

