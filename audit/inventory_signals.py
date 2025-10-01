from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, InventoryTrace
from .utils import create_inventory_trace


@receiver(post_save, sender='purchases.PurchaseItem')
def trace_purchase_item_creation(sender, instance, created, **kwargs):
    """
    Rastrea la creación de items de compra
    """
    if created and instance.purchase.status == 'completed':
        # Crear trazabilidad cuando se completa la compra
        create_inventory_trace(
            movement_type='PURCHASE',
            product=instance.product,
            warehouse=instance.purchase.warehouse,
            quantity=instance.quantity,
            unit_cost=instance.unit_cost,
            total_cost=instance.quantity * instance.unit_cost,
            purchase=instance.purchase,
            purchase_item=instance,
            supplier=instance.purchase.supplier,
            user=instance.purchase.created_by,
            notes=f"Compra completada - {instance.purchase.supplier.name}"
        )


@receiver(post_save, sender='purchases.PurchaseReceipt')
def trace_purchase_receipt(sender, instance, created, **kwargs):
    """
    Rastrea la recepción de productos de compra
    """
    if created:
        for item in instance.items.all():
            create_inventory_trace(
                movement_type='PURCHASE_RECEIPT',
                product=item.product,
                warehouse=instance.warehouse,
                quantity=item.quantity_received,
                unit_cost=item.unit_cost,
                total_cost=item.quantity_received * item.unit_cost,
                purchase=instance.purchase,
                purchase_item=item.purchase_item,
                supplier=instance.purchase.supplier,
                user=instance.received_by,
                batch_number=item.batch_number,
                expiration_date=item.expiration_date,
                notes=f"Recepción de compra - Lote: {item.batch_number or 'N/A'}"
            )


@receiver(post_save, sender='inventory.StockTransferItem')
def trace_stock_transfer(sender, instance, created, **kwargs):
    """
    Rastrea las transferencias de stock
    """
    if created and instance.transfer.status == 'completed':
        # Movimiento de salida desde bodega origen
        create_inventory_trace(
            movement_type='STOCK_TRANSFER',
            product=instance.product,
            warehouse=instance.transfer.from_warehouse,
            quantity=-instance.quantity,  # Negativo para salida
            unit_cost=instance.unit_cost,
            total_cost=instance.quantity * instance.unit_cost,
            stock_transfer=instance.transfer,
            stock_transfer_item=instance,
            user=instance.transfer.created_by,
            notes=f"Transferencia salida a {instance.transfer.to_warehouse.name}"
        )
        
        # Movimiento de entrada a bodega destino
        create_inventory_trace(
            movement_type='STOCK_TRANSFER_RECEIVE',
            product=instance.product,
            warehouse=instance.transfer.to_warehouse,
            quantity=instance.quantity,  # Positivo para entrada
            unit_cost=instance.unit_cost,
            total_cost=instance.quantity * instance.unit_cost,
            stock_transfer=instance.transfer,
            stock_transfer_item=instance,
            user=instance.transfer.created_by,
            notes=f"Transferencia entrada desde {instance.transfer.from_warehouse.name}"
        )


@receiver(post_save, sender='pos.POSSaleItem')
def trace_pos_sale(sender, instance, created, **kwargs):
    """
    Rastrea las ventas POS
    """
    if created and instance.sale.status == 'completed':
        create_inventory_trace(
            movement_type='SALE',
            product=instance.product,
            warehouse=instance.sale.session.warehouse,
            quantity=-instance.quantity,  # Negativo para salida
            unit_cost=instance.unit_cost,
            total_cost=instance.quantity * instance.unit_cost,
            pos_sale=instance.sale,
            pos_sale_item=instance,
            user=instance.sale.session.user,
            notes=f"Venta POS #{instance.sale.id} - Cliente: {instance.sale.customer.name if instance.sale.customer else 'Sin cliente'}"
        )


