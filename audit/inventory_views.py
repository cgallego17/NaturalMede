from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
import csv
import json
from decimal import Decimal

from .models import InventoryTrace, AuditLog
from catalog.models import Product
from inventory.models import Warehouse


def safe_json_dumps(data):
    """
    Convierte datos a JSON de forma segura, manejando Decimal y otros tipos
    """
    def decimal_converter(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(data, default=decimal_converter)


class InventoryTraceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar trazabilidad de inventario
    """
    model = InventoryTrace
    template_name = 'audit/inventory_trace_list.html'
    context_object_name = 'traces'
    permission_required = 'audit.view_inventorytrace'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = InventoryTrace.objects.select_related(
            'product', 'warehouse', 'user', 'supplier',
            'purchase', 'stock_transfer', 'pos_sale', 'order'
        ).order_by('-created_at')
        
        # Filtros
        product_filter = self.request.GET.get('product')
        warehouse_filter = self.request.GET.get('warehouse')
        movement_type_filter = self.request.GET.get('movement_type')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if product_filter:
            queryset = queryset.filter(product_id=product_filter)
        
        if warehouse_filter:
            queryset = queryset.filter(warehouse_id=warehouse_filter)
        
        if movement_type_filter:
            queryset = queryset.filter(movement_type=movement_type_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(product__sku__icontains=search) |
                Q(batch_number__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        context['stats'] = {
            'total_movements': InventoryTrace.objects.count(),
            'today_movements': InventoryTrace.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'incoming_movements': InventoryTrace.objects.filter(
                quantity__gt=0
            ).count(),
            'outgoing_movements': InventoryTrace.objects.filter(
                quantity__lt=0
            ).count(),
        }
        
        # Filtros disponibles
        context['movement_type_choices'] = InventoryTrace.MOVEMENT_TYPES
        context['status_choices'] = InventoryTrace.STATUS_CHOICES
        context['products'] = Product.objects.all().order_by('name')
        context['warehouses'] = Warehouse.objects.all().order_by('name')
        
        return context


class InventoryTraceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Vista para mostrar detalles de trazabilidad de inventario
    """
    model = InventoryTrace
    template_name = 'audit/inventory_trace_detail.html'
    context_object_name = 'trace'
    permission_required = 'audit.view_inventorytrace'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener historial relacionado del producto
        product_traces = InventoryTrace.objects.filter(
            product=self.object.product,
            warehouse=self.object.warehouse
        ).order_by('-created_at')[:10]
        
        context['related_traces'] = product_traces
        
        return context


@login_required
@permission_required('audit.view_inventorytrace')
def inventory_trace_dashboard(request):
    """
    Dashboard de trazabilidad de inventario - VERSIÓN MÍNIMA
    """
    # Datos estáticos mínimos para evitar cualquier problema
    context = {
        'total_traces': 0,
        'today_traces': 0,
        'incoming_movements': 0,
        'outgoing_movements': 0,
        'movement_stats': '[]',
        'product_stats': [],
        'daily_stats': '[]',
        'cost_stats': [],
        'warehouse_stats': [],
        'error_message': 'Dashboard temporalmente deshabilitado para resolver problemas de rendimiento'
    }
    
    return render(request, 'audit/inventory_trace_dashboard.html', context)


@login_required
@permission_required('audit.view_inventorytrace')
def inventory_trace_export(request):
    """
    Exportar trazabilidad de inventario a CSV
    """
    # Obtener filtros de la request
    filters = {}
    if request.GET.get('product'):
        filters['product_id'] = request.GET.get('product')
    if request.GET.get('warehouse'):
        filters['warehouse_id'] = request.GET.get('warehouse')
    if request.GET.get('movement_type'):
        filters['movement_type'] = request.GET.get('movement_type')
    if request.GET.get('date_from'):
        try:
            date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d').date()
            filters['created_at__date__gte'] = date_from
        except ValueError:
            pass
    if request.GET.get('date_to'):
        try:
            date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d').date()
            filters['created_at__date__lte'] = date_to
        except ValueError:
            pass
    
    # Obtener registros
    traces = InventoryTrace.objects.filter(**filters).select_related(
        'product', 'warehouse', 'user', 'supplier'
    ).order_by('-created_at')
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_trace.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Tipo', 'Producto', 'SKU', 'Bodega', 'Cantidad', 
        'Costo Unit.', 'Costo Total', 'Stock Antes', 'Stock Después',
        'Proveedor', 'Lote', 'Vencimiento', 'Usuario', 'Documento Origen', 'Notas'
    ])
    
    for trace in traces:
        writer.writerow([
            trace.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            trace.get_movement_type_display(),
            trace.product.name,
            trace.product.sku,
            trace.warehouse.name,
            trace.quantity,
            trace.unit_cost or '',
            trace.total_cost or '',
            trace.stock_before,
            trace.stock_after,
            trace.supplier.name if trace.supplier else '',
            trace.batch_number or '',
            trace.expiration_date.strftime('%Y-%m-%d') if trace.expiration_date else '',
            trace.user.username if trace.user else '',
            trace.get_source_document(),
            trace.notes or '',
        ])
    
    return response


