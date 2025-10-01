import random
from datetime import timedelta, datetime, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from customers.models import Customer
from orders.models import Order, OrderItem
from catalog.models import Product, Category, Brand
from pos.models import POSSale, POSSaleItem, POSSession
from inventory.models import Warehouse, Stock

class Command(BaseCommand):
    help = 'Agrega datos demo específicos para reportes'

    def handle(self, *args, **options):
        self.stdout.write('Agregando datos demo para reportes...')

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No hay usuarios. Por favor, crea un superusuario primero.'))
            return

        customer = Customer.objects.first()
        if not customer:
            self.stdout.write(self.style.ERROR('No hay clientes. Por favor, crea un cliente primero.'))
            return

        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR('No hay productos disponibles. Por favor, crea algunos productos primero.'))
            return

        # Asegurar que haya una sesión POS activa o crear una
        warehouse = Warehouse.objects.first()
        if not warehouse:
            self.stdout.write(self.style.ERROR('No hay bodegas disponibles. Por favor, crea una bodega primero.'))
            return
            
        session = POSSession.objects.filter(status='open').first()
        if not session:
            session = POSSession.objects.create(
                opening_cash=Decimal('100000'),
                user=user,
                warehouse=warehouse,
                status='open'
            )
            self.stdout.write(self.style.WARNING('No se encontró sesión POS activa, se creó una nueva.'))

        today = timezone.now().date()

        # Crear ventas para los últimos 30 días
        for i in range(30):
            date = today - timedelta(days=i)
            
            # Crear ventas POS (más frecuentes)
            num_pos_sales = random.randint(2, 5)
            for _ in range(num_pos_sales):
                sale_total = Decimal('0')
                sale = POSSale.objects.create(
                    session=session,
                    customer=customer,
                    subtotal=Decimal('0'),
                    iva_amount=Decimal('0'),
                    discount_amount=Decimal('0'),
                    total=Decimal('0'),
                    payment_method=random.choice(['cash', 'card']),
                    created_at=timezone.make_aware(datetime.combine(date, time(random.randint(9, 17), random.randint(0, 59)))),
                    updated_at=timezone.make_aware(datetime.combine(date, time(random.randint(9, 17), random.randint(0, 59))))
                )
                num_items = random.randint(1, 4)
                selected_products = random.sample(products, min(num_items, len(products)))
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    price = product.price
                    total_item = price * quantity
                    POSSaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=price,
                        iva_percentage=Decimal('19.00'),
                        discount_percentage=Decimal('0.00'),
                        subtotal=total_item,
                        iva_amount=total_item * Decimal('0.19'),
                        total=total_item * Decimal('1.19')
                    )
                    sale_total += total_item * Decimal('1.19')
                sale.subtotal = sale_total / Decimal('1.19')
                sale.iva_amount = sale_total - sale.subtotal
                sale.total = sale_total
                sale.save()

            # Crear órdenes web (menos frecuentes)
            if random.random() < 0.3:  # 30% de probabilidad
                order_total = Decimal('0')
                order = Order.objects.create(
                    customer=customer,
                    status=random.choice(['paid', 'shipped', 'delivered']),
                    payment_method=random.choice(['credit_card', 'paypal']),
                    subtotal=Decimal('0'),
                    iva_amount=Decimal('0'),
                    shipping_cost=Decimal('5000'),
                    total=Decimal('0'),
                    shipping_address='Dirección demo',
                    shipping_city='Ciudad demo',
                    shipping_phone='1234567890',
                    created_at=timezone.make_aware(datetime.combine(date, time(random.randint(9, 17), random.randint(0, 59)))),
                    updated_at=timezone.make_aware(datetime.combine(date, time(random.randint(9, 17), random.randint(0, 59))))
                )
                num_items = random.randint(1, 3)
                selected_products = random.sample(products, min(num_items, len(products)))
                for product in selected_products:
                    quantity = random.randint(1, 2)
                    price = product.price
                    total_item = price * quantity
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=price,
                        iva_percentage=Decimal('19.00'),
                        subtotal=total_item,
                        iva_amount=total_item * Decimal('0.19'),
                        total=total_item * Decimal('1.19')
                    )
                    order_total += total_item * Decimal('1.19')
                order.subtotal = order_total / Decimal('1.19')
                order.iva_amount = order_total - order.subtotal
                order.total = order_total + order.shipping_cost
                order.save()

        self.stdout.write(self.style.SUCCESS('Datos demo para reportes agregados exitosamente!'))
