from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, View
from django.db.models import Q, Sum, Count, Avg, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json
from .models import ReportTemplate, ReportSchedule
from orders.models import Order, OrderItem
from catalog.models import Product
from customers.models import Customer
from pos.models import POSSale, POSSaleItem
from inventory.models import Stock, StockMovement


class ReportsDashboardView(ListView):
    template_name = 'reports/dashboard.html'
    context_object_name = 'recent_reports'

    def get_queryset(self):
        return ReportTemplate.objects.filter(is_active=True).order_by('-created_at')[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        # Ventas del día
        context['today_sales'] = Order.objects.filter(
            created_at__date=today,
            status__in=['paid', 'shipped', 'delivered']
        ).aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total')
        )
        
        # Ventas del mes
        context['month_sales'] = Order.objects.filter(
            created_at__date__gte=this_month,
            status__in=['paid', 'shipped', 'delivered']
        ).aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total')
        )
        
        # Productos más vendidos
        context['top_products'] = OrderItem.objects.filter(
            order__created_at__date__gte=this_month,
            order__status__in=['paid', 'shipped', 'delivered']
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total')
        ).order_by('-total_quantity')[:5]
        
        # Clientes más activos
        context['top_customers'] = Customer.objects.annotate(
            total_orders=Count('orders'),
            total_spent=Sum('orders__total', filter=Q(orders__status='delivered'))
        ).order_by('-total_spent')[:5]
        
        return context


class SalesReportView(ListView):
    template_name = 'reports/sales_report.html'
    context_object_name = 'orders'
    paginate_by = 50

    def get_queryset(self):
        queryset = Order.objects.select_related('customer__user').all()
        
        # Filtros de fecha
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Filtro por estado
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por método de pago
        payment_filter = self.request.GET.get('payment_method')
        if payment_filter:
            queryset = queryset.filter(payment_method=payment_filter)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del reporte
        queryset = self.get_queryset()
        context['stats'] = queryset.aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total'),
            avg_order_value=Avg('total')
        )
        
        # Ventas por estado
        context['sales_by_status'] = queryset.values('status').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')
        
        # Ventas por método de pago
        context['sales_by_payment'] = queryset.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')
        
        # Ventas por día
        context['sales_by_day'] = queryset.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('day')
        
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_methods'] = Order.PAYMENT_METHODS
        
        return context


