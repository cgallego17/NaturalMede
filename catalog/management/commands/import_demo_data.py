from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import Category, Brand, Product, ProductImage
from inventory.models import Warehouse, Stock
from customers.models import Customer
from orders.models import ShippingRate
from decimal import Decimal
import os


class Command(BaseCommand):
    help = 'Importa datos de ejemplo para la tienda naturista NaturalMede'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando importación de datos de ejemplo...')
        
        # Crear superusuario si no existe
        self.create_superuser()
        
        # Crear categorías
        self.create_categories()
        
        # Crear marcas
        self.create_brands()
        
        # Crear bodegas
        self.create_warehouses()
        
        # Crear productos
        self.create_products()
        
        # Crear tarifas de envío
        self.create_shipping_rates()
        
        # Crear cliente de ejemplo
        self.create_sample_customer()
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos de ejemplo importados exitosamente!')
        )

    def create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@naturalmede.com',
                password='admin123',
                first_name='Administrador',
                last_name='NaturalMede'
            )
            self.stdout.write('+ Superusuario creado: admin/admin123')

    def create_categories(self):
        categories_data = [
            {
                'name': 'Suplementos',
                'slug': 'suplementos',
                'description': 'Vitaminas, minerales y suplementos nutricionales para una vida saludable.'
            },
            {
                'name': 'Productos Orgánicos',
                'slug': 'productos-organicos',
                'description': 'Alimentos y productos 100% orgánicos certificados.'
            },
            {
                'name': 'Cuidado Personal',
                'slug': 'cuidado-personal',
                'description': 'Productos naturales para el cuidado de la piel y el cabello.'
            },
            {
                'name': 'Tés e Infusiones',
                'slug': 'tes-infusiones',
                'description': 'Tés medicinales, infusiones y bebidas naturales.'
            },
            {
                'name': 'Aromaterapia',
                'slug': 'aromaterapia',
                'description': 'Aceites esenciales, velas y productos de aromaterapia.'
            },
            {
                'name': 'Medicina Natural',
                'slug': 'medicina-natural',
                'description': 'Productos homeopáticos y medicina natural.'
            }
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'+ Categoria creada: {category.name}')

    def create_brands(self):
        brands_data = [
            {
                'name': 'Nature\'s Way',
                'slug': 'natures-way',
                'description': 'Líder mundial en suplementos naturales de alta calidad.'
            },
            {
                'name': 'Organic Valley',
                'slug': 'organic-valley',
                'description': 'Productos orgánicos certificados para toda la familia.'
            },
            {
                'name': 'Weleda',
                'slug': 'weleda',
                'description': 'Cosméticos naturales y cuidado personal biodinámico.'
            },
            {
                'name': 'Twinings',
                'slug': 'twinings',
                'description': 'Tés e infusiones de la más alta calidad desde 1706.'
            },
            {
                'name': 'Young Living',
                'slug': 'young-living',
                'description': 'Aceites esenciales puros y productos de aromaterapia.'
            },
            {
                'name': 'Boiron',
                'slug': 'boiron',
                'description': 'Medicina homeopática de confianza desde 1932.'
            }
        ]
        
        for brand_data in brands_data:
            brand, created = Brand.objects.get_or_create(
                slug=brand_data['slug'],
                defaults=brand_data
            )
            if created:
                self.stdout.write(f'+ Marca creada: {brand.name}')

    def create_warehouses(self):
        warehouses_data = [
            {
                'name': 'Bodega Principal',
                'code': 'BP001',
                'address': 'Carrera 15 #93-47, Bogotá',
                'city': 'Bogotá',
                'phone': '+57 1 234 5678',
                'email': 'bodega@naturalmede.com',
                'is_main': True
            },
            {
                'name': 'Bodega Medellín',
                'code': 'BM001',
                'address': 'Calle 50 #46-42, Medellín',
                'city': 'Medellín',
                'phone': '+57 4 567 8901',
                'email': 'medellin@naturalmede.com',
                'is_main': False
            }
        ]
        
        for wh_data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=wh_data['code'],
                defaults=wh_data
            )
            if created:
                self.stdout.write(f'+ Bodega creada: {warehouse.name}')

    def create_products(self):
        products_data = [
            # Suplementos
            {
                'name': 'Vitamina C 1000mg',
                'slug': 'vitamina-c-1000mg',
                'description': 'Vitamina C de alta potencia para fortalecer el sistema inmunológico. Contiene 1000mg de ácido ascórbico por cápsula.',
                'short_description': 'Vitamina C de alta potencia para el sistema inmunológico',
                'sku': 'VITC1000',
                'barcode': '1234567890123',
                'category_slug': 'suplementos',
                'brand_slug': 'natures-way',
                'price': Decimal('45000'),
                'cost_price': Decimal('25000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.1'),
                'dimensions': '8x5x2 cm',
                'is_featured': True
            },
            {
                'name': 'Omega 3 1000mg',
                'slug': 'omega-3-1000mg',
                'description': 'Aceite de pescado rico en ácidos grasos Omega 3 EPA y DHA. Beneficioso para la salud cardiovascular y cerebral.',
                'short_description': 'Aceite de pescado rico en Omega 3 EPA y DHA',
                'sku': 'OMG31000',
                'barcode': '1234567890124',
                'category_slug': 'suplementos',
                'brand_slug': 'natures-way',
                'price': Decimal('85000'),
                'cost_price': Decimal('45000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.15'),
                'dimensions': '10x6x3 cm',
                'is_featured': True
            },
            {
                'name': 'Magnesio 400mg',
                'slug': 'magnesio-400mg',
                'description': 'Suplemento de magnesio para el funcionamiento normal de los músculos y el sistema nervioso.',
                'short_description': 'Suplemento de magnesio para músculos y nervios',
                'sku': 'MAG400',
                'barcode': '1234567890125',
                'category_slug': 'suplementos',
                'brand_slug': 'natures-way',
                'price': Decimal('35000'),
                'cost_price': Decimal('18000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.08'),
                'dimensions': '7x4x2 cm',
                'is_featured': False
            },
            
            # Productos Orgánicos
            {
                'name': 'Miel de Abeja Orgánica',
                'slug': 'miel-abeja-organica',
                'description': 'Miel 100% orgánica certificada, recolectada de colmenas en bosques nativos. Rica en antioxidantes y enzimas naturales.',
                'short_description': 'Miel 100% orgánica certificada',
                'sku': 'MIEL500',
                'barcode': '1234567890126',
                'category_slug': 'productos-organicos',
                'brand_slug': 'organic-valley',
                'price': Decimal('25000'),
                'cost_price': Decimal('12000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.5'),
                'dimensions': '8x8x8 cm',
                'is_featured': True
            },
            {
                'name': 'Aceite de Coco Virgen',
                'slug': 'aceite-coco-virgen',
                'description': 'Aceite de coco virgen extraído en frío. Ideal para cocinar, cuidado de la piel y cabello.',
                'short_description': 'Aceite de coco virgen extraído en frío',
                'sku': 'ACOC500',
                'barcode': '1234567890127',
                'category_slug': 'productos-organicos',
                'brand_slug': 'organic-valley',
                'price': Decimal('18000'),
                'cost_price': Decimal('9000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.5'),
                'dimensions': '6x6x12 cm',
                'is_featured': False
            },
            
            # Cuidado Personal
            {
                'name': 'Crema Hidratante Natural',
                'slug': 'crema-hidratante-natural',
                'description': 'Crema hidratante con ingredientes 100% naturales. Hidrata y nutre la piel sin químicos agresivos.',
                'short_description': 'Crema hidratante con ingredientes naturales',
                'sku': 'CREM200',
                'barcode': '1234567890128',
                'category_slug': 'cuidado-personal',
                'brand_slug': 'weleda',
                'price': Decimal('65000'),
                'cost_price': Decimal('35000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.2'),
                'dimensions': '6x6x8 cm',
                'is_featured': True
            },
            {
                'name': 'Shampoo Natural',
                'slug': 'shampoo-natural',
                'description': 'Shampoo sin sulfatos con extractos de plantas. Limpia suavemente sin dañar el cabello.',
                'short_description': 'Shampoo sin sulfatos con extractos de plantas',
                'sku': 'SHAM400',
                'barcode': '1234567890129',
                'category_slug': 'cuidado-personal',
                'brand_slug': 'weleda',
                'price': Decimal('45000'),
                'cost_price': Decimal('22000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.4'),
                'dimensions': '8x4x15 cm',
                'is_featured': False
            },
            
            # Tés e Infusiones
            {
                'name': 'Té Verde Earl Grey',
                'slug': 'te-verde-earl-grey',
                'description': 'Té verde aromatizado con bergamota. Rico en antioxidantes y con un sabor cítrico único.',
                'short_description': 'Té verde aromatizado con bergamota',
                'sku': 'TEGR100',
                'barcode': '1234567890130',
                'category_slug': 'tes-infusiones',
                'brand_slug': 'twinings',
                'price': Decimal('15000'),
                'cost_price': Decimal('8000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.1'),
                'dimensions': '15x10x5 cm',
                'is_featured': True
            },
            {
                'name': 'Infusión de Manzanilla',
                'slug': 'infusion-manzanilla',
                'description': 'Infusión relajante de manzanilla. Ideal para calmar y relajar antes de dormir.',
                'short_description': 'Infusión relajante de manzanilla',
                'sku': 'MANZ100',
                'barcode': '1234567890131',
                'category_slug': 'tes-infusiones',
                'brand_slug': 'twinings',
                'price': Decimal('12000'),
                'cost_price': Decimal('6000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.08'),
                'dimensions': '15x10x5 cm',
                'is_featured': False
            },
            
            # Aromaterapia
            {
                'name': 'Aceite Esencial de Lavanda',
                'slug': 'aceite-lavanda',
                'description': 'Aceite esencial puro de lavanda. Relajante y calmante, ideal para aromaterapia y masajes.',
                'short_description': 'Aceite esencial puro de lavanda',
                'sku': 'LAV10',
                'barcode': '1234567890132',
                'category_slug': 'aromaterapia',
                'brand_slug': 'young-living',
                'price': Decimal('75000'),
                'cost_price': Decimal('40000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.01'),
                'dimensions': '3x3x8 cm',
                'is_featured': True
            },
            {
                'name': 'Vela de Soja Aromática',
                'slug': 'vela-soja-aromatica',
                'description': 'Vela de cera de soja con aceites esenciales. Quema limpia y duradera con fragancia natural.',
                'short_description': 'Vela de cera de soja con aceites esenciales',
                'sku': 'VELA200',
                'barcode': '1234567890133',
                'category_slug': 'aromaterapia',
                'brand_slug': 'young-living',
                'price': Decimal('35000'),
                'cost_price': Decimal('18000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.3'),
                'dimensions': '8x8x8 cm',
                'is_featured': False
            },
            
            # Medicina Natural
            {
                'name': 'Arnica Gel',
                'slug': 'arnica-gel',
                'description': 'Gel de árnica para aliviar dolores musculares y articulares. Producto homeopático de uso tópico.',
                'short_description': 'Gel de árnica para dolores musculares',
                'sku': 'ARNI50',
                'barcode': '1234567890134',
                'category_slug': 'medicina-natural',
                'brand_slug': 'boiron',
                'price': Decimal('28000'),
                'cost_price': Decimal('14000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.1'),
                'dimensions': '4x4x12 cm',
                'is_featured': True
            },
            {
                'name': 'Echinacea 500mg',
                'slug': 'echinacea-500mg',
                'description': 'Cápsulas de equinácea para fortalecer el sistema inmunológico. Extracto estandarizado de alta calidad.',
                'short_description': 'Cápsulas de equinácea para el sistema inmunológico',
                'sku': 'ECHI500',
                'barcode': '1234567890135',
                'category_slug': 'medicina-natural',
                'brand_slug': 'boiron',
                'price': Decimal('42000'),
                'cost_price': Decimal('21000'),
                'iva_percentage': Decimal('19.00'),
                'weight': Decimal('0.12'),
                'dimensions': '8x5x2 cm',
                'is_featured': False
            }
        ]
        
        for prod_data in products_data:
            category = Category.objects.get(slug=prod_data['category_slug'])
            brand = Brand.objects.get(slug=prod_data['brand_slug'])
            
            product, created = Product.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'slug': prod_data['slug'],
                    'description': prod_data['description'],
                    'short_description': prod_data['short_description'],
                    'category': category,
                    'brand': brand,
                    'barcode': prod_data['barcode'],
                    'price': prod_data['price'],
                    'cost_price': prod_data['cost_price'],
                    'iva_percentage': prod_data['iva_percentage'],
                    'weight': prod_data['weight'],
                    'dimensions': prod_data['dimensions'],
                    'is_featured': prod_data['is_featured']
                }
            )
            
            if created:
                self.stdout.write(f'+ Producto creado: {product.name}')
                
                # Crear stock en bodega principal
                main_warehouse = Warehouse.objects.get(is_main=True)
                Stock.objects.create(
                    product=product,
                    warehouse=main_warehouse,
                    quantity=50,  # Stock inicial
                    min_stock=10,
                    max_stock=100
                )
                
                # Crear stock en bodega secundaria
                secondary_warehouse = Warehouse.objects.get(is_main=False)
                Stock.objects.create(
                    product=product,
                    warehouse=secondary_warehouse,
                    quantity=20,
                    min_stock=5,
                    max_stock=50
                )

    def create_shipping_rates(self):
        shipping_rates_data = [
            {'city': 'Bogotá', 'min_weight': 0, 'max_weight': 1, 'cost': Decimal('8000'), 'estimated_days': 1},
            {'city': 'Bogotá', 'min_weight': 1, 'max_weight': 3, 'cost': Decimal('12000'), 'estimated_days': 1},
            {'city': 'Bogotá', 'min_weight': 3, 'max_weight': 5, 'cost': Decimal('15000'), 'estimated_days': 1},
            {'city': 'Medellín', 'min_weight': 0, 'max_weight': 1, 'cost': Decimal('10000'), 'estimated_days': 2},
            {'city': 'Medellín', 'min_weight': 1, 'max_weight': 3, 'cost': Decimal('15000'), 'estimated_days': 2},
            {'city': 'Medellín', 'min_weight': 3, 'max_weight': 5, 'cost': Decimal('20000'), 'estimated_days': 2},
            {'city': 'Cali', 'min_weight': 0, 'max_weight': 1, 'cost': Decimal('12000'), 'estimated_days': 3},
            {'city': 'Cali', 'min_weight': 1, 'max_weight': 3, 'cost': Decimal('18000'), 'estimated_days': 3},
            {'city': 'Cali', 'min_weight': 3, 'max_weight': 5, 'cost': Decimal('25000'), 'estimated_days': 3},
            {'city': 'Barranquilla', 'min_weight': 0, 'max_weight': 1, 'cost': Decimal('15000'), 'estimated_days': 4},
            {'city': 'Barranquilla', 'min_weight': 1, 'max_weight': 3, 'cost': Decimal('22000'), 'estimated_days': 4},
            {'city': 'Barranquilla', 'min_weight': 3, 'max_weight': 5, 'cost': Decimal('30000'), 'estimated_days': 4},
        ]
        
        for rate_data in shipping_rates_data:
            rate, created = ShippingRate.objects.get_or_create(
                city=rate_data['city'],
                min_weight=rate_data['min_weight'],
                max_weight=rate_data['max_weight'],
                defaults=rate_data
            )
            if created:
                self.stdout.write(f'+ Tarifa de envio creada: {rate.city} - {rate.min_weight}-{rate.max_weight}kg')

    def create_sample_customer(self):
        # Crear usuario de ejemplo
        user, created = User.objects.get_or_create(
            username='cliente_ejemplo',
            defaults={
                'email': 'cliente@ejemplo.com',
                'first_name': 'María',
                'last_name': 'González',
                'is_active': True
            }
        )
        
        if created:
            user.set_password('cliente123')
            user.save()
        
        # Crear cliente
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={
                'customer_type': 'normal',
                'document_type': 'CC',
                'document_number': '12345678',
                'phone': '+57 300 123 4567',
                'address': 'Calle 123 #45-67',
                'city': 'Bogotá',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('+ Cliente de ejemplo creado: cliente_ejemplo/cliente123')

