from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from .models import Customer, CustomerAddress
from .forms import CustomerForm, CustomerAddressForm


class CustomerListView(ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

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
                Q(document_number__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        return queryset.order_by('user__last_name', 'user__first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer_types'] = Customer.CUSTOMER_TYPES
        return context


class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Customer.objects.select_related('user').prefetch_related('addresses', 'orders')


class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cliente creado exitosamente')
        return response


class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cliente actualizado exitosamente')
        return response


class CustomerAddressListView(ListView):
    model = CustomerAddress
    template_name = 'customers/customer_address_list.html'
    context_object_name = 'addresses'
    paginate_by = 10

    def get_queryset(self):
        customer = get_object_or_404(Customer, pk=self.kwargs['pk'])
        return CustomerAddress.objects.filter(customer=customer).order_by('-is_default', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = get_object_or_404(Customer, pk=self.kwargs['pk'])
        return context


class CustomerAddressCreateView(CreateView):
    model = CustomerAddress
    form_class = CustomerAddressForm
    template_name = 'customers/customer_address_form.html'

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['pk'])
        form.instance.customer = customer
        response = super().form_valid(form)
        messages.success(self.request, 'Dirección creada exitosamente')
        return response

    def get_success_url(self):
        return reverse_lazy('customers:customer_address_list', kwargs={'pk': self.kwargs['pk']})


class CustomerAddressUpdateView(UpdateView):
    model = CustomerAddress
    form_class = CustomerAddressForm
    template_name = 'customers/customer_address_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Dirección actualizada exitosamente')
        return response

    def get_success_url(self):
        return reverse_lazy('customers:customer_address_list', kwargs={'pk': self.object.customer.pk})


class CustomerAddressDeleteView(DeleteView):
    model = CustomerAddress
    template_name = 'customers/customer_address_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Dirección eliminada exitosamente')
        return response

    def get_success_url(self):
        return reverse_lazy('customers:customer_address_list', kwargs={'pk': self.object.customer.pk})


class VIPCustomerListView(ListView):
    model = Customer
    template_name = 'customers/vip_customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        return Customer.objects.filter(
            customer_type='vip',
            is_active=True
        ).select_related('user').order_by('user__last_name', 'user__first_name')













