from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Purchase, PurchaseItem, Supplier, PurchaseReceipt
from .forms import PurchaseForm, PurchaseItemFormSet, SupplierForm, PurchaseReceiptForm
from inventory.models import Stock, Warehouse
from catalog.models import Product, ProductImage


@login_required
def purchase_list(request):
    """Lista de compras"""
    purchases = Purchase.objects.select_related('supplier', 'created_by').prefetch_related('items').all()
    
    # Filtros
    search = request.GET.get('search')
    status = request.GET.get('status')
    supplier_id = request.GET.get('supplier')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if search:
        purchases = purchases.filter(
            Q(purchase_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(notes__icontains=search)
        )
    
    if status:
        purchases = purchases.filter(status=status)
    
    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)
    
    if start_date:
        purchases = purchases.filter(order_date__gte=start_date)
    
    if end_date:
        purchases = purchases.filter(order_date__lte=end_date)
    
    # Ordenar por fecha de creación descendente
    purchases = purchases.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(purchases, 20)
    page_number = request.GET.get('page')
    purchases = paginator.get_page(page_number)
    
    # Opciones para filtros
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    status_choices = Purchase.STATUS_CHOICES
    
    context = {
        'purchases': purchases,
        'suppliers': suppliers,
        'status_choices': status_choices,
        'current_search': search,
        'current_status': status,
        'current_supplier': supplier_id,
        'current_start_date': start_date,
        'current_end_date': end_date,
    }
    
    return render(request, 'purchases/purchase_list.html', context)


@login_required
def purchase_detail(request, pk):
    """Detalle de compra"""
    purchase = get_object_or_404(Purchase.objects.select_related(
        'supplier', 'created_by'
    ).prefetch_related('items__product'), pk=pk)
    
    context = {
        'purchase': purchase,
    }
    
    return render(request, 'purchases/purchase_detail.html', context)


@login_required
def purchase_create(request):
    """Crear nueva compra"""
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            
            # Guardar items
            formset.instance = purchase
            formset.save()
            
            messages.success(request, f'Compra #{purchase.purchase_number} creada exitosamente.')
            return redirect('purchases:purchase_detail', pk=purchase.pk)
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    
    return render(request, 'purchases/purchase_form.html', context)


@login_required
def purchase_edit(request, pk):
    """Editar compra"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'Compra #{purchase.purchase_number} actualizada exitosamente.')
            return redirect('purchases:purchase_detail', pk=purchase.pk)
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)
    
    context = {
        'form': form,
        'formset': formset,
        'purchase': purchase,
    }
    
    return render(request, 'purchases/purchase_form.html', context)


@login_required
def purchase_receive(request, pk):
    """Recibir compra"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if purchase.status != 'pending':
        messages.error(request, 'Solo se pueden recibir compras pendientes.')
        return redirect('purchases:purchase_detail', pk=pk)
    
    if request.method == 'POST':
        receipt_form = PurchaseReceiptForm(request.POST)
        
        if receipt_form.is_valid():
            # Crear recibo
            receipt = receipt_form.save(commit=False)
            receipt.purchase = purchase
            receipt.received_by = request.user
            receipt.save()
            
            # Actualizar estado de la compra
            purchase.status = 'received'
            purchase.received_date = timezone.now().date()
            purchase.save()
            
            # Actualizar stock
            for item in purchase.items.all():
                try:
                    # Obtener o crear stock en la bodega principal
                    warehouse = Warehouse.objects.filter(is_active=True).first()
                    if not warehouse:
                        warehouse = Warehouse.objects.create(
                            name='Bodega Principal',
                            location='Ubicación Central',
                            is_active=True
                        )
                    
                    stock, created = Stock.objects.get_or_create(
                        product=item.product,
                        warehouse=warehouse,
                        defaults={'quantity': 0, 'min_stock': 0}
                    )
                    
                    stock.quantity += item.quantity
                    stock.save()
                    
                except Exception as e:
                    messages.warning(request, f'Error actualizando stock de {item.product.name}: {str(e)}')
            
            messages.success(request, f'Compra #{purchase.purchase_number} recibida exitosamente.')
            return redirect('purchases:purchase_detail', pk=pk)
    else:
        receipt_form = PurchaseReceiptForm()
    
    context = {
        'purchase': purchase,
        'receipt_form': receipt_form,
    }
    
    return render(request, 'purchases/purchase_receive.html', context)