@login_required
@permission_required('audit.view_inventorytrace')
def product_trace_report(request, product_id):
    """
    Reporte de trazabilidad para un producto específico
    """
    product = get_object_or_404(Product, pk=product_id)
    
    # Obtener todas las trazas del producto
    traces = InventoryTrace.objects.filter(
        product=product
    ).select_related(
        'warehouse', 'user', 'supplier', 'purchase', 
        'stock_transfer', 'pos_sale', 'order'
    ).order_by('-created_at')
    
    # Estadísticas del producto
    stats = {
        'total_movements': traces.count(),
        'total_incoming': traces.filter(quantity__gt=0).aggregate(
            total=Sum('quantity')
        )['total'] or 0,
        'total_outgoing': traces.filter(quantity__lt=0).aggregate(
            total=Sum('quantity')
        )['total'] or 0,
        'avg_cost': traces.filter(unit_cost__isnull=False).aggregate(
            avg=Avg('unit_cost')
        )['avg'] or 0,
        'total_cost': traces.filter(total_cost__isnull=False).aggregate(
            total=Sum('total_cost')
        )['total'] or 0,
    }
    
    # Movimientos por bodega
    warehouse_stats = traces.values('warehouse__name').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count')
    
    # Movimientos por tipo
    movement_stats = traces.values('movement_type').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count')
    
    context = {
        'product': product,
        'traces': traces,
        'stats': stats,
        'warehouse_stats': warehouse_stats,
        'movement_stats': movement_stats,
    }
    
    return render(request, 'audit/product_trace_report.html', context)


@login_required
@permission_required('audit.view_inventorytrace')
def inventory_trace_api(request):
    """
    API para obtener datos de trazabilidad (para gráficos)
    """
    chart_type = request.GET.get('chart_type')
    
    if chart_type == 'daily':
        # Datos diarios para gráfico
        days = int(request.GET.get('days', 30))
        data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            
            incoming = InventoryTrace.objects.filter(
                created_at__date=date,
                quantity__gt=0
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            outgoing = InventoryTrace.objects.filter(
                created_at__date=date,
                quantity__lt=0
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'incoming': float(incoming) if incoming else 0,
                'outgoing': float(abs(outgoing)) if outgoing else 0,
                'net': float(incoming + outgoing) if incoming and outgoing else 0
            })
        data.reverse()
        return JsonResponse({'data': data})
    
    elif chart_type == 'movements':
        # Estadísticas por tipo de movimiento
        data = list(InventoryTrace.objects.values('movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-count'))
        return JsonResponse({'data': data})
    
    elif chart_type == 'warehouses':
        # Estadísticas por bodega
        data = list(InventoryTrace.objects.values('warehouse__name').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-count'))
        return JsonResponse({'data': data})
    
    return JsonResponse({'error': 'Invalid chart type'})
