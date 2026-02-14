from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, View, TemplateView
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Product, Category, Brand, Cart, CartItem
from .forms import CartAddForm, CheckoutForm
from orders.models import Order, OrderItem, ShippingRate
from customers.models import Customer, City
from .wompi_views import create_wompi_transaction
import json
from decimal import Decimal

FIXED_SHIPPING_COST = Decimal('13000.00')


def merge_session_cart_into_user_cart(request, user):
    if not request.session.session_key:
        request.session.create()

    session_cart = Cart.objects.filter(session_key=request.session.session_key).first()
    if not session_cart or not session_cart.items.exists():
        Cart.objects.get_or_create(user=user)
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.items.select_related('product').all():
        existing = CartItem.objects.filter(cart=user_cart, product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()

    CartItem.objects.filter(cart=session_cart).delete()
    try:
        session_cart.delete()
    except Exception:
        pass


class FrontendLoginView(View):
    template_name = 'catalog/login.html'

    def get(self, request):
        next_url = request.GET.get('next') or ''
        return render(request, self.template_name, {'next': next_url})

    def post(self, request):
        username_or_email = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        next_url = request.POST.get('next') or request.GET.get('next') or '/'
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = '/'

        if not username_or_email or not password:
            messages.error(request, 'Debes ingresar email/usuario y contraseña.')
            return render(request, self.template_name, {'next': next_url})

        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            by_email = User.objects.filter(email__iexact=username_or_email).first()
            if by_email:
                user = authenticate(request, username=by_email.username, password=password)

        if user is None:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, self.template_name, {'next': next_url})

        merge_session_cart_into_user_cart(request, user)
        login(request, user)
        return redirect(next_url)


