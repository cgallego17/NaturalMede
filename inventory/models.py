from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Warehouse(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    code = models.CharField(max_length=10, unique=True, verbose_name="Código")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_main = models.BooleanField(default=False, verbose_name="Principal")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_main:
            # Solo puede haber una bodega principal
            Warehouse.objects.filter(is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class Stock(models.Model):
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Bodega")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Cantidad")
    min_stock = models.PositiveIntegerField(default=0, verbose_name="Stock mínimo")
    max_stock = models.PositiveIntegerField(default=0, verbose_name="Stock máximo")
    location = models.CharField(max_length=100, blank=True, verbose_name="Ubicación")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        unique_together = ['product', 'warehouse']
        ordering = ['product__name', 'warehouse__name']

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}: {self.quantity}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock

    @property
    def is_out_of_stock(self):
        return self.quantity == 0


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('transfer', 'Transferencia'),
        ('adjustment', 'Ajuste'),
        ('return', 'Devolución'),
    ]

    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Bodega")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name="Tipo de movimiento")
    quantity = models.IntegerField(verbose_name="Cantidad")  # Positivo para entrada, negativo para salida
    reference = models.CharField(max_length=100, blank=True, verbose_name="Referencia")
    notes = models.TextField(blank=True, verbose_name="Notas")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Usuario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name}: {self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el stock después de crear el movimiento
        self.update_stock()

    def update_stock(self):
        stock, created = Stock.objects.get_or_create(
            product=self.product,
            warehouse=self.warehouse,
            defaults={'quantity': 0}
        )
        stock.quantity += self.quantity
        stock.save()


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_transit', 'En tránsito'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_out', verbose_name="Bodega origen")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_in', verbose_name="Bodega destino")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    reference = models.CharField(max_length=100, verbose_name="Referencia")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Completada en")

    class Meta:
        verbose_name = "Transferencia de stock"
        verbose_name_plural = "Transferencias de stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"Transferencia {self.reference}: {self.from_warehouse.name} → {self.to_warehouse.name}"


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items', verbose_name="Transferencia")
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Item de transferencia"
        verbose_name_plural = "Items de transferencia"
        unique_together = ['transfer', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"