@login_required
def supplier_list(request):
    """Lista de proveedores"""
    suppliers = Supplier.objects.all()
    
    # Filtros
    search = request.GET.get('search')
    is_active = request.GET.get('is_active')
    
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(contact_person__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if is_active is not None and is_active != '':
        suppliers = suppliers.filter(is_active=is_active == 'true')
    
    # Ordenar por nombre
    suppliers = suppliers.order_by('name')
    
    # Paginación
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers,
        'current_search': search,
        'current_is_active': is_active,
    }
    
    return render(request, 'purchases/supplier_list.html', context)


@login_required
def supplier_detail(request, pk):
    """Detalle de proveedor"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Obtener compras recientes
    recent_purchases = supplier.purchases.order_by('-created_at')[:10]
    
    # Estadísticas
    total_purchases = supplier.purchase_count
    total_amount = supplier.total_purchases
    
    context = {
        'supplier': supplier,
        'recent_purchases': recent_purchases,
        'total_purchases': total_purchases,
        'total_amount': total_amount,
    }
    
    return render(request, 'purchases/supplier_detail.html', context)


@login_required
def supplier_create(request):
    """Crear proveedor"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Proveedor {supplier.name} creado exitosamente.')
            return redirect('purchases:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'purchases/supplier_form.html', context)


@login_required
def supplier_edit(request, pk):
    """Editar proveedor"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Proveedor {supplier.name} actualizado exitosamente.')
            return redirect('purchases:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
    }
    
    return render(request, 'purchases/supplier_form.html', context)


@login_required
def purchase_dashboard(request):
    """Dashboard de compras"""
    # Estadísticas generales
    total_purchases = Purchase.objects.count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    
    # Compras por estado
    purchases_by_status = {}
    for status, status_display in Purchase.STATUS_CHOICES:
        count = Purchase.objects.filter(status=status).count()
        purchases_by_status[status_display] = count
    
    # Compras recientes
    recent_purchases = Purchase.objects.select_related('supplier', 'created_by').order_by('-created_at')[:10]
    
    # Top proveedores
    top_suppliers = Supplier.objects.annotate(
        purchase_count=models.Count('purchases'),
        total_amount=models.Sum('purchases__total')
    ).filter(purchase_count__gt=0).order_by('-total_amount')[:5]
    
    # Compras del mes actual
    current_month = timezone.now().replace(day=1)
    monthly_purchases = Purchase.objects.filter(
        created_at__gte=current_month
    ).aggregate(
        count=models.Count('id'),
        total=models.Sum('total')
    )
    
    context = {
        'total_purchases': total_purchases,
        'total_suppliers': total_suppliers,
        'purchases_by_status': purchases_by_status,
        'recent_purchases': recent_purchases,
        'top_suppliers': top_suppliers,
        'monthly_purchases': monthly_purchases,
    }
    
    return render(request, 'purchases/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def purchase_cancel(request, pk):
    """Cancelar compra"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if purchase.status in ['received', 'cancelled']:
        messages.error(request, 'No se puede cancelar una compra recibida o ya cancelada.')
    else:
        purchase.status = 'cancelled'
        purchase.save()
        messages.success(request, f'Compra #{purchase.purchase_number} cancelada.')
    
    return redirect('purchases:purchase_detail', pk=pk)


@login_required
def api_products_for_purchase(request):
    """API para obtener productos para compras"""
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    
    data = []
    for product in products:
        data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
            'current_price': float(product.price),
        })
    
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def api_products(request):
    """API para obtener productos con información completa"""
    products = Product.objects.select_related('category', 'brand').prefetch_related('images').all()
    
    data = []
    for product in products:
        # Obtener imagen principal
        primary_image = product.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = product.images.first()
        
        image_url = primary_image.image.url if primary_image else None
        
        data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'price': float(product.price),
            'image_url': image_url,
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
            'stock': 0,  # Se puede calcular si es necesario
        })
    
    return JsonResponse(data, safe=False)