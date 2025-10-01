from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json


class AuditLog(models.Model):
    """
    Modelo de auditoría para rastrear cambios en el sistema
    """
    
    # Tipos de acciones
    ACTION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Iniciar Sesión'),
        ('LOGOUT', 'Cerrar Sesión'),
        ('VIEW', 'Ver'),
        ('EXPORT', 'Exportar'),
        ('IMPORT', 'Importar'),
        ('PRINT', 'Imprimir'),
        ('EMAIL', 'Enviar Email'),
        ('CANCEL', 'Cancelar'),
        ('APPROVE', 'Aprobar'),
        ('REJECT', 'Rechazar'),
        ('COMPLETE', 'Completar'),
        ('TRANSFER', 'Transferir'),
        ('RECEIVE', 'Recibir'),
        ('RETURN', 'Devolver'),
        ('REFUND', 'Reembolsar'),
        ('DISCOUNT', 'Descuento'),
        ('PAYMENT', 'Pago'),
        ('STOCK_ADJUSTMENT', 'Ajuste de Stock'),
        ('PRICE_CHANGE', 'Cambio de Precio'),
        ('STATUS_CHANGE', 'Cambio de Estado'),
        ('PERMISSION_CHANGE', 'Cambio de Permisos'),
        ('PASSWORD_CHANGE', 'Cambio de Contraseña'),
        ('PROFILE_UPDATE', 'Actualizar Perfil'),
        ('SYSTEM_CONFIG', 'Configuración del Sistema'),
        ('BACKUP', 'Respaldo'),
        ('RESTORE', 'Restaurar'),
        ('OTHER', 'Otro'),
    ]
    
    # Niveles de severidad
    SEVERITY_CHOICES = [
        ('LOW', 'Bajo'),
        ('MEDIUM', 'Medio'),
        ('HIGH', 'Alto'),
        ('CRITICAL', 'Crítico'),
    ]
    
    # Estados del log
    STATUS_CHOICES = [
        ('SUCCESS', 'Exitoso'),
        ('FAILED', 'Fallido'),
        ('PENDING', 'Pendiente'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    # Campos principales
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Usuario",
        help_text="Usuario que realizó la acción"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Acción",
        help_text="Tipo de acción realizada"
    )
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Tipo de Contenido",
        help_text="Tipo de modelo afectado"
    )
    
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="ID del Objeto",
        help_text="ID del objeto afectado"
    )
    
    content_object = GenericForeignKey(
        'content_type', 
        'object_id'
    )
    
    object_repr = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Representación del Objeto",
        help_text="Representación string del objeto"
    )
    
    # Datos de cambios
    old_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Valores Anteriores",
        help_text="Valores antes del cambio",
        encoder=DjangoJSONEncoder
    )
    
    new_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Valores Nuevos",
        help_text="Valores después del cambio",
        encoder=DjangoJSONEncoder
    )
    
    # Metadatos
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name="Severidad",
        help_text="Nivel de severidad del evento"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUCCESS',
        verbose_name="Estado",
        help_text="Estado del evento"
    )
    
    message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Mensaje",
        help_text="Descripción detallada del evento"
    )
    
    # Información de contexto
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP",
        help_text="IP desde donde se realizó la acción"
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent",
        help_text="Información del navegador/cliente"
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name="Clave de Sesión",
        help_text="ID de la sesión"
    )
    
    # Información de la aplicación
    app_label = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Etiqueta de App",
        help_text="Nombre de la aplicación Django"
    )
    
    model_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Nombre del Modelo",
        help_text="Nombre del modelo Django"
    )
    
    # Información adicional
    extra_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Datos Extra",
        help_text="Información adicional del evento",
        encoder=DjangoJSONEncoder
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Creación",
        help_text="Momento en que ocurrió el evento"
    )
    
    # Campos de auditoría del propio modelo
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_created',
        verbose_name="Creado por",
        help_text="Usuario que creó este registro de auditoría"
    )
    
    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.object_repr or 'Sistema'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def has_changes(self):
        """Verifica si hay cambios registrados"""
        return bool(self.old_values or self.new_values)
    
    @property
    def changes_summary(self):
        """Resumen de los cambios realizados"""
        if not self.has_changes:
            return "Sin cambios registrados"
        
        changes = []
        if self.old_values and self.new_values:
            for field, new_value in self.new_values.items():
                old_value = self.old_values.get(field)
                if old_value != new_value:
                    changes.append(f"{field}: {old_value} → {new_value}")
        elif self.new_values:
            changes.append("Campos agregados: " + ", ".join(self.new_values.keys()))
        elif self.old_values:
            changes.append("Campos eliminados: " + ", ".join(self.old_values.keys()))
        
        return "; ".join(changes) if changes else "Cambios no especificados"
    
    def get_related_objects(self):
        """Obtiene objetos relacionados si existen"""
        if not self.content_type or not self.object_id:
            return None
        
        try:
            model_class = self.content_type.model_class()
            return model_class.objects.get(pk=self.object_id)
        except:
            return None


