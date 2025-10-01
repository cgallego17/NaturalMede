from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from .models import Order, OrderItem, ShippingRate
from .forms import OrderForm, ShippingRateForm
from customers.models import Customer
from inventory.models import Stock
import json


class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = Order.objects.select_related('customer__user').all()
        
        # Filtro por estado
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por método de pago
        payment_filter = self.request.GET.get('payment_method')
        if payment_filter:
            queryset = queryset.filter(payment_method=payment_filter)
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(customer__user__first_name__icontains=search_query) |
                Q(customer__user__last_name__icontains=search_query) |
                Q(customer__user__email__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_methods'] = Order.PAYMENT_METHODS
        return context


class OrderDetailView(DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Order.objects.select_related('customer__user').prefetch_related('items__product')


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('orders:order_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Orden creada exitosamente')
        return response


class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('orders:order_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Orden actualizada exitosamente')
        return response


class OrderStatusUpdateView(UpdateView):
    model = Order
    fields = ['status']
    template_name = 'orders/order_status_update.html'
    success_url = reverse_lazy('orders:order_list')

    def form_valid(self, form):
        old_status = self.object.status
        new_status = form.cleaned_data['status']
        
        # Validar transición de estado
        if not self.is_valid_status_transition(old_status, new_status):
            messages.error(self.request, f'No se puede cambiar de {old_status} a {new_status}')
            return redirect('orders:order_detail', pk=self.object.pk)
        
        response = super().form_valid(form)
        
        # Actualizar fechas según el estado
        if new_status == 'paid':
            self.object.paid_at = timezone.now()
        elif new_status == 'shipped':
            self.object.shipped_at = timezone.now()
        elif new_status == 'delivered':
            self.object.delivered_at = timezone.now()
        
        self.object.save()
        
        messages.success(self.request, f'Estado actualizado a {self.object.get_status_display()}')
        return response

    def is_valid_status_transition(self, old_status, new_status):
        """Valida si la transición de estado es válida"""
        valid_transitions = {
            'new': ['pending', 'cancelled'],
            'pending': ['paid', 'cancelled'],
            'paid': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        return new_status in valid_transitions.get(old_status, [])


class OrderInvoiceView(DetailView):
    model = Order
    template_name = 'orders/order_invoice.html'
    context_object_name = 'order'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Order.objects.select_related('customer__user').prefetch_related('items__product')


class ShippingRateListView(ListView):
    model = ShippingRate
    template_name = 'orders/shipping_rate_list.html'
    context_object_name = 'shipping_rates'
    paginate_by = 20

    def get_queryset(self):
        return ShippingRate.objects.all().order_by('city', 'min_weight')


class ShippingRateCreateView(CreateView):
    model = ShippingRate
    form_class = ShippingRateForm
    template_name = 'orders/shipping_rate_form.html'
    success_url = reverse_lazy('orders:shipping_rate_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Tarifa de envío creada exitosamente')
        return response


class ShippingRateUpdateView(UpdateView):
    model = ShippingRate
    form_class = ShippingRateForm
    template_name = 'orders/shipping_rate_form.html'
    success_url = reverse_lazy('orders:shipping_rate_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Tarifa de envío actualizada exitosamente')
        return response


class ShippingRateDeleteView(DeleteView):
    model = ShippingRate
    template_name = 'orders/shipping_rate_confirm_delete.html'
    success_url = reverse_lazy('orders:shipping_rate_list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Tarifa de envío eliminada exitosamente')
        return response
