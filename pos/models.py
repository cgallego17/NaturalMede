from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class POSSession(models.Model):
    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
    ]

    session_id = models.CharField(max_length=50, unique=True, verbose_name="ID de sesión")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Usuario")
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE, verbose_name="Bodega")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Estado")
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Efectivo inicial")
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Efectivo final")
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total ventas")
    total_transactions = models.PositiveIntegerField(default=0, verbose_name="Total transacciones")
    opened_at = models.DateTimeField(auto_now_add=True, verbose_name="Abierta en")
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="Cerrada en")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Sesión POS"
        verbose_name_plural = "Sesiones POS"
        ordering = ['-opened_at']

    def __str__(self):
        return f"Sesión {self.session_id} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = self.generate_session_id()
        super().save(*args, **kwargs)

    def generate_session_id(self):
        """Genera un ID único para la sesión"""
        import datetime
        now = datetime.datetime.now()
        return f"POS{now.strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:6].upper()}"

    @property
    def cash_difference(self):
        """Diferencia entre el efectivo final y el esperado"""
        expected_cash = self.opening_cash + self.total_sales
        return self.closing_cash - expected_cash

    @property
    def expected_cash(self):
        """Efectivo esperado (inicial + ventas)"""
        return self.opening_cash + self.total_sales

    @property
    def duration(self):
        """Duración de la sesión"""
        if self.closed_at:
            return self.closed_at - self.opened_at
        else:
            from django.utils import timezone
            return timezone.now() - self.opened_at

    @property
    def duration_formatted(self):
        """Duración formateada"""
        duration = self.duration
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

    def close_session(self, closing_cash, notes=None):
        """Cierra la sesión con el efectivo final"""
        from django.utils import timezone
        from django.db.models import Sum
        
        # Calcular estadísticas finales
        sales = POSSale.objects.filter(session=self)
        total_sales_aggregate = sales.aggregate(total_sum=Sum('total'))
        self.total_sales = total_sales_aggregate['total_sum'] or Decimal('0.00')
        self.total_transactions = sales.count()
        self.closing_cash = closing_cash
        self.status = 'closed'
        self.closed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
        return self


class POSSale(models.Model):
    ORDER_TYPES = [
        ('principal', 'Principal'),
        ('auxiliar', 'Auxiliar'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('mixed', 'Mixto'),
    ]

    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='principal', verbose_name="Tipo de orden")
    sale_number = models.CharField(max_length=20, unique=True, verbose_name="Número de venta")
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='sales', verbose_name="Sesión")
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Cliente")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name="Método de pago")
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal")
    iva_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Descuento")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total")
    
    # Información adicional
    notes = models.TextField(blank=True, verbose_name="Notas")
    barcode_scanned = models.CharField(max_length=50, blank=True, verbose_name="Código de barras escaneado")
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Venta POS"
        verbose_name_plural = "Ventas POS"
        ordering = ['-created_at']

    def __str__(self):
        return f"Venta {self.sale_number} - ${self.total}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = self.generate_sale_number()
        super().save(*args, **kwargs)

    def generate_sale_number(self):
        """Genera un número único para la venta basado en el tipo"""
        import datetime
        from django.db.models import Max
        
        now = datetime.datetime.now()
        date_prefix = now.strftime('%Y%m%d')
        
        # Prefijo según el tipo de orden
        type_prefix = 'PR' if self.order_type == 'principal' else 'AU'
        
        # Buscar el último consecutivo del día para este tipo
        last_sale = POSSale.objects.filter(
            sale_number__startswith=f"{type_prefix}{date_prefix}",
            order_type=self.order_type
        ).aggregate(max_num=Max('sale_number'))
        
        if last_sale['max_num']:
            # Extraer el número del último consecutivo
            last_num = int(last_sale['max_num'][-4:])  # Últimos 4 dígitos
            next_num = last_num + 1
        else:
            next_num = 1
        
        # Formato: PR202509300001 o AU202509300001
        return f"{type_prefix}{date_prefix}{next_num:04d}"
    
    @property
    def has_iva(self):
        """Determina si la venta debe tener IVA"""
        return self.order_type == 'principal'


class POSSaleItem(models.Model):
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name='items', verbose_name="Venta")
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    iva_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="% IVA")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Descuento")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    iva_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="IVA")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Descuento")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")

    class Meta:
        verbose_name = "Item de venta POS"
        verbose_name_plural = "Items de venta POS"
        unique_together = ['sale', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calcular totales
        self.subtotal = self.unit_price * self.quantity
        self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        subtotal_after_discount = self.subtotal - self.discount_amount
        
        # Solo aplicar IVA si la venta es principal
        if self.sale.has_iva:
            self.iva_amount = subtotal_after_discount * (self.iva_percentage / 100)
        else:
            self.iva_amount = Decimal('0.00')
            
        self.total = subtotal_after_discount + self.iva_amount
        super().save(*args, **kwargs)