class HomeView(TemplateView):
    """Vista principal del ecommerce con productos dinámicos"""
    template_name = 'catalog/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener productos recientes para la sección RECENT PRODUCTS
        recent_products = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:6]  # Últimos 6 productos
        
        # Obtener productos destacados (si tienes un campo featured)
        featured_products = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('?')[:3]  # 3 productos aleatorios como destacados
        
        # Obtener producto más vendido para la sección supplement
        featured_product = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').annotate(
            total_sold=Sum('orderitem__quantity')
        ).order_by('-total_sold', '-created_at').first()

        # Si no hay ventas registradas, usar el más reciente
        if (not featured_product or not getattr(featured_product, 'total_sold', None)) and recent_products:
            featured_product = recent_products.first()
        
        # Obtener producto destacado para el banner
        banner_product = Product.objects.filter(
            id=14,
            is_active=True,
        ).select_related('category', 'brand').prefetch_related('images').first()
        
        # Si no hay productos, usar el primero de recent_products
        if not banner_product and recent_products:
            banner_product = recent_products.first()
        
        # Obtener producto destacado para la sección shop-details
        shop_featured_product = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('?').first()
        
        # Si no hay productos, usar el primero de recent_products
        if not shop_featured_product and recent_products:
            shop_featured_product = recent_products.first()
        
        # Obtener 3 productos para la sección de planes/precios
        pricing_products = list(Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('?')[:3])
        
        # Si no hay suficientes productos, usar los de recent_products
        if len(pricing_products) < 3 and recent_products:
            for product in recent_products:
                if product not in pricing_products and len(pricing_products) < 3:
                    pricing_products.append(product)
        
        context.update({
            'recent_products': recent_products,
            'featured_products': featured_products,
            'featured_product': featured_product,
            'banner_product': banner_product,
            'shop_featured_product': shop_featured_product,
            'pricing_products': pricing_products,
        })
        
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
        
        # Filtro por categoría (desde URL o GET)
        category_slug = self.kwargs.get('category_slug') or self.request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                pass
        
        # Filtro por marca (desde URL o GET)
        brand_slug = self.kwargs.get('brand_slug') or self.request.GET.get('brand')
        if brand_slug:
            try:
                brand = Brand.objects.get(slug=brand_slug, is_active=True)
                queryset = queryset.filter(brand=brand)
            except Brand.DoesNotExist:
                pass
        
        # Filtro por precio
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except (ValueError, TypeError):
                pass
        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except (ValueError, TypeError):
                pass
        
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
        sort_by = self.request.GET.get('sort') or self.request.GET.get('orderby')
        if sort_by == 'price' or sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price-desc' or sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'date' or sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'popularity':
            queryset = queryset.order_by('-is_featured', '-created_at')
        else:
            queryset = queryset.order_by('-is_featured', '-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Categorías activas con slugs válidos para el sidebar
        context['categories'] = Category.objects.filter(
            is_active=True
        ).exclude(slug='').exclude(slug__isnull=True).order_by('name')
        
        # Marcas activas
        context['brands'] = Brand.objects.filter(is_active=True).order_by('name')
        
        # Productos destacados
        context['featured_products'] = Product.objects.filter(
            is_active=True, 
            is_featured=True
        ).prefetch_related('images')[:6]
        
        # Últimos productos para el sidebar
        context['latest_products'] = Product.objects.filter(
            is_active=True
        ).prefetch_related('images').order_by('-created_at')[:3]
        
        # Rango de precios para el filtro
        from django.db.models import Min, Max
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = int(price_range['min_price'] or 0)
        context['max_price'] = int(price_range['max_price'] or 100000)
        
        # Filtro por categoría desde GET
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                context['selected_category'] = Category.objects.get(slug=category_slug, is_active=True)
            except Category.DoesNotExist:
                context['selected_category'] = None
        else:
            context['selected_category'] = None
        
        # Filtro por marca desde GET
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            try:
                context['selected_brand'] = Brand.objects.get(slug=brand_slug, is_active=True)
            except Brand.DoesNotExist:
                context['selected_brand'] = None
        else:
            context['selected_brand'] = None
        
        # Filtro por precio desde GET
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
        
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
        products = Product.objects.filter(category=self.object, is_active=True).prefetch_related('images')
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
        
        # Return JSON if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart_items = []
            for item in cart.items.all().select_related('product').prefetch_related('product__images'):
                image_url = ''
                try:
                    if item.product.images.exists():
                        first_image = item.product.images.first()
                        if first_image and first_image.image:
                            # Use simple URL instead of build_absolute_uri to avoid errors
                            image_url = first_image.image.url
                except Exception as e:
                    # If image URL fails, use empty string
                    image_url = ''
                
                try:
                    # Use total property from CartItem model
                    item_total = float(item.total) if hasattr(item, 'total') and item.total else 0.0
                    if item_total == 0.0:
                        # Fallback calculation
                        item_total = float(item.product.price) * item.quantity if item.product.price else 0.0
                    
                    cart_items.append({
                        'id': item.id,
                        'product_id': item.product.id,
                        'product_name': item.product.name or 'Producto sin nombre',
                        'product_image': image_url,
                        'quantity': item.quantity,
                        'price': float(item.product.price) if item.product.price else 0.0,
                        'subtotal': item_total
                    })
                except Exception as e:
                    # Skip items that cause errors, but log them
                    import traceback
                    print(f"Error processing cart item {item.id}: {e}")
                    print(traceback.format_exc())
                    continue
            
            try:
                # Calculate totals safely
                cart_total = 0.0
                cart_items_count = 0
                
                try:
                    # Use the property from Cart model
                    cart_total = float(cart.total_with_iva) if cart.total_with_iva else 0.0
                except Exception as e:
                    # Calculate manually if property fails
                    try:
                        for item in cart.items.all():
                            if hasattr(item, 'total_with_iva'):
                                cart_total += float(item.total_with_iva) if item.total_with_iva else 0.0
                            elif hasattr(item, 'total'):
                                cart_total += float(item.total) if item.total else 0.0
                    except:
                        cart_total = 0.0
                
                try:
                    # Use the property from Cart model
                    cart_items_count = cart.total_items if cart.total_items else 0
                except:
                    # Calculate manually
                    cart_items_count = sum(item.quantity for item in cart.items.all())
                
                return JsonResponse({
                    'success': True,
                    'cart_items': cart_items,
                    'cart_total': cart_total,
                    'cart_items_count': cart_items_count
                })
            except Exception as e:
                # Fallback response if there's an error
                import traceback
                print(f"Error in CartView JSON response: {e}")
                print(traceback.format_exc())
                return JsonResponse({
                    'success': True,
                    'cart_items': [],
                    'cart_total': 0.0,
                    'cart_items_count': 0
                })
        
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
        import json
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = self.get_cart(request)
        
        # Handle both JSON and form data
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                quantity = int(data.get('quantity', 1))
            except (json.JSONDecodeError, ValueError, TypeError):
                quantity = 1
        else:
            quantity = int(request.POST.get('quantity', 1))
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Producto agregado al carrito exitosamente',
                'cart_total': float(cart.total_with_iva),
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
            if form.cleaned_data.get('create_account') and not request.user.is_authenticated:
                email = (form.cleaned_data.get('email') or '').strip().lower()
                password = form.cleaned_data.get('password1') or ''
                first_name = (form.cleaned_data.get('first_name') or '').strip()
                last_name = (form.cleaned_data.get('last_name') or '').strip()

                if User.objects.filter(username=email).exists() or User.objects.filter(email__iexact=email).exists():
                    messages.error(request, 'Ya existe una cuenta con ese email. Inicia sesión para continuar.')
                    return redirect('custom_admin:home_login')

                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                self._get_or_create_customer(user, form.cleaned_data)
                merge_session_cart_into_user_cart(request, user)
                login(request, user)
                cart = Cart.objects.get_or_create(user=user)[0]

            # Asegurar que el método de pago sea Wompi
            form.cleaned_data['payment_method'] = 'wompi'
            
            # Crear orden
            order = self.create_order(cart, form.cleaned_data)
            
            # Preparar datos para el widget de Wompi
            wompi_data, error = create_wompi_transaction(order)
            if error:
                messages.error(request, f'Error al preparar pago Wompi: {error}')
                return render(request, self.template_name, {'cart': cart, 'form': form})

            checkout_url = (wompi_data or {}).get('checkout_url')
            if checkout_url and not settings.DEBUG:
                return redirect(checkout_url)
            
            # No limpiar el carrito aún, esperar confirmación del pago
            return render(request, self.template_name, {
                'cart': cart, 
                'form': form,
                'order': order,
                'wompi_data': wompi_data,
                'show_wompi_widget': True
            })
        
        return render(request, self.template_name, {'cart': cart, 'form': form})

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart

    def _get_or_create_guest_user(self, form_data):
        email = (form_data.get('email') or '').strip().lower()
        first_name = (form_data.get('first_name') or '').strip()
        last_name = (form_data.get('last_name') or '').strip()

        user = User.objects.filter(email__iexact=email).first()
        if user:
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            if email and user.email != email:
                user.email = email
            user.save()
            return user

        base_username = (email.split('@', 1)[0] if email else 'guest').strip() or 'guest'
        candidate = base_username
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base_username}{suffix}"

        user = User.objects.create_user(
            username=candidate,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()
        return user

    def _get_or_create_customer(self, user, form_data):
        import uuid

        phone = (form_data.get('phone') or '').strip()
        address = (form_data.get('address') or '').strip()
        city_obj = form_data.get('city')
        city = (getattr(city_obj, 'name', None) or '').strip()

        customer = Customer.objects.filter(user=user).first()
        if customer:
            if phone:
                customer.phone = phone
            if address:
                customer.address = address
            if city:
                customer.city = city
            customer.save()
            return customer

        document_number = f"GUEST-{uuid.uuid4().hex[:12].upper()}"
        customer = Customer.objects.create(
            user=user,
            customer_type='normal',
            document_type='CC',
            document_number=document_number,
            phone=phone or '+573001234567',
            address=address or 'N/A',
            city=city or 'N/A',
            channel='website',
        )
        return customer

    def create_order(self, cart, form_data):
        # Obtener o crear cliente
        if cart.user:
            user = cart.user
        else:
            user = self._get_or_create_guest_user(form_data)
            cart.user = user
            cart.save()

        customer = self._get_or_create_customer(user, form_data)
        
        city_obj = form_data.get('city')
        department_obj = form_data.get('department')
        country_obj = form_data.get('country')

        shipping_city = (getattr(city_obj, 'name', None) or '').strip() or 'N/A'
        shipping_notes = ''
        if department_obj and country_obj:
            shipping_notes = f"{department_obj.name} - {country_obj.name}"
        elif country_obj:
            shipping_notes = country_obj.name

        # Crear orden
        order = Order.objects.create(
            customer=customer,
            status='pending',
            payment_method=form_data['payment_method'],
            subtotal=cart.total_amount,
            iva_amount=0,
            shipping_cost=FIXED_SHIPPING_COST,
            total=cart.total_amount + FIXED_SHIPPING_COST,
            shipping_address=form_data['address'],
            shipping_city=shipping_city,
            shipping_phone=form_data['phone'],
            shipping_notes=shipping_notes,
            notes=form_data.get('notes', '')
        )
        
        # Crear items de la orden
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                iva_percentage=Decimal('0.00')
            )
        
        return order