class InventoryReportView(ListView):
    template_name = 'reports/inventory_report.html'
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
        
        return queryset.order_by('product__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del inventario
        queryset = self.get_queryset()
        context['stats'] = queryset.aggregate(
            total_products=Count('id'),
            total_value=Sum(F('quantity') * F('product__cost_price')),
            low_stock_count=Count('id', filter=Q(quantity__lte=F('min_stock'))),
            out_of_stock_count=Count('id', filter=Q(quantity=0))
        )
        
        # Stock por bodega
        context['stock_by_warehouse'] = queryset.values('warehouse__name').annotate(
            total_products=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__cost_price'))
        ).order_by('-total_value')
        
        # Productos con más movimiento
        context['top_movements'] = StockMovement.objects.filter(
            created_at__date__gte=timezone.now().date() - timedelta(days=30)
        ).values('product__name').annotate(
            total_movements=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-total_movements')[:10]
        
        from inventory.models import Warehouse
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        
        return context


class ProductsReportView(ListView):
    template_name = 'reports/products_report.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')
        
        # Filtro por categoría
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtro por marca
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas de productos
        queryset = self.get_queryset()
        context['stats'] = queryset.aggregate(
            total_products=Count('id'),
            avg_price=Avg('price'),
            total_value=Sum(F('price') * F('stock__quantity'))
        )
        
        # Productos más vendidos
        context['top_selling'] = OrderItem.objects.filter(
            order__created_at__date__gte=timezone.now().date() - timedelta(days=30),
            order__status__in=['paid', 'shipped', 'delivered']
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total')
        ).order_by('-total_quantity')[:10]
        
        # Productos por categoría
        context['products_by_category'] = queryset.values('category__name').annotate(
            count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-count')
        
        from catalog.models import Category, Brand
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        
        return context


class CustomersReportView(ListView):
    template_name = 'reports/customers_report.html'
    context_object_name = 'customers'
    paginate_by = 50

    def get_queryset(self):
        queryset = Customer.objects.filter(is_active=True).select_related('user')
        
        # Filtro por tipo de cliente
        customer_type = self.request.GET.get('customer_type')
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(document_number__icontains=search_query)
            )
        
        return queryset.annotate(
            total_orders=Count('orders'),
            total_spent=Sum('orders__total', filter=Q(orders__status='delivered'))
        ).order_by('-total_spent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas de clientes
        queryset = self.get_queryset()
        context['stats'] = queryset.aggregate(
            total_customers=Count('id'),
            vip_customers=Count('id', filter=Q(customer_type='vip')),
            avg_orders_per_customer=Avg('total_orders'),
            avg_spent_per_customer=Avg('total_spent')
        )
        
        # Clientes por tipo
        context['customers_by_type'] = queryset.values('customer_type').annotate(
            count=Count('id'),
            avg_spent=Avg('total_spent')
        ).order_by('-count')
        
        # Clientes por ciudad
        context['customers_by_city'] = queryset.values('city').annotate(
            count=Count('id'),
            avg_spent=Avg('total_spent')
        ).order_by('-count')[:10]
        
        context['customer_types'] = Customer.CUSTOMER_TYPES
        
        return context


class FinancialReportView(ListView):
    template_name = 'reports/financial_report.html'
    context_object_name = 'orders'
    paginate_by = 50

    def get_queryset(self):
        queryset = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered']
        ).select_related('customer__user')
        
        # Filtros de fecha
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas financieras
        queryset = self.get_queryset()
        context['stats'] = queryset.aggregate(
            total_revenue=Sum('total'),
            total_orders=Count('id'),
            avg_order_value=Avg('total'),
            total_iva=Sum('iva_amount'),
            total_shipping=Sum('shipping_cost')
        )
        
        # Ingresos por método de pago
        context['revenue_by_payment'] = queryset.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')
        
        # Ingresos por mes
        context['revenue_by_month'] = queryset.extra(
            select={'month': 'strftime("%Y-%m", created_at)'}
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('month')
        
        # Comparación con mes anterior
        if queryset.exists():
            current_month = timezone.now().date().replace(day=1)
            last_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_revenue = queryset.filter(
                created_at__date__gte=current_month
            ).aggregate(total=Sum('total'))['total'] or 0
            
            last_revenue = Order.objects.filter(
                created_at__date__gte=last_month,
                created_at__date__lt=current_month,
                status__in=['paid', 'shipped', 'delivered']
            ).aggregate(total=Sum('total'))['total'] or 0
            
            if last_revenue > 0:
                growth = ((current_revenue - last_revenue) / last_revenue) * 100
                context['revenue_growth'] = round(growth, 2)
            else:
                context['revenue_growth'] = 0
        
        return context


class ReportExportView(View):
    def get(self, request, report_type):
        if report_type == 'sales':
            return self.export_sales_report(request)
        elif report_type == 'inventory':
            return self.export_inventory_report(request)
        elif report_type == 'products':
            return self.export_products_report(request)
        elif report_type == 'customers':
            return self.export_customers_report(request)
        elif report_type == 'financial':
            return self.export_financial_report(request)
        else:
            return JsonResponse({'error': 'Tipo de reporte no válido'}, status=400)

    def export_sales_report(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Número de Orden', 'Cliente', 'Estado', 'Método de Pago',
            'Subtotal', 'IVA', 'Costo de Envío', 'Total', 'Fecha'
        ])
        
        orders = Order.objects.select_related('customer__user').all()
        
        # Aplicar filtros
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status_filter = request.GET.get('status')
        
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        for order in orders:
            writer.writerow([
                order.order_number,
                order.customer.full_name,
                order.get_status_display(),
                order.get_payment_method_display(),
                order.subtotal,
                order.iva_amount,
                order.shipping_cost,
                order.total,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response

    def export_inventory_report(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Producto', 'SKU', 'Bodega', 'Cantidad', 'Stock Mínimo',
            'Stock Máximo', 'Precio de Costo', 'Valor Total'
        ])
        
        stocks = Stock.objects.select_related('product', 'warehouse').all()
        
        for stock in stocks:
            writer.writerow([
                stock.product.name,
                stock.product.sku,
                stock.warehouse.name,
                stock.quantity,
                stock.min_stock,
                stock.max_stock,
                stock.product.cost_price,
                stock.quantity * stock.product.cost_price
            ])
        
        return response

    def export_products_report(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Nombre', 'SKU', 'Categoría', 'Marca', 'Precio',
            'Precio de Costo', 'IVA %', 'Stock Total', 'Valor Total'
        ])
        
        products = Product.objects.filter(is_active=True).select_related('category', 'brand')
        
        for product in products:
            total_stock = Stock.objects.filter(product=product).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            writer.writerow([
                product.name,
                product.sku,
                product.category.name,
                product.brand.name,
                product.price,
                product.cost_price,
                product.iva_percentage,
                total_stock,
                total_stock * product.cost_price
            ])
        
        return response

    def export_customers_report(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Nombre', 'Email', 'Teléfono', 'Tipo', 'Ciudad',
            'Total Órdenes', 'Total Gastado', 'Fecha Registro'
        ])
        
        customers = Customer.objects.filter(is_active=True).select_related('user').annotate(
            total_orders=Count('orders'),
            total_spent=Sum('orders__total', filter=Q(orders__status='delivered'))
        )
        
        for customer in customers:
            writer.writerow([
                customer.full_name,
                customer.email,
                customer.phone,
                customer.get_customer_type_display(),
                customer.city,
                customer.total_orders,
                customer.total_spent or 0,
                customer.created_at.strftime('%Y-%m-%d')
            ])
        
        return response

    def export_financial_report(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Fecha', 'Número de Orden', 'Cliente', 'Método de Pago',
            'Subtotal', 'IVA', 'Costo de Envío', 'Total'
        ])
        
        orders = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered']
        ).select_related('customer__user')
        
        # Aplicar filtros de fecha
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)
        
        for order in orders:
            writer.writerow([
                order.created_at.strftime('%Y-%m-%d'),
                order.order_number,
                order.customer.full_name,
                order.get_payment_method_display(),
                order.subtotal,
                order.iva_amount,
                order.shipping_cost,
                order.total
            ])
        
        return response
