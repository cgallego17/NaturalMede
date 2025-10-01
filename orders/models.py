from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Order(models.Model):
    ORDER_TYPES = [
        ('principal', 'Principal'),
        ('auxiliar', 'Auxiliar'),
    ]

    STATUS_CHOICES = [
        ('new', 'Nuevo'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_METHODS = [
        ('cash_on_delivery', 'Contraentrega'),
        ('bank_transfer', 'Transferencia Bancolombia'),
        ('addi', 'Addi'),
    ]

    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='principal', verbose_name="Tipo de orden")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Número de orden")
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='orders', verbose_name="Cliente")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Estado")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name="Método de pago")
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal")
    iva_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo de envío")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total")
    
    # Información de envío
    shipping_address = models.TextField(verbose_name="Dirección de envío")
    shipping_city = models.CharField(max_length=100, verbose_name="Ciudad de envío")
    shipping_phone = models.CharField(max_length=20, verbose_name="Teléfono de envío")
    shipping_notes = models.TextField(blank=True, verbose_name="Notas de envío")
    
    # Información adicional
    notes = models.TextField(blank=True, verbose_name="Notas")
    internal_notes = models.TextField(blank=True, verbose_name="Notas internas")
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Pagada en")
    shipped_at = models.DateTimeField(blank=True, null=True, verbose_name="Enviada en")
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name="Entregada en")

    class Meta:
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden {self.order_number} - {self.customer.full_name}"
    
    @property
    def status_color(self):
        """Retorna el color CSS para el estado de la orden"""
        colors = {
            'new': 'primary',
            'pending': 'warning',
            'paid': 'success',
            'shipped': 'info',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Genera un número de orden único basado en el tipo"""
        import datetime
        from django.db.models import Max
        
        now = datetime.datetime.now()
        date_prefix = now.strftime('%Y%m%d')
        
        # Prefijo según el tipo de orden
        type_prefix = 'PR' if self.order_type == 'principal' else 'AU'
        
        # Buscar el último consecutivo del día para este tipo
        last_order = Order.objects.filter(
            order_number__startswith=f"{type_prefix}{date_prefix}",
            order_type=self.order_type
        ).aggregate(max_num=Max('order_number'))
        
        if last_order['max_num']:
            # Extraer el número del último consecutivo
            last_num = int(last_order['max_num'][-4:])  # Últimos 4 dígitos
            next_num = last_num + 1
        else:
            next_num = 1
        
        # Formato: PR202509300001 o AU202509300001
        return f"{type_prefix}{date_prefix}{next_num:04d}"

    @property
    def can_be_cancelled(self):
        return self.status in ['new', 'pending']

    @property
    def can_be_paid(self):
        return self.status in ['new', 'pending']

    @property
    def can_be_shipped(self):
        return self.status == 'paid'

    @property
    def can_be_delivered(self):
        return self.status == 'shipped'
    
    @property
    def has_iva(self):
        """Determina si la orden debe tener IVA"""
        return self.order_type == 'principal'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Orden")
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    iva_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="% IVA")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    iva_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="IVA")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")

    class Meta:
        verbose_name = "Item de orden"
        verbose_name_plural = "Items de orden"
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calcular totales
        self.subtotal = self.unit_price * self.quantity
        
        # Solo aplicar IVA si la orden es principal
        if self.order.has_iva:
            self.iva_amount = self.subtotal * (self.iva_percentage / 100)
        else:
            self.iva_amount = Decimal('0.00')
            
        self.total = self.subtotal + self.iva_amount
        super().save(*args, **kwargs)


class ShippingRate(models.Model):
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    min_weight = models.DecimalField(max_digits=8, decimal_places=3, default=0, verbose_name="Peso mínimo (kg)")
    max_weight = models.DecimalField(max_digits=8, decimal_places=3, verbose_name="Peso máximo (kg)")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo")
    estimated_days = models.PositiveIntegerField(default=1, verbose_name="Días estimados")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Tarifa de envío"
        verbose_name_plural = "Tarifas de envío"
        ordering = ['city', 'min_weight']

    def __str__(self):
        return f"{self.city} - {self.min_weight}-{self.max_weight}kg: ${self.cost}"

    @classmethod
    def get_shipping_cost(cls, city, weight):
        """Calcula el costo de envío para una ciudad y peso específicos"""
        try:
            rate = cls.objects.filter(
                city__iexact=city,
                min_weight__lte=weight,
                max_weight__gte=weight,
                is_active=True
            ).first()
            return rate.cost if rate else Decimal('0.00')
        except:
            return Decimal('0.00')