class CheckoutLoginView(View):
    def post(self, request):
        username_or_email = (request.POST.get('username') or request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''

        if not username_or_email or not password:
            messages.error(request, 'Debes ingresar email/usuario y contraseña.')
            return redirect('catalog:checkout')

        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            by_email = User.objects.filter(email__iexact=username_or_email).first()
            if by_email:
                user = authenticate(request, username=by_email.username, password=password)

        if user is None:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return redirect('catalog:checkout')

        merge_session_cart_into_user_cart(request, user)
        login(request, user)
        messages.success(request, 'Sesión iniciada. Tu carrito se mantuvo.')
        return redirect('catalog:checkout')


class CheckoutRegisterView(View):
    def post(self, request):
        email = (request.POST.get('email') or '').strip().lower()
        password1 = request.POST.get('password1') or ''
        password2 = request.POST.get('password2') or ''
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()

        if not email or not password1:
            messages.error(request, 'Email y contraseña son obligatorios.')
            return redirect('catalog:checkout')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('catalog:checkout')

        if User.objects.filter(username=email).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese email. Inicia sesión.')
            return redirect('catalog:checkout')

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password1,
        )

        phone = (request.POST.get('phone') or '').strip()
        address = (request.POST.get('address') or '').strip()
        city_id = request.POST.get('city')
        city_name = ''
        if city_id:
            city_obj = City.objects.filter(id=city_id).first()
            city_name = (getattr(city_obj, 'name', None) or '').strip()

        import uuid
        Customer.objects.get_or_create(
            user=user,
            defaults={
                'customer_type': 'normal',
                'document_type': 'CC',
                'document_number': f"GUEST-{uuid.uuid4().hex[:12].upper()}",
                'phone': phone or '+573001234567',
                'address': address or 'N/A',
                'city': city_name or 'N/A',
                'channel': 'website',
            },
        )

        merge_session_cart_into_user_cart(request, user)
        login(request, user)
        messages.success(request, 'Cuenta creada e iniciada. Tu carrito se mantuvo.')
        return redirect('catalog:checkout')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'Sesión cerrada.')
        return redirect('catalog:home')


class WompiCreateTransactionView(View):
    """Vista para crear una transacción de Wompi para una orden existente"""
    
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        transaction_data, error = create_wompi_transaction(order)
        if error:
            return JsonResponse({'success': False, 'error': error}, status=400)
        
        checkout_url = transaction_data.get('checkout_url')
        if checkout_url:
            return JsonResponse({'success': True, 'checkout_url': checkout_url})
        else:
            return JsonResponse({'success': False, 'error': 'No se pudo obtener la URL de pago'}, status=400)


class CheckoutSuccessView(DetailView):
    model = Order
    template_name = 'catalog/checkout_success.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = context.get('order')
        context['is_paid'] = bool(order and order.status == 'paid')
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        try:
            order = getattr(self, 'object', None)
            if order and order.status == 'paid':
                user = getattr(order.customer, 'user', None)
                if user:
                    cart = Cart.objects.filter(user=user).first()
                    if cart:
                        cart.items.all().delete()
        except Exception:
            pass

        return response


