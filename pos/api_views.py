from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum
from .models import POSSale, POSSaleItem, POSSession
from .serializers import POSSaleSerializer, POSSaleItemSerializer
from catalog.models import Product
from inventory.models import Stock, Warehouse
from customers.models import Customer
from decimal import Decimal
import json


@method_decorator(csrf_exempt, name='dispatch')
class POSSaleCreateAPIView(generics.CreateAPIView):
    serializer_class = POSSaleSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            
            # Obtener sesión activa
            active_session = POSSession.objects.filter(
                user=request.user,
                status='open'
            ).first()
            
            if not active_session:
                return Response(
                    {'error': 'No hay una sesión POS abierta'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la venta
            sale_data = {
                'session': active_session,
                'order_type': data.get('order_type', 'principal'),
                'customer_id': data.get('customer_id'),
                'payment_method': data.get('payment_method', 'cash'),
                'notes': data.get('notes', ''),
                'subtotal': Decimal('0.00'),
                'iva_amount': Decimal('0.00'),
                'discount_amount': Decimal(data.get('discount', 0)),
                'total': Decimal('0.00')
            }
            
            sale = POSSale.objects.create(**sale_data)
            
            # Procesar items
            items = data.get('items', [])
            subtotal = Decimal('0.00')
            total_iva = Decimal('0.00')
            
            for item_data in items:
                product_id = item_data.get('product_id')
                quantity = int(item_data.get('quantity', 1))
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
                
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                except Product.DoesNotExist:
                    continue
                
                # Calcular IVA según el tipo de orden
                item_subtotal = unit_price * quantity
                has_iva = sale.order_type == 'principal'
                item_iva = item_subtotal * Decimal('0.19') if has_iva else Decimal('0.00')
                item_total = item_subtotal + item_iva
                
                # Crear item de venta
                sale_item = POSSaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    iva_percentage=Decimal('19.00') if has_iva else Decimal('0.00'),
                    discount_percentage=Decimal('0.00'),
                    subtotal=item_subtotal,
                    iva_amount=item_iva,
                    discount_amount=Decimal('0.00'),
                    total=item_total
                )
                
                subtotal += item_subtotal
                total_iva += item_iva
                
                # Actualizar stock
                try:
                    stock = Stock.objects.get(product=product, warehouse=active_session.warehouse)
                    if stock.quantity >= quantity:
                        stock.quantity -= quantity
                        stock.save()
                    else:
                        return Response(
                            {'error': f'Stock insuficiente para {product.name}'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Stock.DoesNotExist:
                    return Response(
                        {'error': f'Producto {product.name} no disponible en la bodega'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Actualizar totales de la venta
            discount_amount = Decimal(data.get('discount', 0))
            sale.subtotal = subtotal
            sale.iva_amount = total_iva
            sale.discount_amount = discount_amount
            sale.total = subtotal + total_iva - discount_amount
            sale.save()
            
            # Actualizar estadísticas de la sesión
            active_session.total_sales += sale.total
            active_session.total_transactions += 1
            active_session.save()
            
            serializer = self.get_serializer(sale)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error al procesar la venta: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def pos_sales_list(request):
    """Lista las ventas del POS de la sesión activa"""
    # Obtener sesión activa
    active_session = POSSession.objects.filter(
        user=request.user,
        status='open'
    ).first()
    
    if not active_session:
        return Response([])
    
    # Filtrar solo las ventas de la sesión activa
    sales = POSSale.objects.filter(session=active_session).select_related(
        'session', 'customer__user'
    ).prefetch_related('items__product').order_by('-created_at')
    
    serializer = POSSaleSerializer(sales, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def pos_sale_detail(request, pk):
    """Detalle de una venta del POS"""
    try:
        sale = POSSale.objects.select_related(
            'session', 'customer__user'
        ).prefetch_related('items__product').get(pk=pk)
        
        serializer = POSSaleSerializer(sale)
        return Response(serializer.data)
        
    except POSSale.DoesNotExist:
        return Response(
            {'error': 'Venta no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@method_decorator(csrf_exempt, name='dispatch')
class POSSessionOpenAPIView(generics.CreateAPIView):
    """API para abrir una sesión POS"""
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            data = request.POST
            
            # Validar datos de entrada
            warehouse_id = data.get('warehouse_id')
            opening_cash = data.get('opening_cash', '0')
            notes = data.get('notes', '')

            # Validaciones
            if not warehouse_id:
                return Response({
                    'error': 'Bodega es requerida'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                opening_cash = Decimal(str(opening_cash))
                if opening_cash < 0:
                    return Response({
                        'error': 'El efectivo inicial no puede ser negativo'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'error': 'El efectivo inicial debe ser un número válido'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar que no haya una sesión abierta
            existing_session = POSSession.objects.filter(
                user=request.user,
                status='open'
            ).first()

            if existing_session:
                return Response({
                    'error': 'Ya tienes una sesión POS abierta',
                    'session_id': existing_session.session_id,
                    'warehouse': existing_session.warehouse.name,
                    'opened_at': existing_session.opened_at.isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar que la bodega existe y está activa
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
            except Warehouse.DoesNotExist:
                return Response({
                    'error': 'Bodega no encontrada o inactiva'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Crear nueva sesión
            session = POSSession.objects.create(
                user=request.user,
                warehouse=warehouse,
                opening_cash=opening_cash,
                status='open',
                notes=notes
            )

            return Response({
                'success': True,
                'message': 'Sesión POS abierta exitosamente',
                'session': {
                    'id': session.id,
                    'session_id': session.session_id,
                    'warehouse': {
                        'id': warehouse.id,
                        'name': warehouse.name,
                        'city': warehouse.city
                    },
                    'opening_cash': float(session.opening_cash),
                    'opened_at': session.opened_at.isoformat(),
                    'notes': session.notes or ''
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error interno al abrir sesión: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class POSSessionCloseAPIView(generics.GenericAPIView):
    """API para cerrar una sesión POS"""
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = request.POST
            
            # Validar datos de entrada
            closing_cash = data.get('closing_cash', '0')
            notes = data.get('notes', '')

            # Validaciones
            try:
                closing_cash = Decimal(str(closing_cash))
                if closing_cash < 0:
                    return Response({
                        'error': 'El efectivo final no puede ser negativo'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'error': 'El efectivo final debe ser un número válido'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Obtener la sesión activa
            session = POSSession.objects.filter(
                user=request.user,
                status='open'
            ).first()

            if not session:
                return Response({
                    'error': 'No hay una sesión POS abierta para cerrar'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Cerrar la sesión usando el método del modelo
            session.close_session(closing_cash, notes)

            # Preparar reporte de ventas detallado
            sales = POSSale.objects.filter(session=session).select_related('customer__user')
            sales_report = []
            for sale in sales:
                sales_report.append({
                    'sale_number': sale.sale_number,
                    'order_type': sale.get_order_type_display(),
                    'customer': sale.customer.full_name if sale.customer else 'Cliente general',
                    'payment_method': sale.get_payment_method_display(),
                    'subtotal': float(sale.subtotal),
                    'iva_amount': float(sale.iva_amount),
                    'discount_amount': float(sale.discount_amount),
                    'total': float(sale.total),
                    'created_at': sale.created_at.isoformat(),
                    'items_count': sale.items.count()
                })

            # Calcular estadísticas adicionales
            total_items_sold = sum(sale.items.count() for sale in sales)
            payment_methods = {}
            for sale in sales:
                method = sale.get_payment_method_display()
                payment_methods[method] = payment_methods.get(method, 0) + float(sale.total)

            return Response({
                'success': True,
                'message': 'Sesión POS cerrada exitosamente',
                'session': {
                    'id': session.id,
                    'session_id': session.session_id,
                    'warehouse': {
                        'id': session.warehouse.id,
                        'name': session.warehouse.name,
                        'city': session.warehouse.city
                    },
                    'opening_cash': float(session.opening_cash),
                    'closing_cash': float(session.closing_cash),
                    'total_sales': float(session.total_sales),
                    'total_transactions': session.total_transactions,
                    'expected_cash': float(session.expected_cash),
                    'cash_difference': float(session.cash_difference),
                    'duration': session.duration_formatted,
                    'opened_at': session.opened_at.isoformat(),
                    'closed_at': session.closed_at.isoformat(),
                    'notes': session.notes or ''
                },
                'summary': {
                    'total_items_sold': total_items_sold,
                    'average_sale': float(session.total_sales / session.total_transactions) if session.total_transactions > 0 else 0,
                    'payment_methods': payment_methods
                },
                'sales_report': sales_report
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error interno al cerrar sesión: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def pos_session_status(request):
    """API para obtener el estado de la sesión actual"""
    try:
        # Obtener la sesión activa
        session = POSSession.objects.filter(
            user=request.user,
            status='open'
        ).select_related('warehouse').first()

        if not session:
            return Response({
                'has_active_session': False,
                'message': 'No hay una sesión POS abierta'
            })

        # Calcular estadísticas actuales
        sales = POSSale.objects.filter(session=session)
        total_sales_aggregate = sales.aggregate(total_sum=Sum('total'))
        current_total_sales = total_sales_aggregate['total_sum'] or Decimal('0.00')
        current_transactions = sales.count()
        current_items_sold = sum(sale.items.count() for sale in sales)

        # Calcular estadísticas por método de pago
        payment_methods = {}
        for sale in sales:
            method = sale.get_payment_method_display()
            payment_methods[method] = payment_methods.get(method, 0) + float(sale.total)

        # Calcular estadísticas por tipo de orden
        order_types = {}
        for sale in sales:
            order_type = sale.get_order_type_display()
            order_types[order_type] = order_types.get(order_type, 0) + float(sale.total)

        return Response({
            'has_active_session': True,
            'session': {
                'id': session.id,
                'session_id': session.session_id,
                'warehouse': {
                    'id': session.warehouse.id,
                    'name': session.warehouse.name,
                    'city': session.warehouse.city
                },
                'opening_cash': float(session.opening_cash),
                'current_sales': float(current_total_sales),
                'current_transactions': current_transactions,
                'current_items_sold': current_items_sold,
                'expected_cash': float(session.opening_cash + current_total_sales),
                'duration': session.duration_formatted,
                'opened_at': session.opened_at.isoformat(),
                'notes': session.notes or ''
            },
            'statistics': {
                'payment_methods': payment_methods,
                'order_types': order_types,
                'average_sale': float(current_total_sales / current_transactions) if current_transactions > 0 else 0,
                'average_items_per_sale': current_items_sold / current_transactions if current_transactions > 0 else 0
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener estado de sesión: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def warehouses_list(request):
    """API para obtener la lista de bodegas disponibles"""
    try:
        warehouses = Warehouse.objects.filter(is_active=True).values('id', 'name', 'city', 'code')
        return Response(list(warehouses))
    except Exception as e:
        return Response({
            'error': f'Error al obtener bodegas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