class InventoryTrace(models.Model):
    """
    Modelo específico para trazabilidad de inventario
    Rastrea el flujo completo desde compra hasta venta
    """
    
    # Tipos de movimiento de inventario
    MOVEMENT_TYPES = [
        ('PURCHASE', 'Compra'),
        ('PURCHASE_RECEIPT', 'Recepción de Compra'),
        ('STOCK_ADJUSTMENT', 'Ajuste de Stock'),
        ('STOCK_TRANSFER', 'Transferencia'),
        ('STOCK_TRANSFER_RECEIVE', 'Recepción de Transferencia'),
        ('SALE', 'Venta'),
        ('SALE_RETURN', 'Devolución de Venta'),
        ('DAMAGE', 'Daño'),
        ('THEFT', 'Robo'),
        ('EXPIRATION', 'Vencimiento'),
        ('DONATION', 'Donación'),
        ('SAMPLE', 'Muestra'),
        ('OTHER', 'Otro'),
    ]
    
    # Estados del movimiento
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
        ('REJECTED', 'Rechazado'),
    ]
    
    # Información básica del movimiento
    movement_type = models.CharField(
        max_length=30,
        choices=MOVEMENT_TYPES,
        verbose_name="Tipo de Movimiento",
        help_text="Tipo de movimiento de inventario"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estado",
        help_text="Estado actual del movimiento"
    )
    
    # Referencias a objetos relacionados
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        verbose_name="Producto",
        help_text="Producto afectado"
    )
    
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        verbose_name="Bodega",
        help_text="Bodega donde ocurre el movimiento"
    )
    
    # Cantidades
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad del movimiento (positiva para entrada, negativa para salida)"
    )
    
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo Unitario",
        help_text="Costo unitario del producto en este movimiento"
    )
    
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo Total",
        help_text="Costo total del movimiento"
    )
    
    # Stock antes y después del movimiento
    stock_before = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Stock Antes",
        help_text="Stock disponible antes del movimiento"
    )
    
    stock_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Stock Después",
        help_text="Stock disponible después del movimiento"
    )
    
    # Referencias a documentos origen
    purchase = models.ForeignKey(
        'purchases.Purchase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Compra",
        help_text="Compra que originó este movimiento"
    )
    
    purchase_item = models.ForeignKey(
        'purchases.PurchaseItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Item de Compra",
        help_text="Item específico de la compra"
    )
    
    stock_transfer = models.ForeignKey(
        'inventory.StockTransfer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Transferencia",
        help_text="Transferencia que originó este movimiento"
    )
    
    stock_transfer_item = models.ForeignKey(
        'inventory.StockTransferItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Item de Transferencia",
        help_text="Item específico de la transferencia"
    )
    
    pos_sale = models.ForeignKey(
        'pos.POSSale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Venta POS",
        help_text="Venta POS que originó este movimiento"
    )
    
    pos_sale_item = models.ForeignKey(
        'pos.POSSaleItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Item de Venta POS",
        help_text="Item específico de la venta POS"
    )
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Orden",
        help_text="Orden que originó este movimiento"
    )
    
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Item de Orden",
        help_text="Item específico de la orden"
    )
    
    # Información de trazabilidad
    batch_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Número de Lote",
        help_text="Número de lote del producto"
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Vencimiento",
        help_text="Fecha de vencimiento del producto"
    )
    
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Proveedor",
        help_text="Proveedor del producto"
    )
    
    # Información de usuario y contexto
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario",
        help_text="Usuario que realizó el movimiento"
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre el movimiento"
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Creación",
        help_text="Momento en que se creó el movimiento"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización",
        help_text="Momento de la última actualización"
    )
    
    # Información adicional
    extra_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Datos Extra",
        help_text="Información adicional del movimiento",
        encoder=DjangoJSONEncoder
    )
    
    class Meta:
        verbose_name = "Trazabilidad de Inventario"
        verbose_name_plural = "Trazabilidades de Inventario"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'warehouse', 'created_at']),
            models.Index(fields=['movement_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiration_date']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} - {self.quantity} unidades"
    
    @property
    def is_incoming(self):
        """Verifica si es un movimiento de entrada"""
        return self.quantity > 0
    
    @property
    def is_outgoing(self):
        """Verifica si es un movimiento de salida"""
        return self.quantity < 0
    
    @property
    def movement_description(self):
        """Descripción detallada del movimiento"""
        direction = "Entrada" if self.is_incoming else "Salida"
        return f"{direction} de {abs(self.quantity)} unidades de {self.product.name} en {self.warehouse.name}"
    
    def get_source_document(self):
        """Obtiene el documento origen del movimiento"""
        if self.purchase:
            return f"Compra #{self.purchase.id}"
        elif self.stock_transfer:
            return f"Transferencia #{self.stock_transfer.id}"
        elif self.pos_sale:
            return f"Venta POS #{self.pos_sale.id}"
        elif self.order:
            return f"Orden #{self.order.id}"
        return "Manual"
    
    def get_cost_per_unit(self):
        """Calcula el costo por unidad"""
        if self.total_cost and self.quantity:
            return abs(self.total_cost / self.quantity)
        return self.unit_cost or 0


