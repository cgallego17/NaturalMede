from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import POSSession, POSSale, POSSaleItem
from .forms import POSSaleForm, POSSaleItemForm
from catalog.models import Product
from inventory.models import Warehouse, Stock
from customers.models import Customer
import json


class POSDashboardView(LoginRequiredMixin, ListView):
    template_name = 'pos/dashboard.html'
    context_object_name = 'recent_sales'

    def get_queryset(self):
        return POSSale.objects.select_related(
            'session', 'customer__user'
        ).order_by('-created_at')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Sesión activa
        context['active_session'] = POSSession.objects.filter(
            user=self.request.user,
            status='open'
        ).first()
        
        # Estadísticas del día
        today = timezone.now().date()
        today_sales_data = POSSale.objects.filter(
            created_at__date=today
        ).aggregate(
            total_sales=Sum('total'),
            total_transactions=Count('id')
        )
        
        # Calcular promedio de ventas
        if today_sales_data['total_transactions'] and today_sales_data['total_transactions'] > 0:
            today_sales_data['average_sale'] = today_sales_data['total_sales'] / today_sales_data['total_transactions']
        else:
            today_sales_data['average_sale'] = 0
            
        context['today_sales'] = today_sales_data
        
        # Productos más vendidos
        context['top_products'] = POSSaleItem.objects.filter(
            sale__created_at__date=today
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total')
        ).order_by('-total_quantity')[:5]
        
        return context


class POSSessionView(LoginRequiredMixin, ListView):
    model = POSSession
    template_name = 'pos/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        return POSSession.objects.filter(
            user=self.request.user
        ).order_by('-opened_at')


class POSSessionOpenView(LoginRequiredMixin, CreateView):
    model = POSSession
    fields = ['warehouse', 'opening_cash']
    template_name = 'pos/session_open.html'
    success_url = reverse_lazy('pos:dashboard')

    def form_valid(self, form):
        # Verificar que no haya una sesión abierta
        if POSSession.objects.filter(user=self.request.user, status='open').exists():
            messages.error(self.request, 'Ya tienes una sesión abierta')
            return redirect('pos:dashboard')
        
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Sesión POS abierta exitosamente')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context


class POSSessionCloseView(LoginRequiredMixin, UpdateView):
    model = POSSession
    fields = ['closing_cash']
    template_name = 'pos/session_close.html'
    success_url = reverse_lazy('pos:dashboard')

    def get_queryset(self):
        return POSSession.objects.filter(
            user=self.request.user,
            status='open'
        )

    def form_valid(self, form):
        session = self.object
        
        # Calcular totales de la sesión
        sales = POSSale.objects.filter(session=session)
        session.total_sales = sales.aggregate(total=Sum('total'))['total'] or 0
        session.total_transactions = sales.count()
        session.status = 'closed'
        session.closed_at = timezone.now()
        
        response = super().form_valid(form)
        messages.success(self.request, 'Sesión POS cerrada exitosamente')
        return response


class POSSaleView(LoginRequiredMixin, ListView):
    model = POSSale
    template_name = 'pos/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        return POSSale.objects.select_related(
            'session', 'customer__user'
        ).order_by('-created_at')


class POSSaleCreateView(LoginRequiredMixin, CreateView):
    model = POSSale
    form_class = POSSaleForm
    template_name = 'pos/sale_form.html'
    success_url = reverse_lazy('pos:sale_list')

    def form_valid(self, form):
        # Obtener sesión activa
        active_session = POSSession.objects.filter(
            user=self.request.user,
            status='open'
        ).first()
        
        if not active_session:
            messages.error(self.request, 'No hay una sesión POS abierta')
            return redirect('pos:dashboard')
        
        form.instance.session = active_session
        response = super().form_valid(form)
        messages.success(self.request, 'Venta POS creada exitosamente')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(is_active=True)
        context['products'] = Product.objects.filter(is_active=True)
        return context


class POSSaleDetailView(LoginRequiredMixin, DetailView):
    model = POSSale
    template_name = 'pos/sale_detail.html'
    context_object_name = 'sale'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return POSSale.objects.select_related(
            'session', 'customer__user'
        ).prefetch_related('items__product')