@receiver(post_save, sender='orders.OrderItem')
def trace_order_sale(sender, instance, created, **kwargs):
    """
    Rastrea las ventas por órdenes web
    """
    if created and instance.order.status == 'completed':
        # Asumir que las órdenes web se despachan desde la bodega principal
        # Esto se puede ajustar según la lógica de negocio
        from inventory.models import Warehouse
        main_warehouse = Warehouse.objects.filter(is_main=True).first()
        
        if main_warehouse:
            create_inventory_trace(
                movement_type='SALE',
                product=instance.product,
                warehouse=main_warehouse,
                quantity=-instance.quantity,  # Negativo para salida
                unit_cost=instance.unit_cost,
                total_cost=instance.quantity * instance.unit_cost,
                order=instance.order,
                order_item=instance,
                user=instance.order.user,
                notes=f"Venta Web #{instance.order.id} - Cliente: {instance.order.customer.name if instance.order.customer else 'Sin cliente'}"
            )


@receiver(post_save, sender='inventory.Stock')
def trace_stock_adjustments(sender, instance, created, **kwargs):
    """
    Rastrea ajustes manuales de stock
    """
    if not created:  # Solo para actualizaciones
        # Obtener el valor anterior del stock
        old_stock = getattr(instance, '_old_stock', None)
        if old_stock is not None and old_stock != instance.quantity:
            difference = instance.quantity - old_stock
            
            create_inventory_trace(
                movement_type='STOCK_ADJUSTMENT',
                product=instance.product,
                warehouse=instance.warehouse,
                quantity=difference,
                unit_cost=instance.product.price,
                total_cost=abs(difference) * instance.product.price,
                user=getattr(instance, '_updated_by', None),
                notes=f"Ajuste manual de stock: {old_stock} → {instance.quantity}"
            )


@receiver(pre_save, sender='inventory.Stock')
def capture_old_stock(sender, instance, **kwargs):
    """
    Captura el valor anterior del stock antes de la actualización
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_stock = old_instance.quantity
        except sender.DoesNotExist:
            pass


def create_inventory_trace(movement_type, product, warehouse, quantity, 
                          unit_cost=None, total_cost=None, user=None,
                          purchase=None, purchase_item=None,
                          stock_transfer=None, stock_transfer_item=None,
                          pos_sale=None, pos_sale_item=None,
                          order=None, order_item=None,
                          supplier=None, batch_number=None, 
                          expiration_date=None, notes=None, **kwargs):
    """
    Función helper para crear trazabilidad de inventario
    """
    try:
        # Obtener stock actual
        from inventory.models import Stock
        stock_obj = Stock.objects.filter(
            product=product, 
            warehouse=warehouse
        ).first()
        
        stock_before = stock_obj.quantity if stock_obj else 0
        stock_after = stock_before + quantity
        
        # Crear el registro de trazabilidad
        trace = InventoryTrace.objects.create(
            movement_type=movement_type,
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            stock_before=stock_before,
            stock_after=stock_after,
            purchase=purchase,
            purchase_item=purchase_item,
            stock_transfer=stock_transfer,
            stock_transfer_item=stock_transfer_item,
            pos_sale=pos_sale,
            pos_sale_item=pos_sale_item,
            order=order,
            order_item=order_item,
            supplier=supplier,
            batch_number=batch_number,
            expiration_date=expiration_date,
            user=user,
            notes=notes,
            extra_data=kwargs.get('extra_data')
        )
        
        # Crear también un log de auditoría
        AuditLog.objects.create(
            user=user,
            action='STOCK_MOVEMENT',
            content_type=ContentType.objects.get_for_model(InventoryTrace),
            object_id=str(trace.pk),
            object_repr=str(trace),
            severity='MEDIUM',
            app_label='audit',
            model_name='inventorytrace',
            message=trace.movement_description,
            extra_data={
                'movement_type': movement_type,
                'product_id': product.id,
                'warehouse_id': warehouse.id,
                'quantity': float(quantity),
                'stock_before': float(stock_before),
                'stock_after': float(stock_after),
            }
        )
        
        return trace
        
    except Exception as e:
        # Log del error pero no fallar la operación principal
        print(f"Error creando trazabilidad de inventario: {str(e)}")
        return None
