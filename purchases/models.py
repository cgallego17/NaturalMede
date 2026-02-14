from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
from decimal import Decimal


class Supplier(models.Model):
    """Proveedor de productos"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Persona de contacto")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="NIT/RUT")
    payment_terms = models.CharField(max_length=100, blank=True, verbose_name="Términos de pago")
    notes = models.TextField(blank=True, verbose_name="Notas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_purchases(self):
        """Total de compras realizadas a este proveedor"""
        return self.purchases.aggregate(total=models.Sum('total'))['total'] or Decimal('0')

    def get_purchase_count(self):
        """Obtener el número de compras realizadas a este proveedor"""
        return self.purchases.count()
    
    @property
    def purchase_count(self):
        """Número de compras realizadas a este proveedor (propiedad de solo lectura)"""
        return self.purchases.count()


class Purchase(models.Model):
    """Compra de productos"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('received', 'Recibida'),
        ('cancelled', 'Cancelada'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagado'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases', verbose_name="Proveedor")
    purchase_number = models.CharField(max_length=20, unique=True, verbose_name="Número de compra")
    order_date = models.DateField(verbose_name="Fecha de orden")
    expected_delivery = models.DateField(blank=True, null=True, verbose_name="Fecha esperada de entrega")
    received_date = models.DateField(blank=True, null=True, verbose_name="Fecha de recepción")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Estado de pago")
    
    # Totales
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Subtotal")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="IVA")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Descuento")
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Costo de envío")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Total")
    
    # Información adicional
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-created_at']

    def __str__(self):
        if hasattr(self, 'supplier') and self.supplier:
            return f"Compra #{self.purchase_number} - {self.supplier.name}"
        else:
            return f"Compra #{self.purchase_number} - Sin proveedor"

    def save(self, *args, **kwargs):
        if not self.purchase_number:
            self.purchase_number = self.generate_purchase_number()
        super().save(*args, **kwargs)

    def generate_purchase_number(self):
        """Generar número de compra único"""
        from datetime import datetime
        today = datetime.now()
        year = today.year
        month = today.month
        
        # Contar compras del mes actual
        count = Purchase.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count() + 1
        
        return f"COMP-{year}{month:02d}-{count:04d}"

    def recalculate_totals(self):
        items = self.items.all()
        subtotal = sum((item.subtotal for item in items), Decimal('0.00'))
        tax_amount = sum((item.tax_amount for item in items), Decimal('0.00'))
        discount_amount = sum((item.discount_amount for item in items), Decimal('0.00'))
        total = subtotal - discount_amount + tax_amount + (self.shipping_cost or Decimal('0.00'))

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.discount_amount = discount_amount
        self.total = total
        self.save(update_fields=['subtotal', 'tax_amount', 'discount_amount', 'total'])

    @property
    def items_count(self):
        """Número de items en la compra"""
        return self.items.count()

    @property
    def total_quantity(self):
        """Cantidad total de productos"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0


class PurchaseItem(models.Model):
    """Item de una compra"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items', verbose_name="Compra")
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo unitario")
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'), verbose_name="% IVA")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="% Descuento")
    
    # Totales calculados
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="IVA")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Descuento")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total")

    class Meta:
        verbose_name = "Item de compra"
        verbose_name_plural = "Items de compra"
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} unidades"

    def save(self, *args, **kwargs):
        # Calcular totales
        self.subtotal = self.unit_cost * self.quantity
        self.discount_amount = self.subtotal * (self.discount_percentage / Decimal('100'))
        self.tax_amount = (self.subtotal - self.discount_amount) * (self.tax_percentage / Decimal('100'))
        self.total = self.subtotal - self.discount_amount + self.tax_amount
        
        super().save(*args, **kwargs)
        
        # Actualizar totales de la compra solo si ya tiene una compra asignada
        if self.purchase_id:
            self.update_purchase_totals()

    def update_purchase_totals(self):
        """Actualizar totales de la compra padre"""
        purchase = self.purchase
        items = purchase.items.all()
        
        purchase.subtotal = sum(item.subtotal for item in items)
        purchase.tax_amount = sum(item.tax_amount for item in items)
        purchase.discount_amount = sum(item.discount_amount for item in items)
        purchase.total = purchase.subtotal - purchase.discount_amount + purchase.tax_amount + purchase.shipping_cost
        
        purchase.save(update_fields=['subtotal', 'tax_amount', 'discount_amount', 'total'])


class PurchaseReceipt(models.Model):
    """Recibo de compra"""
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='receipt', verbose_name="Compra")
    receipt_number = models.CharField(max_length=50, verbose_name="Número de recibo")
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Recibido por")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Recibido en")
    notes = models.TextField(blank=True, verbose_name="Notas de recepción")

    class Meta:
        verbose_name = "Recibo de compra"
        verbose_name_plural = "Recibos de compra"

    def __str__(self):
        return f"Recibo #{self.receipt_number} - {self.purchase.purchase_number}"


@receiver(post_delete, sender=PurchaseItem)
def _purchaseitem_post_delete_recalculate_totals(sender, instance, **kwargs):
    purchase = getattr(instance, 'purchase', None)
    if purchase and purchase.pk:
        purchase.recalculate_totals()