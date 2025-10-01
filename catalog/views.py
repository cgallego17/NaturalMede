from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, View, TemplateView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings
from .models import Product, Category, Brand, Cart, CartItem
from .forms import CartAddForm, CheckoutForm
from orders.models import Order, OrderItem, ShippingRate
from customers.models import Customer
import json


class HomeView(TemplateView):
    """Vista principal del ecommerce con secciones destacadas"""
    template_name = 'catalog/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Productos destacados (más vendidos o con mejor rating)
        featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
        
        # Categorías principales con productos
        main_categories = Category.objects.filter(is_active=True).annotate(
            product_count=Count('product', filter=Q(product__is_active=True))
        ).filter(product_count__gt=0).order_by('-product_count')[:6]
        
        # Productos por categoría para mostrar en cada sección
        for category in main_categories:
            category.products = Product.objects.filter(
                category=category, 
                is_active=True
            ).order_by('-created_at')[:4]
        
        # Estadísticas de la tienda
        total_products = Product.objects.filter(is_active=True).count()
        total_categories = Category.objects.filter(is_active=True).count()
        total_brands = Brand.objects.filter(is_active=True).count()
        
        context.update({
            'featured_products': featured_products,
            'main_categories': main_categories,
            'total_products': total_products,
            'total_categories': total_categories,
            'total_brands': total_brands,
        })
        
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')
        
        # Filtro por categoría
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            queryset = queryset.filter(category=category)
        
        # Filtro por marca
        brand_slug = self.kwargs.get('brand_slug')
        if brand_slug:
            brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
            queryset = queryset.filter(brand=brand)
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )
        
        # Ordenamiento
        sort_by = self.request.GET.get('sort')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-is_featured', '-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        context['featured_products'] = Product.objects.filter(is_active=True, is_featured=True)[:6]
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'catalog/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(category=self.object, is_active=True)
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        context['products'] = paginator.get_page(page_number)
        return context


class BrandDetailView(DetailView):
    model = Brand
    template_name = 'catalog/brand_detail.html'
    context_object_name = 'brand'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(brand=self.object, is_active=True)
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        context['products'] = paginator.get_page(page_number)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'brand')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(id=self.object.id)[:4]
        context['cart_form'] = CartAddForm()
        return context


class ProductSearchView(ListView):
    model = Product
    template_name = 'catalog/product_search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query),
                is_active=True
            ).select_related('category', 'brand')
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class CartView(View):
    template_name = 'catalog/cart.html'

    def get(self, request):
        cart = self.get_cart(request)
        return render(request, self.template_name, {'cart': cart})

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CartAddView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = self.get_cart(request)
        
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Producto agregado al carrito',
                'cart_total': cart.total_with_iva,
                'cart_items_count': cart.total_items
            })
        
        messages.success(request, 'Producto agregado al carrito')
        return redirect('catalog:cart')

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CartRemoveView(View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            cart = self.get_cart(request)
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado del carrito',
                'cart_total': cart.total_with_iva,
                'cart_items_count': cart.total_items
            })
        
        messages.success(request, 'Producto eliminado del carrito')
        return redirect('catalog:cart')

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CartUpdateView(View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        if request.headers.get('Content-Type') == 'application/json':
            cart = self.get_cart(request)
            return JsonResponse({
                'success': True,
                'message': 'Carrito actualizado',
                'cart_total': cart.total_with_iva,
                'cart_items_count': cart.total_items
            })
        
        messages.success(request, 'Carrito actualizado')
        return redirect('catalog:cart')

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CheckoutView(View):
    template_name = 'catalog/checkout.html'

    def get(self, request):
        cart = self.get_cart(request)
        if not cart.items.exists():
            messages.warning(request, 'Tu carrito está vacío')
            return redirect('catalog:product_list')
        
        form = CheckoutForm()
        return render(request, self.template_name, {'cart': cart, 'form': form})

    def post(self, request):
        cart = self.get_cart(request)
        if not cart.items.exists():
            messages.warning(request, 'Tu carrito está vacío')
            return redirect('catalog:product_list')
        
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Crear orden
            order = self.create_order(cart, form.cleaned_data)
            
            # Limpiar carrito
            cart.items.all().delete()
            
            messages.success(request, 'Tu orden ha sido creada exitosamente')
            return redirect('catalog:checkout_success', order_id=order.id)
        
        return render(request, self.template_name, {'cart': cart, 'form': form})

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart

    def create_order(self, cart, form_data):
        # Obtener o crear cliente
        if cart.user:
            customer, created = Customer.objects.get_or_create(user=cart.user)
        else:
            # Para usuarios no autenticados, crear un cliente temporal
            customer = Customer.objects.create(
                user=None,  # Esto requeriría modificar el modelo
                document_type='CC',
                document_number='TEMP',
                phone=form_data['phone'],
                address=form_data['address'],
                city=form_data['city']
            )
        
        # Crear orden
        order = Order.objects.create(
            customer=customer,
            payment_method=form_data['payment_method'],
            subtotal=cart.total_amount,
            iva_amount=cart.total_iva,
            shipping_cost=0,  # Calcular según la ciudad
            total=cart.total_with_iva,
            shipping_address=form_data['address'],
            shipping_city=form_data['city'],
            shipping_phone=form_data['phone'],
            notes=form_data.get('notes', '')
        )
        
        # Crear items de la orden
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                iva_percentage=cart_item.product.iva_percentage
            )
        
        return order


class CheckoutSuccessView(DetailView):
    model = Order
    template_name = 'catalog/checkout_success.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.all()


