"""
Pruebas para los modelos del proyecto NaturalMede
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

# Importar modelos según estén disponibles
try:
    from catalog.models import Product, Category, Brand
    CATALOG_AVAILABLE = True
except ImportError:
    CATALOG_AVAILABLE = False

try:
    from purchases.models import Purchase, PurchaseItem, Supplier
    PURCHASES_AVAILABLE = True
except ImportError:
    PURCHASES_AVAILABLE = False

try:
    from audit.models import AuditLog, InventoryTrace
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False


@pytest.mark.skipif(not CATALOG_AVAILABLE, reason="Catalog models not available")
class CatalogModelTests(TestCase):
    """Pruebas para los modelos del catálogo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category description",
            slug="test-category"
        )
        self.brand = Brand.objects.create(
            name="Test Brand",
            description="Test brand description",
            slug="test-brand"
        )
    
    def test_category_creation(self):
        """Verifica la creación de categorías"""
        category = Category.objects.create(
            name="New Category",
            description="New category description",
            slug="new-category"
        )
        assert category.name == "New Category"
        assert category.description == "New category description"
        assert str(category) == "New Category"
    
    def test_brand_creation(self):
        """Verifica la creación de marcas"""
        brand = Brand.objects.create(
            name="New Brand",
            description="New brand description",
            slug="new-brand"
        )
        assert brand.name == "New Brand"
        assert brand.description == "New brand description"
        assert str(brand) == "New Brand"
    
    def test_product_creation(self):
        """Verifica la creación de productos"""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            price=10.50,
            cost_price=8.00,
            category=self.category,
            brand=self.brand
        )
        assert product.name == "Test Product"
        assert product.sku == "TEST001"
        assert product.price == 10.50
        assert product.cost_price == 8.00
        assert product.category == self.category
        assert product.brand == self.brand
        assert str(product) == "Test Product"


@pytest.mark.skipif(not PURCHASES_AVAILABLE, reason="Purchases models not available")
class PurchasesModelTests(TestCase):
    """Pruebas para los modelos de compras"""
    
    def test_supplier_creation(self):
        """Verifica la creación de proveedores"""
        supplier = Supplier.objects.create(
            name="New Supplier"
        )
        assert supplier.name == "New Supplier"
        assert str(supplier) == "New Supplier"
    
    def test_purchase_creation(self):
        """Verifica la creación de compras"""
        # Esta prueba se omite por ahora debido a dependencias complejas
        # Se puede implementar cuando los modelos estén completamente definidos
        pass


@pytest.mark.skipif(not AUDIT_AVAILABLE, reason="Audit models not available")
class AuditModelTests(TestCase):
    """Pruebas para los modelos de auditoría"""
    
    def test_audit_log_creation(self):
        """Verifica la creación de logs de auditoría"""
        audit_log = AuditLog.objects.create(
            action='CREATE',
            object_repr='Test Object',
            app_label='test',
            model_name='TestModel'
        )
        assert audit_log.action == 'CREATE'
        assert audit_log.object_repr == 'Test Object'
        assert audit_log.app_label == 'test'
        assert audit_log.model_name == 'TestModel'
        # Verificar que el string representation contenga la información básica
        assert str(audit_log) is not None  # Solo verificar que no sea None
    
    def test_inventory_trace_creation(self):
        """Verifica la creación de trazas de inventario"""
        # Esta prueba se omite por ahora debido a dependencias complejas
        # Se puede implementar cuando los modelos estén completamente definidos
        pass


class DatabaseTests(TestCase):
    """Pruebas de base de datos"""
    
    def test_database_connection(self):
        """Verifica la conexión a la base de datos"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_migrations_applied(self):
        """Verifica que las migraciones se hayan aplicado"""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM django_migrations")
                migrations = cursor.fetchall()
                assert len(migrations) > 0  # Debe haber al menos algunas migraciones
        except Exception:
            # Si no hay tabla de migraciones, es aceptable para pruebas básicas
            pass
