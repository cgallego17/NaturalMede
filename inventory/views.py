from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse
from django.utils import timezone
from .models import Warehouse, Stock, StockMovement, StockTransfer, StockTransferItem
from .forms import StockMovementForm, StockTransferForm, StockTransferItemForm
from catalog.models import Product


class InventoryDashboardView(ListView):
    template_name = 'inventory/dashboard.html'
    context_object_name = 'low_stock_items'

    def get_queryset(self):
        return Stock.objects.filter(
            quantity__lte=F('min_stock'),
            warehouse__is_active=True
        ).select_related('product', 'warehouse').order_by('quantity')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_products'] = Product.objects.filter(is_active=True).count()
        context['total_warehouses'] = Warehouse.objects.filter(is_active=True).count()
        context['out_of_stock'] = Stock.objects.filter(quantity=0).count()
        context['low_stock'] = Stock.objects.filter(quantity__lte=F('min_stock')).count()
        
        # Movimientos recientes
        context['recent_movements'] = StockMovement.objects.select_related(
            'product', 'warehouse', 'user'
        ).order_by('-created_at')[:10]
        
        # Transferencias pendientes
        context['pending_transfers'] = StockTransfer.objects.filter(
            status='pending'
        ).select_related('from_warehouse', 'to_warehouse', 'created_by')
        
        return context


class WarehouseListView(ListView):
    model = Warehouse
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'warehouses'
    paginate_by = 20

    def get_queryset(self):
        return Warehouse.objects.filter(is_active=True).order_by('name')


class WarehouseDetailView(DetailView):
    model = Warehouse
    template_name = 'inventory/warehouse_detail.html'
    context_object_name = 'warehouse'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse = self.object
        
        # Stock en esta bodega
        context['stocks'] = Stock.objects.filter(
            warehouse=warehouse
        ).select_related('product').order_by('product__name')
        
        # Movimientos recientes
        context['recent_movements'] = StockMovement.objects.filter(
            warehouse=warehouse
        ).select_related('product', 'user').order_by('-created_at')[:10]
        
        return context


class StockListView(ListView):
    model = Stock
    template_name = 'inventory/stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        queryset = Stock.objects.select_related('product', 'warehouse').all()
        
        # Filtro por bodega
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Filtro por stock bajo
        low_stock = self.request.GET.get('low_stock')
        if low_stock:
            queryset = queryset.filter(quantity__lte=F('min_stock'))
        
        # Filtro por sin stock
        out_of_stock = self.request.GET.get('out_of_stock')
        if out_of_stock:
            queryset = queryset.filter(quantity=0)
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(product__name__icontains=search_query) |
                Q(product__sku__icontains=search_query) |
                Q(product__barcode__icontains=search_query)
            )
        
        return queryset.order_by('product__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context


class LowStockListView(ListView):
    model = Stock
    template_name = 'inventory/low_stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        return Stock.objects.filter(
            quantity__lte=F('min_stock'),
            warehouse__is_active=True
        ).select_related('product', 'warehouse').order_by('quantity')


class StockMovementListView(ListView):
    model = StockMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 50

    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            'product', 'warehouse', 'user'
        ).all()
        
        # Filtro por tipo de movimiento
        movement_type = self.request.GET.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        # Filtro por bodega
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Filtro por producto
        product_id = self.request.GET.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movement_types'] = StockMovement.MOVEMENT_TYPES
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        context['products'] = Product.objects.filter(is_active=True)
        return context


class StockMovementCreateView(CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/movement_form.html'
    success_url = reverse_lazy('inventory:movement_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Movimiento de stock creado exitosamente')
        return response


class StockTransferListView(ListView):
    model = StockTransfer
    template_name = 'inventory/transfer_list.html'
    context_object_name = 'transfers'
    paginate_by = 20

    def get_queryset(self):
        queryset = StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'created_by'
        ).all()
        
        # Filtro por estado
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = StockTransfer.STATUS_CHOICES
        return context


class StockTransferCreateView(CreateView):
    model = StockTransfer
    form_class = StockTransferForm
    template_name = 'inventory/transfer_form.html'
    success_url = reverse_lazy('inventory:transfer_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Transferencia de stock creada exitosamente')
        return response


class StockTransferDetailView(DetailView):
    model = StockTransfer
    template_name = 'inventory/transfer_detail.html'
    context_object_name = 'transfer'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'created_by'
        ).prefetch_related('items__product')


class StockTransferCompleteView(UpdateView):
    model = StockTransfer
    fields = []
    template_name = 'inventory/transfer_complete.html'
    success_url = reverse_lazy('inventory:transfer_list')

    def form_valid(self, form):
        transfer = self.object
        
        if transfer.status != 'pending':
            messages.error(self.request, 'Solo se pueden completar transferencias pendientes')
            return redirect('inventory:transfer_detail', pk=transfer.pk)
        
        # Procesar items de la transferencia
        for item in transfer.items.all():
            # Reducir stock en bodega origen
            from_stock, created = Stock.objects.get_or_create(
                product=item.product,
                warehouse=transfer.from_warehouse,
                defaults={'quantity': 0}
            )
            from_stock.quantity -= item.quantity
            from_stock.save()
            
            # Crear movimiento de salida
            StockMovement.objects.create(
                product=item.product,
                warehouse=transfer.from_warehouse,
                movement_type='out',
                quantity=-item.quantity,
                reference=f'Transferencia {transfer.reference}',
                notes=f'Transferencia a {transfer.to_warehouse.name}',
                user=self.request.user
            )
            
            # Aumentar stock en bodega destino
            to_stock, created = Stock.objects.get_or_create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                defaults={'quantity': 0}
            )
            to_stock.quantity += item.quantity
            to_stock.save()
            
            # Crear movimiento de entrada
            StockMovement.objects.create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                movement_type='in',
                quantity=item.quantity,
                reference=f'Transferencia {transfer.reference}',
                notes=f'Transferencia desde {transfer.from_warehouse.name}',
                user=self.request.user
            )
        
        # Actualizar estado de la transferencia
        transfer.status = 'completed'
        transfer.completed_at = timezone.now()
        transfer.save()
        
        messages.success(self.request, 'Transferencia completada exitosamente')
        return redirect('inventory:transfer_detail', pk=transfer.pk)