class POSSalePrintView(LoginRequiredMixin, DetailView):
    model = POSSale
    template_name = 'pos/sale_print.html'
    context_object_name = 'sale'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return POSSale.objects.select_related(
            'session', 'customer__user'
        ).prefetch_related('items__product')


class POSSaleEmailView(LoginRequiredMixin, View):
    """Vista para enviar recibo de venta POS por correo"""
    
    def post(self, request, pk):
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        sale = get_object_or_404(POSSale.objects.select_related(
            'session', 'customer__user'
        ).prefetch_related('items__product'), pk=pk)
        
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Debe proporcionar una dirección de correo')
            return redirect('pos:sale_detail', pk=sale.id)
        
        try:
            # Renderizar el recibo como HTML
            html_content = render_to_string('pos/sale_print.html', {
                'sale': sale,
                'email_mode': True
            })
            
            # Enviar correo
            subject = f'Recibo de Venta #{sale.sale_number} - NaturalMede'
            send_mail(
                subject=subject,
                message='',  # Mensaje vacío porque usamos HTML
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            messages.success(request, f'Recibo enviado exitosamente a {email}')
            
        except Exception as e:
            messages.error(request, f'Error al enviar el correo: {str(e)}')
        
        return redirect('pos:sale_detail', pk=sale.id)


class BarcodeScanView(LoginRequiredMixin, View):
    def post(self, request):
        barcode = request.POST.get('barcode')
        
        if not barcode:
            return JsonResponse({'error': 'Código de barras requerido'}, status=400)
        
        try:
            product = Product.objects.get(barcode=barcode, is_active=True)
            
            # Verificar stock
            stock = Stock.objects.filter(
                product=product,
                warehouse__is_main=True
            ).first()
            
            if not stock or stock.quantity <= 0:
                return JsonResponse({
                    'error': 'Producto sin stock',
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': float(product.price),
                        'available': False
                    }
                })
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'available': True,
                    'stock': stock.quantity
                }
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)


class QuickSaleView(LoginRequiredMixin, View):
    template_name = 'pos/quick_sale.html'

    def get(self, request):
        # Obtener sesión activa
        active_session = POSSession.objects.filter(
            user=request.user,
            status='open'
        ).first()
        
        if not active_session:
            messages.error(request, 'No hay una sesión POS abierta')
            return redirect('pos:dashboard')
        
        # Productos más vendidos para venta rápida
        top_products = POSSaleItem.objects.filter(
            sale__created_at__date=timezone.now().date()
        ).values(
            'product__id', 'product__name', 'product__price'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:10]
        
        context = {
            'active_session': active_session,
            'top_products': top_products,
            'products': Product.objects.filter(is_active=True)[:20]
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        # Obtener sesión activa
        active_session = POSSession.objects.filter(
            user=request.user,
            status='open'
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No hay una sesión POS abierta'}, status=400)
        
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Verificar stock
            stock = Stock.objects.filter(
                product=product,
                warehouse=active_session.warehouse
            ).first()
            
            if not stock or stock.quantity < quantity:
                return JsonResponse({'error': 'Stock insuficiente'}, status=400)
            
            # Crear venta rápida
            sale = POSSale.objects.create(
                session=active_session,
                payment_method='cash',
                subtotal=product.price * quantity,
                iva_amount=(product.price * quantity) * (product.iva_percentage / 100),
                total=(product.price * quantity) * (1 + product.iva_percentage / 100)
            )
            
            # Crear item de venta
            POSSaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                iva_percentage=product.iva_percentage
            )
            
            # Actualizar stock
            stock.quantity -= quantity
            stock.save()
            
            # Crear movimiento de stock
            from inventory.models import StockMovement
            StockMovement.objects.create(
                product=product,
                warehouse=active_session.warehouse,
                movement_type='out',
                quantity=-quantity,
                reference=f'Venta POS {sale.sale_number}',
                user=request.user
            )
            
            return JsonResponse({
                'success': True,
                'sale': {
                    'id': sale.id,
                    'sale_number': sale.sale_number,
                    'total': float(sale.total)
                }
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