class AuditConfiguration(models.Model):
    """
    Configuración de auditoría para diferentes modelos
    """
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Contenido",
        help_text="Modelo a auditar"
    )
    
    is_enabled = models.BooleanField(
        default=True,
        verbose_name="Habilitado",
        help_text="Si la auditoría está habilitada para este modelo"
    )
    
    track_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Campos a Rastrear",
        help_text="Lista de campos específicos a auditar (vacío = todos)"
    )
    
    exclude_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Campos Excluidos",
        help_text="Lista de campos a excluir de la auditoría"
    )
    
    track_creates = models.BooleanField(
        default=True,
        verbose_name="Rastrear Creaciones",
        help_text="Si rastrear cuando se crean objetos"
    )
    
    track_updates = models.BooleanField(
        default=True,
        verbose_name="Rastrear Actualizaciones",
        help_text="Si rastrear cuando se actualizan objetos"
    )
    
    track_deletes = models.BooleanField(
        default=True,
        verbose_name="Rastrear Eliminaciones",
        help_text="Si rastrear cuando se eliminan objetos"
    )
    
    track_views = models.BooleanField(
        default=False,
        verbose_name="Rastrear Visualizaciones",
        help_text="Si rastrear cuando se visualizan objetos"
    )
    
    severity_level = models.CharField(
        max_length=20,
        choices=AuditLog.SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name="Nivel de Severidad",
        help_text="Nivel de severidad por defecto para este modelo"
    )
    
    retention_days = models.PositiveIntegerField(
        default=365,
        verbose_name="Días de Retención",
        help_text="Días que mantener los logs antes de eliminarlos"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    
    class Meta:
        verbose_name = "Configuración de Auditoría"
        verbose_name_plural = "Configuraciones de Auditoría"
        unique_together = ['content_type']
    
    def __str__(self):
        return f"Auditoría para {self.content_type.model}"


class AuditReport(models.Model):
    """
    Reportes de auditoría generados
    """
    
    REPORT_TYPES = [
        ('USER_ACTIVITY', 'Actividad de Usuario'),
        ('MODEL_CHANGES', 'Cambios de Modelo'),
        ('SECURITY_EVENTS', 'Eventos de Seguridad'),
        ('SYSTEM_EVENTS', 'Eventos del Sistema'),
        ('INVENTORY_TRACE', 'Trazabilidad de Inventario'),
        ('CUSTOM', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('GENERATING', 'Generando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre del Reporte",
        help_text="Nombre descriptivo del reporte"
    )
    
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPES,
        verbose_name="Tipo de Reporte"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estado"
    )
    
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Parámetros",
        help_text="Parámetros utilizados para generar el reporte"
    )
    
    file_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Ruta del Archivo",
        help_text="Ruta del archivo generado"
    )
    
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tamaño del Archivo",
        help_text="Tamaño del archivo en bytes"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Creado por"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Completado"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Mensaje de Error",
        help_text="Mensaje de error si el reporte falló"
    )
    
    class Meta:
        verbose_name = "Reporte de Auditoría"
        verbose_name_plural = "Reportes de Auditoría"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def is_failed(self):
        return self.status == 'FAILED'
    
    @property
    def duration(self):
        if self.completed_at and self.created_at:
            return self.completed_at - self.created_at
        return None