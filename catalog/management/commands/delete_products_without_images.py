from django.core.management.base import BaseCommand
from catalog.models import Product, ProductImage


class Command(BaseCommand):
    help = 'Elimina productos que no tienen imágenes asociadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué productos se eliminarían sin eliminarlos realmente',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma la eliminación de productos sin imágenes',
        )

    def handle(self, *args, **options):
        # Obtener todos los productos
        all_products = Product.objects.all()
        
        # Filtrar productos sin imágenes
        products_without_images = []
        for product in all_products:
            if not product.images.exists():
                products_without_images.append(product)
        
        if not products_without_images:
            self.stdout.write(
                self.style.SUCCESS('✓ No hay productos sin imágenes en la base de datos.')
            )
            return
        
        # Mostrar productos que se eliminarían
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠ Se encontraron {len(products_without_images)} productos sin imágenes:\n'
            )
        )
        
        for product in products_without_images:
            self.stdout.write(
                f'  - ID: {product.id} | SKU: {product.sku} | Nombre: {product.name}'
            )
        
        # Si es dry-run, solo mostrar
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ Modo dry-run: No se eliminaron productos. '
                    f'Usa --confirm para eliminar realmente.'
                )
            )
            return
        
        # Si no está confirmado, pedir confirmación
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    f'\n⚠ ADVERTENCIA: Se eliminarán {len(products_without_images)} productos.\n'
                    f'Para confirmar, ejecuta el comando con --confirm'
                )
            )
            return
        
        # Eliminar productos
        deleted_count = 0
        for product in products_without_images:
            product_name = product.name
            product_sku = product.sku
            product.delete()
            deleted_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Eliminado: {product_name} (SKU: {product_sku})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado. Se eliminaron {deleted_count} productos sin imágenes.'
            )
        )



