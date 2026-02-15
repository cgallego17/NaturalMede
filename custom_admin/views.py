from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from catalog.models import Product, Category, Brand, Cart
from catalog.models import CartItem
from inventory.models import Stock, Warehouse, StockMovement, StockTransfer, StockTransferItem
from customers.models import Customer
from orders.models import Order, OrderItem, WompiConfig
from pos.models import POSSale, POSSaleItem, POSSession
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .forms import HomeBannerConfigForm
from .models import HomeBannerConfig


def admin_login(request):
    """Vista de login personalizada para el admin"""
    if request.user.is_authenticated:
        return redirect('custom_admin:admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            return redirect('custom_admin:admin_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'custom_admin/login.html')


def home_login(request):
    """Vista de login desde el home que redirige según el tipo de usuario"""
    if request.user.is_authenticated:
        # Si el usuario es staff (admin), redirigir al admin personalizado
        if request.user.is_staff:
            return redirect('custom_admin:admin_dashboard')
        else:
            # Si es usuario normal, redirigir al home
            return redirect('/')

    next_url = request.GET.get('next') or request.POST.get('next') or '/'
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not request.session.session_key:
                request.session.create()

            session_cart = Cart.objects.filter(session_key=request.session.session_key).first()
            user_cart, _ = Cart.objects.get_or_create(user=user)
            if session_cart and session_cart.items.exists():
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

            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            
            # Redirigir según el tipo de usuario
            if user.is_staff:
                return redirect('custom_admin:admin_dashboard')
            else:
                return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'custom_admin/home_login.html')


@login_required
def admin_dashboard(request):
    """Dashboard principal del admin personalizado"""
    
    # Fecha de hoy
    today = timezone.now().date()
    
    # Estadísticas del día
    today_web_orders = Order.objects.filter(created_at__date=today).count()
    today_pos_sales = POSSale.objects.filter(created_at__date=today).count()
    today_orders = today_web_orders + today_pos_sales
    
    today_web_sales = Order.objects.filter(
        created_at__date=today,
        status__in=['paid', 'shipped', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    today_pos_sales_amount = POSSale.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    today_sales = today_web_sales + today_pos_sales_amount
    
    # Estadísticas de la semana
    week_ago = today - timedelta(days=7)
    week_web_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
    week_pos_sales = POSSale.objects.filter(created_at__date__gte=week_ago).count()
    week_orders = week_web_orders + week_pos_sales
    
    week_web_sales = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=['paid', 'shipped', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    week_pos_sales_amount = POSSale.objects.filter(
        created_at__date__gte=week_ago
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    week_sales = week_web_sales + week_pos_sales_amount
    
    # Estadísticas del mes
    month_ago = today - timedelta(days=30)
    month_web_orders = Order.objects.filter(created_at__date__gte=month_ago).count()
    month_pos_sales = POSSale.objects.filter(created_at__date__gte=month_ago).count()
    month_orders = month_web_orders + month_pos_sales
    
    month_web_sales = Order.objects.filter(
        created_at__date__gte=month_ago,
        status__in=['paid', 'shipped', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    month_pos_sales_amount = POSSale.objects.filter(
        created_at__date__gte=month_ago
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    month_sales = month_web_sales + month_pos_sales_amount
    
    # Estadísticas generales
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = Customer.objects.count()
    total_web_orders = Order.objects.count()
    total_pos_sales = POSSale.objects.count()
    total_orders = total_web_orders + total_pos_sales
    total_categories = Category.objects.filter(is_active=True).count()
    total_brands = Brand.objects.filter(is_active=True).count()
    low_stock_count = Stock.objects.filter(
        quantity__lte=F('min_stock')
    ).count()
    
    # Órdenes recientes (web + POS)
    recent_web_orders = Order.objects.select_related('customer__user').order_by('-created_at')[:5]
    recent_pos_sales = POSSale.objects.select_related('customer__user').order_by('-created_at')[:5]
    
    # Crear lista unificada de órdenes recientes
    recent_orders = []
    
    # Agregar órdenes web
    for order in recent_web_orders:
        # Manejar casos donde no hay cliente
        customer_name = "Cliente General"
        if order.customer and order.customer.user:
            customer_name = order.customer.user.get_full_name() or order.customer.user.username
        elif order.customer:
            customer_name = order.customer.full_name
        
        recent_orders.append({
            'id': order.id,
            'number': order.order_number,
            'customer_name': customer_name,
            'customer': order.customer,  # Mantener para compatibilidad
            'created_at': order.created_at,
            'total': order.total,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.status_color,
            'type': 'web',
            'type_display': 'Web'
        })
    
    # Agregar ventas POS
    for sale in recent_pos_sales:
        # Manejar casos donde no hay cliente
        customer_name = "Cliente General"
        if sale.customer and sale.customer.user:
            customer_name = sale.customer.user.get_full_name() or sale.customer.user.username
        elif sale.customer:
            customer_name = sale.customer.full_name
        
        recent_orders.append({
            'id': sale.id,
            'number': sale.sale_number,
            'customer_name': customer_name,
            'customer': sale.customer,  # Mantener para compatibilidad
            'created_at': sale.created_at,
            'total': sale.total,
            'status': 'paid',  # Las ventas POS siempre están pagadas
            'status_display': 'Pagado',
            'status_color': 'success',
            'type': 'pos',
            'type_display': 'POS'
        })
    
    # Ordenar por fecha de creación (más recientes primero)
    recent_orders.sort(key=lambda x: x['created_at'], reverse=True)
    recent_orders = recent_orders[:10]
    
    # Productos más vendidos (últimos 30 días) - Web + POS
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Productos vendidos en web
    web_top_products = Product.objects.filter(
        orderitem__order__created_at__gte=thirty_days_ago,
        orderitem__order__status__in=['paid', 'shipped', 'delivered']
    ).annotate(
        web_sold=Sum('orderitem__quantity'),
        web_revenue=Sum('orderitem__total')
    )
    
    # Productos vendidos en POS
    pos_top_products = Product.objects.filter(
        possaleitem__sale__created_at__gte=thirty_days_ago
    ).annotate(
        pos_sold=Sum('possaleitem__quantity'),
        pos_revenue=Sum('possaleitem__total')
    )
    
    # Combinar datos de web y POS
    all_products = Product.objects.all()
    top_products = []
    
    for product in all_products:
        web_data = next((p for p in web_top_products if p.id == product.id), None)
        pos_data = next((p for p in pos_top_products if p.id == product.id), None)
        
        web_sold = web_data.web_sold if web_data and web_data.web_sold else 0
        web_revenue = web_data.web_revenue if web_data and web_data.web_revenue else Decimal('0')
        pos_sold = pos_data.pos_sold if pos_data and pos_data.pos_sold else 0
        pos_revenue = pos_data.pos_revenue if pos_data and pos_data.pos_revenue else Decimal('0')
        
        total_sold = web_sold + pos_sold
        total_revenue = web_revenue + pos_revenue
        
        if total_sold > 0:  # Solo incluir productos que se han vendido
            top_products.append({
                'product': product,
                'total_sold': total_sold,
                'total_revenue': total_revenue
            })
    
    # Ordenar por cantidad vendida
    top_products.sort(key=lambda x: x['total_sold'], reverse=True)
    top_products = top_products[:10]
    
    # Productos con stock bajo
    low_stock_products = Stock.objects.select_related('product', 'warehouse').filter(
        quantity__lte=F('min_stock')
    ).order_by('quantity')[:10]
    
    # Órdenes por estado (Web + POS)
    web_orders_by_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Agregar ventas POS como "paid" (pagadas)
    pos_sales_count = POSSale.objects.count()
    
    orders_by_status = list(web_orders_by_status)
    
    # Si hay ventas POS, agregar o actualizar el estado "paid"
    if pos_sales_count > 0:
        paid_status_exists = False
        for status_data in orders_by_status:
            if status_data['status'] == 'paid':
                status_data['count'] += pos_sales_count
                paid_status_exists = True
                break
        
        if not paid_status_exists:
            orders_by_status.append({'status': 'paid', 'count': pos_sales_count})
    
    # Categorías más populares
    popular_categories = Product.objects.values(
        'category__name'
    ).annotate(
        product_count=Count('id')
    ).order_by('-product_count')[:5]
    
    # Distribución de ventas por categoría (Web + POS)
    web_category_sales = Category.objects.filter(
        product__orderitem__order__created_at__gte=thirty_days_ago,
        product__orderitem__order__status__in=['paid', 'shipped', 'delivered']
    ).annotate(
        web_sales=Sum('product__orderitem__total')
    )
    
    pos_category_sales = Category.objects.filter(
        product__possaleitem__sale__created_at__gte=thirty_days_ago
    ).annotate(
        pos_sales=Sum('product__possaleitem__total')
    )
    
    # Combinar datos de categorías
    all_categories = Category.objects.all()
    category_distribution = []
    
    for category in all_categories:
        web_data = next((c for c in web_category_sales if c.id == category.id), None)
        pos_data = next((c for c in pos_category_sales if c.id == category.id), None)
        
        web_sales = web_data.web_sales if web_data and web_data.web_sales else Decimal('0')
        pos_sales = pos_data.pos_sales if pos_data and pos_data.pos_sales else Decimal('0')
        
        total_sales = web_sales + pos_sales
        
        if total_sales > 0:  # Solo incluir categorías con ventas
            category_distribution.append({
                'category': category,
                'total_sales': total_sales,
                'web_sales': web_sales,
                'pos_sales': pos_sales
            })
    
    # Ordenar por ventas totales
    category_distribution.sort(key=lambda x: x['total_sales'], reverse=True)
    category_distribution = category_distribution[:5]  # Top 5 categorías
    
    # Clientes VIP
    vip_customers = Customer.objects.filter(
        customer_type='vip'
    ).select_related('user')[:5]
    
    # Datos para el gráfico de ventas (últimos 7 días) - Web + POS
    sales_data = []
    sales_labels = []
    
    for i in range(7):
        date = today - timedelta(days=i)
        
        # Ventas web del día
        daily_web_sales = Order.objects.filter(
            created_at__date=date,
            status__in=['paid', 'shipped', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Ventas POS del día
        daily_pos_sales = POSSale.objects.filter(
            created_at__date=date
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Total del día
        daily_total = daily_web_sales + daily_pos_sales
        
        sales_data.append(float(daily_total))
        sales_labels.append(date.strftime('%d/%m'))
    
    sales_data.reverse()
    sales_labels.reverse()
    
    # Si no hay datos, crear datos demo para mostrar el gráfico
    if all(val == 0 for val in sales_data):
        sales_data = [0, 0, 0, 0, 0, 0, 0]
        sales_labels = [(today - timedelta(days=6-i)).strftime('%d/%m') for i in range(7)]
    
    # Debug: Imprimir datos de ventas diarias
    print("=== DEBUG VENTAS DIARIAS ===")
    print("Sales Labels:", sales_labels)
    print("Sales Data:", sales_data)
    print("===========================")
    
    # Datos para el gráfico de órdenes por estado
    status_data = []
    status_labels = []
    status_colors = {
        'new': '#007bff',
        'pending': '#ffc107',
        'paid': '#28a745',
        'shipped': '#17a2b8',
        'delivered': '#6f42c1',
        'cancelled': '#dc3545'
    }
    
    for order_status in orders_by_status:
        status_data.append(order_status['count'])
        status_labels.append(order_status['status'].title())
    
    context = {
        'today_sales': today_sales,
        'today_orders': today_orders,
        'week_sales': week_sales,
        'week_orders': week_orders,
        'month_sales': month_sales,
        'month_orders': month_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_categories': total_categories,
        'total_brands': total_brands,
        'low_stock_count': low_stock_count,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'orders_by_status': orders_by_status,
        'popular_categories': popular_categories,
        'vip_customers': vip_customers,
        'category_distribution': category_distribution,
        'sales_data': json.dumps(sales_data),
        'sales_labels': json.dumps(sales_labels),
        'status_data': json.dumps(status_data),
        'status_labels': json.dumps(status_labels),
        'status_colors': status_colors,
        'now': timezone.now(),
    }
    
    return render(request, 'custom_admin/dashboard.html', context)




@login_required
def admin_product_create(request):
    """Crear nuevo producto"""
    from catalog.forms import ProductForm
    from catalog.models import ProductImage
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Manejar imagen principal
            main_image = form.cleaned_data.get('main_image')
            if main_image:
                # Crear imagen principal
                ProductImage.objects.create(
                    product=product,
                    image=main_image,
                    is_primary=True,
                    alt_text=product.name
                )
            
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('custom_admin:admin_products')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Crear Producto',
        'action': 'create'
    }
    
    return render(request, 'custom_admin/product_form.html', context)


@login_required
def admin_product_detail(request, pk):
    """Ver detalles de un producto"""
    try:
        product = Product.objects.select_related('category', 'brand').prefetch_related('images').get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('custom_admin:admin_products')
    
    # Obtener stock del producto
    try:
        stock = product.stock
    except:
        stock = None
    
    context = {
        'product': product,
        'stock': stock,
    }
    
    return render(request, 'custom_admin/product_detail.html', context)


@login_required
def admin_product_edit(request, pk):
    """Editar producto existente"""
    from catalog.forms import ProductForm
    from catalog.models import ProductImage
    
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('custom_admin:admin_products')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            # Manejar imagen principal
            main_image = form.cleaned_data.get('main_image')
            if main_image:
                # Eliminar imagen principal anterior si existe
                ProductImage.objects.filter(product=product, is_primary=True).delete()
                
                # Crear nueva imagen principal
                ProductImage.objects.create(
                    product=product,
                    image=main_image,
                    is_primary=True,
                    alt_text=product.name
                )
            
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('custom_admin:admin_products')
    else:
        form = ProductForm(instance=product)
        # Cargar imagen principal existente si existe
        main_image = product.images.filter(is_primary=True).first()
        if main_image:
            form.fields['main_image'].initial = main_image.image
    
    context = {
        'form': form,
        'product': product,
        'title': 'Editar Producto',
        'action': 'edit'
    }
    
    return render(request, 'custom_admin/product_form.html', context)


@login_required
def admin_product_delete(request, pk):
    """Eliminar producto"""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('custom_admin:admin_products')
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        return redirect('custom_admin:admin_products')
    
    context = {
        'product': product,
    }
    
    return render(request, 'custom_admin/product_confirm_delete.html', context)


@login_required
def admin_categories(request):
    """Lista de categorías con filtros y paginación"""
    from catalog.models import Category
    
    categories = Category.objects.all()
    
    # Filtros
    search = request.GET.get('search')
    is_active = request.GET.get('is_active')
    
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if is_active is not None and is_active != '':
        categories = categories.filter(is_active=is_active == 'true')
    
    # Ordenamiento
    categories = categories.order_by('name')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'current_search': search,
        'current_is_active': is_active,
    }
    
    return render(request, 'custom_admin/categories.html', context)


@login_required
def admin_category_create(request):
    """Crear nueva categoría"""
    from catalog.models import Category
    from catalog.forms import CategoryForm
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
            return redirect('custom_admin:admin_categories')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Crear Categoría',
        'action': 'create'
    }
    
    return render(request, 'custom_admin/category_form.html', context)


@login_required
def admin_category_detail(request, pk):
    """Ver detalles de una categoría"""
    from catalog.models import Category
    
    try:
        category = Category.objects.prefetch_related('product_set').get(pk=pk)
    except Category.DoesNotExist:
        messages.error(request, 'Categoría no encontrada.')
        return redirect('custom_admin:admin_categories')
    
    # Productos de esta categoría
    products = category.product_set.all()[:10]  # Solo los primeros 10
    
    context = {
        'category': category,
        'products': products,
    }
    
    return render(request, 'custom_admin/category_detail.html', context)


@login_required
def admin_category_edit(request, pk):
    """Editar categoría existente"""
    from catalog.models import Category
    from catalog.forms import CategoryForm
    
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        messages.error(request, 'Categoría no encontrada.')
        return redirect('custom_admin:admin_categories')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada exitosamente.')
            return redirect('custom_admin:admin_categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Editar Categoría',
        'action': 'edit'
    }
    
    return render(request, 'custom_admin/category_form.html', context)


@login_required
def admin_category_delete(request, pk):
    """Eliminar categoría"""
    from catalog.models import Category
    
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        messages.error(request, 'Categoría no encontrada.')
        return redirect('custom_admin:admin_categories')
    
    product_count = category.product_set.count()
    products = category.product_set.select_related('category', 'brand').prefetch_related('stock_set__warehouse')[:10] if product_count > 0 else []
    
    # Verificar si hay productos con compras asociadas
    from purchases.models import PurchaseItem
    products_with_purchases = PurchaseItem.objects.filter(product__category=category).values_list('product_id', flat=True).distinct()
    has_purchase_items = products_with_purchases.exists()
    
    if request.method == 'POST':
        if has_purchase_items:
            messages.error(request, f'No se puede eliminar la categoría "{category.name}" porque tiene productos con compras registradas. Esto afectaría el historial de compras.')
            return redirect('custom_admin:admin_category_detail', pk=pk)
        
        if product_count > 0:
            confirm_cascade = request.POST.get('confirm_cascade')
            if not confirm_cascade:
                messages.error(request, f'Debes confirmar que deseas eliminar la categoría "{category.name}" y sus {product_count} producto(s) asociado(s).')
                return redirect('custom_admin:admin_category_delete', pk=pk)
        
        category_name = category.name
        category.delete()
        if product_count > 0:
            messages.success(request, f'Categoría "{category_name}" y {product_count} producto(s) eliminados exitosamente.')
        else:
            messages.success(request, f'Categoría "{category_name}" eliminada exitosamente.')
        return redirect('custom_admin:admin_categories')
    
    context = {
        'category': category,
        'product_count': product_count,
        'products': products,
        'has_purchase_items': has_purchase_items,
    }
    
    return render(request, 'custom_admin/category_confirm_delete.html', context)


@login_required
def admin_brands(request):
    """Lista de marcas con filtros y paginación"""
    from catalog.models import Brand
    
    brands = Brand.objects.all()
    
    # Filtros
    search = request.GET.get('search')
    is_active = request.GET.get('is_active')
    
    if search:
        brands = brands.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(website__icontains=search)
        )
    
    if is_active is not None and is_active != '':
        brands = brands.filter(is_active=is_active == 'true')
    
    # Ordenamiento
    brands = brands.order_by('name')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(brands, 20)
    page_number = request.GET.get('page')
    brands = paginator.get_page(page_number)
    
    context = {
        'brands': brands,
        'current_search': search,
        'current_is_active': is_active,
    }
    
    return render(request, 'custom_admin/brands.html', context)


@login_required
def admin_brand_create(request):
    """Crear nueva marca"""
    from catalog.models import Brand
    from catalog.forms import BrandForm
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Marca "{brand.name}" creada exitosamente.')
            return redirect('custom_admin:admin_brands')
    else:
        form = BrandForm()
    
    context = {
        'form': form,
        'title': 'Crear Marca',
        'action': 'create'
    }
    
    return render(request, 'custom_admin/brand_form.html', context)


@login_required
def admin_brand_detail(request, pk):
    """Ver detalles de una marca"""
    from catalog.models import Brand
    
    try:
        brand = Brand.objects.prefetch_related('product_set').get(pk=pk)
    except Brand.DoesNotExist:
        messages.error(request, 'Marca no encontrada.')
        return redirect('custom_admin:admin_brands')
    
    # Productos de esta marca
    products = brand.product_set.all()[:10]  # Solo los primeros 10
    
    context = {
        'brand': brand,
        'products': products,
    }
    
    return render(request, 'custom_admin/brand_detail.html', context)


@login_required
def admin_brand_edit(request, pk):
    """Editar marca existente"""
    from catalog.models import Brand
    from catalog.forms import BrandForm
    
    try:
        brand = Brand.objects.get(pk=pk)
    except Brand.DoesNotExist:
        messages.error(request, 'Marca no encontrada.')
        return redirect('custom_admin:admin_brands')
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Marca "{brand.name}" actualizada exitosamente.')
            return redirect('custom_admin:admin_brands')
    else:
        form = BrandForm(instance=brand)
    
    context = {
        'form': form,
        'brand': brand,
        'title': 'Editar Marca',
        'action': 'edit'
    }
    
    return render(request, 'custom_admin/brand_form.html', context)


@login_required
def admin_brand_delete(request, pk):
    """Eliminar marca"""
    from catalog.models import Brand
    
    try:
        brand = Brand.objects.get(pk=pk)
    except Brand.DoesNotExist:
        messages.error(request, 'Marca no encontrada.')
        return redirect('custom_admin:admin_brands')
    
    product_count = brand.product_set.count()
    products = brand.product_set.select_related('category', 'brand').prefetch_related('stock_set__warehouse')[:10] if product_count > 0 else []
    
    # Verificar si hay productos con compras asociadas
    from purchases.models import PurchaseItem
    products_with_purchases = PurchaseItem.objects.filter(product__brand=brand).values_list('product_id', flat=True).distinct()
    has_purchase_items = products_with_purchases.exists()
    
    if request.method == 'POST':
        if has_purchase_items:
            messages.error(request, f'No se puede eliminar la marca "{brand.name}" porque tiene productos con compras registradas. Esto afectaría el historial de compras.')
            return redirect('custom_admin:admin_brand_detail', pk=pk)
        
        if product_count > 0:
            confirm_cascade = request.POST.get('confirm_cascade')
            if not confirm_cascade:
                messages.error(request, f'Debes confirmar que deseas eliminar la marca "{brand.name}" y sus {product_count} producto(s) asociado(s).')
                return redirect('custom_admin:admin_brand_delete', pk=pk)
        
        brand_name = brand.name
        brand.delete()
        if product_count > 0:
            messages.success(request, f'Marca "{brand_name}" y {product_count} producto(s) eliminados exitosamente.')
        else:
            messages.success(request, f'Marca "{brand_name}" eliminada exitosamente.')
        return redirect('custom_admin:admin_brands')
    
    context = {
        'brand': brand,
        'product_count': product_count,
        'products': products,
        'has_purchase_items': has_purchase_items,
    }
    
    return render(request, 'custom_admin/brand_confirm_delete.html', context)




@login_required
def admin_orders(request):
    """Gestión de órdenes"""
    
    orders = Order.objects.select_related('customer__user').all()
    
    # Filtros
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(customer__user__first_name__icontains=search) |
            Q(customer__user__last_name__icontains=search) |
            Q(customer__user__username__icontains=search)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    orders = orders.order_by('-created_at')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Opciones de estado
    status_choices = Order.STATUS_CHOICES
    
    context = {
        'orders': orders,
        'status_choices': status_choices,
        'current_status': status,
        'current_search': search,
    }
    
    return render(request, 'custom_admin/orders.html', context)




@login_required
def admin_pos(request):
    """Punto de venta"""
    
    # Obtener sesión activa o crear una nueva
    active_session = POSSession.objects.filter(
        user=request.user,
        status='open'
    ).first()
    
    if not active_session:
        # Necesitamos una bodega por defecto
        default_warehouse = Warehouse.objects.first()
        if not default_warehouse:
            # Crear una bodega por defecto si no existe
            default_warehouse = Warehouse.objects.create(
                name='Bodega Principal',
                address='Dirección principal',
                phone='+573001234567',
                is_active=True
            )
        
        active_session = POSSession.objects.create(
            user=request.user,
            warehouse=default_warehouse,
            status='open'
        )
    
    # Obtener ventas de la sesión
    sales = POSSale.objects.filter(session=active_session).order_by('-created_at')
    
    # Estadísticas de la sesión
    session_stats = {
        'total_sales': sales.count(),
        'total_amount': sales.aggregate(total=Sum('total'))['total'] or Decimal('0'),
        'total_items': POSSaleItem.objects.filter(sale__session=active_session).aggregate(
            total=Sum('quantity')
        )['total'] or 0,
    }
    
    context = {
        'active_session': active_session,
        'sales': sales,
        'session_stats': session_stats,
    }
    
    return render(request, 'custom_admin/pos.html', context)


@login_required
def admin_products(request):
    """Gestión de productos"""
    products = Product.objects.select_related('category', 'brand').all()
    
    # Filtros
    search = request.GET.get('search')
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    is_active = request.GET.get('is_active')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(sku__icontains=search) |
            Q(short_description__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    if is_active is not None and is_active != '':
        products = products.filter(is_active=is_active == 'true')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Datos para filtros
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'current_search': search,
        'current_category': category_id,
        'current_brand': brand_id,
        'current_is_active': is_active,
    }
    
    return render(request, 'custom_admin/products.html', context)


@login_required
def admin_inventory(request):
    """Gestión de inventario"""
    # Obtener todos los stocks inicialmente
    stocks = Stock.objects.select_related('product', 'warehouse').all()
    
    # Filtros
    search = request.GET.get('search') or None
    warehouse_id = request.GET.get('warehouse') or None
    low_stock = request.GET.get('low_stock') or None
    
    # Aplicar filtro de búsqueda
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) | 
            Q(product__sku__icontains=search) |
            Q(product__category__name__icontains=search) |
            Q(product__brand__name__icontains=search)
        )
    
    # Aplicar filtro de bodega
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)
    
    # Aplicar filtro de stock bajo
    if low_stock == 'true':
        stocks = stocks.filter(quantity__lte=F('min_stock'))
    
    # Ordenamiento
    stocks = stocks.order_by('warehouse__name', 'product__name')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(stocks, 50)
    page_number = request.GET.get('page')
    stocks = paginator.get_page(page_number)
    
    # Datos para filtros
    warehouses = Warehouse.objects.all().order_by('name')
    
    context = {
        'stocks': stocks,
        'warehouses': warehouses,
        'current_search': search if search else '',
        'current_warehouse': warehouse_id if warehouse_id else '',
        'low_stock_filter': low_stock if low_stock else '',
    }
    
    return render(request, 'custom_admin/inventory.html', context)


@login_required
def admin_orders(request):
    """Gestión de órdenes - incluye órdenes web y ventas POS"""
    
    # Obtener órdenes web
    web_orders = Order.objects.select_related('customer__user').all()
    
    # Obtener ventas POS
    pos_sales = POSSale.objects.select_related('session', 'customer__user').all()
    
    # Filtros
    search = request.GET.get('search')
    status = request.GET.get('status')
    order_type = request.GET.get('order_type')  # Nuevo filtro para tipo de orden
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Aplicar filtros a órdenes web
    if search:
        web_orders = web_orders.filter(
            Q(id__icontains=search) |
            Q(customer__user__first_name__icontains=search) |
            Q(customer__user__last_name__icontains=search) |
            Q(customer__user__email__icontains=search) |
            Q(customer__user__username__icontains=search)
        )
    
    if status:
        web_orders = web_orders.filter(status=status)
    
    if start_date:
        web_orders = web_orders.filter(created_at__date__gte=start_date)
    
    if end_date:
        web_orders = web_orders.filter(created_at__date__lte=end_date)
    
    # Aplicar filtros a ventas POS
    if search:
        pos_sales = pos_sales.filter(
            Q(sale_number__icontains=search) |
            Q(customer__user__first_name__icontains=search) |
            Q(customer__user__last_name__icontains=search) |
            Q(customer__user__email__icontains=search) |
            Q(customer__user__username__icontains=search)
        )
    
    if start_date:
        pos_sales = pos_sales.filter(created_at__date__gte=start_date)
    
    if end_date:
        pos_sales = pos_sales.filter(created_at__date__lte=end_date)
    
    # Crear lista unificada con información del tipo
    all_orders = []
    
    # Agregar órdenes web
    for order in web_orders:
        all_orders.append({
            'id': order.id,
            'number': order.order_number,
            'customer': order.customer,
            'created_at': order.created_at,
            'total': order.total,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.status_color,
            'payment_method': order.get_payment_method_display(),
            'order_type': 'web',
            'order_type_display': 'Web',
            'order_type_color': 'info',
            'original_object': order,
        })
    
    # Agregar ventas POS
    for sale in pos_sales:
        all_orders.append({
            'id': sale.id,
            'number': sale.sale_number,
            'customer': sale.customer,
            'created_at': sale.created_at,
            'total': sale.total,
            'status': 'completed',  # Las ventas POS siempre están completadas
            'status_display': 'Completada',
            'status_color': 'success',
            'payment_method': sale.get_payment_method_display(),
            'order_type': 'pos',
            'order_type_display': 'POS',
            'order_type_color': 'primary',
            'original_object': sale,
        })
    
    # Filtrar por tipo de orden si se especifica
    if order_type:
        all_orders = [order for order in all_orders if order['order_type'] == order_type]
    
    # Ordenar por fecha de creación (más recientes primero)
    all_orders.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(all_orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Opciones de estado para el filtro
    status_choices = [
        ('', 'Todos los estados'),
        ('new', 'Nuevo'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Completada'),
    ]
    
    # Opciones de tipo de orden
    order_type_choices = [
        ('', 'Todos los tipos'),
        ('web', 'Web'),
        ('pos', 'POS'),
    ]
    
    context = {
        'orders': orders_page,
        'current_search': search,
        'current_status': status,
        'current_order_type': order_type,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': status_choices,
        'order_type_choices': order_type_choices,
    }
    
    return render(request, 'custom_admin/orders.html', context)


@login_required
def admin_customers(request):
    """Gestión de clientes"""
    customers = Customer.objects.select_related('user').all()
    
    # Filtros
    search = request.GET.get('search')
    customer_type = request.GET.get('customer_type')
    is_active = request.GET.get('is_active')
    
    if search:
        customers = customers.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search) |
            Q(document_number__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if customer_type:
        customers = customers.filter(customer_type=customer_type)
    
    if is_active is not None and is_active != '':
        customers = customers.filter(is_active=is_active == 'true')
    
    # Ordenar por nombre
    customers = customers.order_by('user__first_name', 'user__last_name')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)
    
    # Opciones de tipo de cliente para el filtro
    customer_type_choices = [
        ('', 'Todos los tipos'),
        ('normal', 'Normal'),
        ('vip', 'VIP'),
    ]
    
    context = {
        'customers': customers,
        'current_search': search,
        'current_customer_type': customer_type,
        'current_is_active': is_active,
        'customer_type_choices': customer_type_choices,
    }
    
    return render(request, 'custom_admin/customers.html', context)


@login_required
def admin_customer_detail(request, pk):
    """Detalle de cliente"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Obtener órdenes del cliente (para estadísticas)
    all_orders = Order.objects.filter(customer=customer)
    orders = all_orders.order_by('-created_at')[:10]
    
    # Obtener ventas POS del cliente (para estadísticas)
    all_pos_sales = POSSale.objects.filter(customer=customer)
    pos_sales = all_pos_sales.order_by('-created_at')[:10]
    
    # Estadísticas
    total_orders = all_orders.count()
    total_pos_sales = all_pos_sales.count()
    total_spent = sum(order.total for order in all_orders.filter(status='delivered'))
    total_pos_spent = sum(sale.total for sale in all_pos_sales)
    
    context = {
        'customer': customer,
        'orders': orders,
        'pos_sales': pos_sales,
        'total_orders': total_orders,
        'total_pos_sales': total_pos_sales,
        'total_spent': total_spent,
        'total_pos_spent': total_pos_spent,
    }
    
    return render(request, 'custom_admin/customer_detail.html', context)


@login_required
def admin_customer_edit(request, pk):
    """Editar cliente"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        # Actualizar datos del usuario
        user = customer.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Actualizar datos del cliente
        customer.customer_type = request.POST.get('customer_type')
        customer.document_type = request.POST.get('document_type')
        customer.document_number = request.POST.get('document_number')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')
        customer.city = request.POST.get('city')
        customer.birth_date = request.POST.get('birth_date') or None
        customer.channel = request.POST.get('channel')
        customer.notes = request.POST.get('notes')
        customer.is_active = request.POST.get('is_active') == 'on'
        customer.save()
        
        messages.success(request, 'Cliente actualizado exitosamente.')
        return redirect('custom_admin:admin_customer_detail', pk=customer.pk)
    
    context = {
        'customer': customer,
    }
    
    return render(request, 'custom_admin/customer_edit.html', context)


@login_required
def admin_customer_toggle_vip(request, pk):
    """Cambiar tipo de cliente entre Normal y VIP"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if customer.customer_type == 'normal':
        customer.customer_type = 'vip'
        messages.success(request, f'{customer.full_name} ahora es cliente VIP.')
    else:
        customer.customer_type = 'normal'
        messages.success(request, f'{customer.full_name} ya no es cliente VIP.')
    
    customer.save()
    return redirect('custom_admin:admin_customers')


@login_required
def admin_customer_toggle_status(request, pk):
    """Activar/desactivar cliente"""
    customer = get_object_or_404(Customer, pk=pk)
    
    customer.is_active = not customer.is_active
    customer.save()
    
    status = "activado" if customer.is_active else "desactivado"
    messages.success(request, f'{customer.full_name} ha sido {status}.')
    
    return redirect('custom_admin:admin_customers')


@login_required
def admin_customer_orders(request, pk):
    """Órdenes de un cliente específico"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Obtener órdenes web
    web_orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    # Obtener ventas POS
    pos_sales = POSSale.objects.filter(customer=customer).order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if search:
        web_orders = web_orders.filter(
            Q(id__icontains=search) |
            Q(order_number__icontains=search)
        )
        pos_sales = pos_sales.filter(
            Q(sale_number__icontains=search)
        )
    
    if status:
        web_orders = web_orders.filter(status=status)
    
    if start_date:
        web_orders = web_orders.filter(created_at__date__gte=start_date)
        pos_sales = pos_sales.filter(created_at__date__gte=start_date)
    
    if end_date:
        web_orders = web_orders.filter(created_at__date__lte=end_date)
        pos_sales = pos_sales.filter(created_at__date__lte=end_date)
    
    # Combinar órdenes
    all_orders = []
    
    for order in web_orders:
        all_orders.append({
            'id': order.id,
            'number': order.order_number,
            'date': order.created_at,
            'total': order.total,
            'status': order.status,
            'status_display': order.get_status_display(),
            'type': 'web',
            'type_display': 'Web',
            'order': order,
        })
    
    for sale in pos_sales:
        all_orders.append({
            'id': sale.id,
            'number': sale.sale_number,
            'date': sale.created_at,
            'total': sale.total,
            'status': 'paid',
            'status_display': 'Pagado',
            'type': 'pos',
            'type_display': 'POS',
            'sale': sale,
        })
    
    # Ordenar por fecha
    all_orders.sort(key=lambda x: x['date'], reverse=True)
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(all_orders, 20)
    page_number = request.GET.get('page')
    all_orders = paginator.get_page(page_number)
    
    context = {
        'customer': customer,
        'orders': all_orders,
        'current_search': search,
        'current_status': status,
        'current_start_date': start_date,
        'current_end_date': end_date,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/customer_orders.html', context)


@login_required
def admin_customer_create(request):
    """Crear nuevo cliente"""
    if request.method == 'POST':
        try:
            # Crear usuario básico (sin login)
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            # Generar username único basado en email
            base_username = email.split('@')[0] if email else f"{first_name.lower()}{last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Crear usuario básico
            user = User.objects.create_user(
                username=username,
                email=email,
                password='temp_password_123',  # Contraseña temporal
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Usuario no activo para login
            )
            
            # Crear cliente
            customer = Customer.objects.create(
                user=user,
                customer_type=request.POST.get('customer_type', 'normal'),
                document_type=request.POST.get('document_type'),
                document_number=request.POST.get('document_number'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                birth_date=request.POST.get('birth_date') or None,
                channel=request.POST.get('channel', 'other'),
                notes=request.POST.get('notes'),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            messages.success(request, f'Cliente {customer.full_name} creado exitosamente.')
            return redirect('custom_admin:admin_customer_detail', pk=customer.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear el cliente: {str(e)}')
    
    return render(request, 'custom_admin/customer_create.html')


@login_required
def admin_reports(request):
    """Reportes y estadísticas avanzados"""
    
    # Filtros de fecha
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'sales')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Convertir a datetime
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Filtro base para órdenes web pagadas
    paid_web_orders = Order.objects.filter(
        created_at__date__range=[start_dt, end_dt],
        status__in=['paid', 'shipped', 'delivered']
    )
    
    # Filtro base para ventas POS
    pos_sales = POSSale.objects.filter(
        created_at__date__range=[start_dt, end_dt]
    )
    
    # 1. REPORTES DE VENTAS (Web + POS)
    web_sales_report = paid_web_orders.aggregate(
        total_orders=Count('id'),
        total_sales=Sum('total'),
        avg_order_value=Sum('total') / Count('id')
    )
    
    pos_sales_report = pos_sales.aggregate(
        total_orders=Count('id'),
        total_sales=Sum('total'),
        avg_order_value=Sum('total') / Count('id')
    )
    
    # Combinar reportes
    total_orders = (web_sales_report['total_orders'] or 0) + (pos_sales_report['total_orders'] or 0)
    total_sales = (web_sales_report['total_sales'] or Decimal('0')) + (pos_sales_report['total_sales'] or Decimal('0'))
    avg_order_value = total_sales / total_orders if total_orders > 0 else Decimal('0')
    
    sales_report = {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'avg_order_value': avg_order_value,
        'web_orders': web_sales_report['total_orders'] or 0,
        'pos_orders': pos_sales_report['total_orders'] or 0,
        'web_sales': web_sales_report['total_sales'] or Decimal('0'),
        'pos_sales': pos_sales_report['total_sales'] or Decimal('0')
    }
    
    # Comparación con período anterior (Web + POS)
    prev_start = start_dt - timedelta(days=(end_dt - start_dt).days + 1)
    prev_end = start_dt - timedelta(days=1)
    
    prev_web_sales = Order.objects.filter(
        created_at__date__range=[prev_start, prev_end],
        status__in=['paid', 'shipped', 'delivered']
    ).aggregate(
        total_orders=Count('id'),
        total_sales=Sum('total')
    )
    
    prev_pos_sales = POSSale.objects.filter(
        created_at__date__range=[prev_start, prev_end]
    ).aggregate(
        total_orders=Count('id'),
        total_sales=Sum('total')
    )
    
    prev_total_orders = (prev_web_sales['total_orders'] or 0) + (prev_pos_sales['total_orders'] or 0)
    prev_total_sales = (prev_web_sales['total_sales'] or Decimal('0')) + (prev_pos_sales['total_sales'] or Decimal('0'))
    
    prev_sales = {
        'total_orders': prev_total_orders,
        'total_sales': prev_total_sales
    }
    
    # Calcular crecimiento
    current_total = sales_report['total_sales'] or Decimal('0')
    prev_total = prev_sales['total_sales'] or Decimal('0')
    growth_percentage = 0
    if prev_total > 0:
        growth_percentage = ((current_total - prev_total) / prev_total) * 100
    
    # 2. PRODUCTOS MÁS VENDIDOS (Web + POS)
    web_top_products = Product.objects.filter(
        orderitem__order__created_at__date__range=[start_dt, end_dt],
        orderitem__order__status__in=['paid', 'shipped', 'delivered']
    ).annotate(
        web_sold=Sum('orderitem__quantity'),
        web_revenue=Sum('orderitem__total')
    )
    
    pos_top_products = Product.objects.filter(
        possaleitem__sale__created_at__date__range=[start_dt, end_dt]
    ).annotate(
        pos_sold=Sum('possaleitem__quantity'),
        pos_revenue=Sum('possaleitem__total')
    )
    
    # Combinar datos de web y POS
    all_products = Product.objects.all()
    top_products = []
    
    for product in all_products:
        web_data = next((p for p in web_top_products if p.id == product.id), None)
        pos_data = next((p for p in pos_top_products if p.id == product.id), None)
        
        web_sold = web_data.web_sold if web_data and web_data.web_sold else 0
        web_revenue = web_data.web_revenue if web_data and web_data.web_revenue else Decimal('0')
        pos_sold = pos_data.pos_sold if pos_data and pos_data.pos_sold else 0
        pos_revenue = pos_data.pos_revenue if pos_data and pos_data.pos_revenue else Decimal('0')
        
        total_sold = web_sold + pos_sold
        total_revenue = web_revenue + pos_revenue
        
        if total_sold > 0:  # Solo incluir productos que se han vendido
            top_products.append({
                'product': product,
                'total_sold': total_sold,
                'total_revenue': total_revenue,
                'web_sold': web_sold,
                'pos_sold': pos_sold
            })
    
    # Ordenar por cantidad vendida
    top_products.sort(key=lambda x: x['total_sold'], reverse=True)
    top_products = top_products[:10]
    
    # 3. VENTAS POR DÍA (para gráfico) - Web + POS
    daily_sales = []
    current_date = start_dt
    while current_date <= end_dt:
        # Ventas web del día
        daily_web_total = paid_web_orders.filter(
            created_at__date=current_date
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Ventas POS del día
        daily_pos_total = pos_sales.filter(
            created_at__date=current_date
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Total del día
        daily_total = daily_web_total + daily_pos_total
        
        daily_sales.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'total': float(daily_total),
            'web_total': float(daily_web_total),
            'pos_total': float(daily_pos_total)
        })
        
        current_date += timedelta(days=1)
    
    # 4. VENTAS POR CATEGORÍA (Web + POS)
    web_category_sales = Category.objects.filter(
        product__orderitem__order__created_at__date__range=[start_dt, end_dt],
        product__orderitem__order__status__in=['paid', 'shipped', 'delivered']
    ).annotate(
        web_sales=Sum('product__orderitem__total'),
        web_quantity=Sum('product__orderitem__quantity')
    )
    
    pos_category_sales = Category.objects.filter(
        product__possaleitem__sale__created_at__date__range=[start_dt, end_dt]
    ).annotate(
        pos_sales=Sum('product__possaleitem__total'),
        pos_quantity=Sum('product__possaleitem__quantity')
    )
    
    # Combinar datos de categorías
    all_categories = Category.objects.all()
    category_sales = []
    
    for category in all_categories:
        web_data = next((c for c in web_category_sales if c.id == category.id), None)
        pos_data = next((c for c in pos_category_sales if c.id == category.id), None)
        
        web_sales = web_data.web_sales if web_data and web_data.web_sales else Decimal('0')
        web_quantity = web_data.web_quantity if web_data and web_data.web_quantity else 0
        pos_sales = pos_data.pos_sales if pos_data and pos_data.pos_sales else Decimal('0')
        pos_quantity = pos_data.pos_quantity if pos_data and pos_data.pos_quantity else 0
        
        total_sales = web_sales + pos_sales
        total_quantity = web_quantity + pos_quantity
        
        if total_sales > 0:  # Solo incluir categorías con ventas
            category_sales.append({
                'category': category,
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'web_sales': web_sales,
                'pos_sales': pos_sales
            })
    
    # Ordenar por ventas totales
    category_sales.sort(key=lambda x: x['total_sales'], reverse=True)
    category_sales = category_sales[:5]
    
    # 5. ESTADO DE INVENTARIO
    low_stock_products = Stock.objects.filter(
        quantity__lte=F('min_stock'),
        quantity__gt=0
    ).select_related('product', 'product__category', 'product__brand')[:10]
    
    out_of_stock_products = Stock.objects.filter(
        quantity=0
    ).select_related('product', 'product__category', 'product__brand')[:10]
    
    # 6. CLIENTES TOP (Web + POS)
    web_top_customers = Customer.objects.filter(
        orders__created_at__date__range=[start_dt, end_dt],
        orders__status__in=['paid', 'shipped', 'delivered']
    ).annotate(
        web_spent=Sum('orders__total'),
        web_orders=Count('orders')
    )
    
    pos_top_customers = Customer.objects.filter(
        possale__created_at__date__range=[start_dt, end_dt]
    ).annotate(
        pos_spent=Sum('possale__total'),
        pos_orders=Count('possale')
    )
    
    # Combinar datos de clientes
    all_customers = Customer.objects.all()
    top_customers = []
    
    for customer in all_customers:
        web_data = next((c for c in web_top_customers if c.id == customer.id), None)
        pos_data = next((c for c in pos_top_customers if c.id == customer.id), None)
        
        web_spent = web_data.web_spent if web_data and web_data.web_spent else Decimal('0')
        web_orders = web_data.web_orders if web_data and web_data.web_orders else 0
        pos_spent = pos_data.pos_spent if pos_data and pos_data.pos_spent else Decimal('0')
        pos_orders = pos_data.pos_orders if pos_data and pos_data.pos_orders else 0
        
        total_spent = web_spent + pos_spent
        total_orders = web_orders + pos_orders
        
        if total_spent > 0:  # Solo incluir clientes con gastos
            avg_ticket = total_spent / total_orders if total_orders > 0 else Decimal('0')
            top_customers.append({
                'customer': customer,
                'total_spent': total_spent,
                'total_orders': total_orders,
                'avg_ticket': avg_ticket,
                'web_spent': web_spent,
                'pos_spent': pos_spent,
                'web_orders': web_orders,
                'pos_orders': pos_orders
            })
    
    # Ordenar por gasto total
    top_customers.sort(key=lambda x: x['total_spent'], reverse=True)
    top_customers = top_customers[:10]
    
    # 7. ESTADÍSTICAS DE ÓRDENES (Web + POS)
    web_order_stats = {
        'new': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='new').count(),
        'pending': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='pending').count(),
        'paid': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='paid').count(),
        'shipped': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='shipped').count(),
        'delivered': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='delivered').count(),
        'cancelled': Order.objects.filter(created_at__date__range=[start_dt, end_dt], status='cancelled').count(),
    }
    
    pos_sales_count = POSSale.objects.filter(created_at__date__range=[start_dt, end_dt]).count()
    
    # Combinar estadísticas
    order_stats = {
        'new': web_order_stats['new'],
        'pending': web_order_stats['pending'],
        'paid': web_order_stats['paid'] + pos_sales_count,  # POS se considera como "paid"
        'shipped': web_order_stats['shipped'],
        'delivered': web_order_stats['delivered'],
        'cancelled': web_order_stats['cancelled'],
        'pos_sales': pos_sales_count,
        'web_orders': sum(web_order_stats.values())
    }
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
        'sales_report': sales_report,
        'growth_percentage': round(growth_percentage, 2),
        'top_products': top_products,
        'daily_sales': daily_sales,
        'category_sales': category_sales,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'top_customers': top_customers,
        'order_stats': order_stats,
    }
    
    return render(request, 'custom_admin/reports.html', context)


@login_required
def admin_pos_sale_detail(request, pk):
    """Vista de detalle de venta POS desde el admin"""
    sale = get_object_or_404(POSSale.objects.select_related(
        'session', 'customer__user'
    ).prefetch_related('items__product'), pk=pk)
    
    context = {
        'sale': sale,
        'from_admin': True,
    }
    
    return render(request, 'custom_admin/pos_sale_detail.html', context)


@login_required
def admin_pos_sale_print(request, pk):
    """Vista de impresión de venta POS desde el admin"""
    sale = get_object_or_404(POSSale.objects.select_related(
        'session', 'customer__user'
    ).prefetch_related('items__product'), pk=pk)
    
    context = {
        'sale': sale,
        'from_admin': True,
    }
    
    return render(request, 'custom_admin/pos_sale_print.html', context)


@login_required
def admin_pos_sale_email(request, pk):
    """Vista para enviar recibo de venta POS por correo desde el admin"""
    if request.method == 'POST':
        sale = get_object_or_404(POSSale.objects.select_related(
            'session', 'customer__user'
        ).prefetch_related('items__product'), pk=pk)
        
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Debe proporcionar una dirección de correo')
            return redirect('custom_admin:admin_pos_sale_detail', pk=sale.id)
        
        try:
            # Renderizar el recibo como HTML
            html_content = render_to_string('custom_admin/pos_sale_print.html', {
                'sale': sale,
                'from_admin': True,
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
        
        return redirect('custom_admin:admin_pos_sale_detail', pk=sale.id)
    
    # Si es GET, mostrar formulario
    sale = get_object_or_404(POSSale.objects.select_related(
        'session', 'customer__user'
    ).prefetch_related('items__product'), pk=pk)
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'custom_admin/pos_sale_email_form.html', context)


# ==================== GESTIÓN DE INVENTARIO ====================

@login_required
def admin_adjust_stock(request, stock_id):
    """Ajustar stock de un producto"""
    stock = get_object_or_404(Stock.objects.select_related('product', 'warehouse'), id=stock_id)
    
    if request.method == 'POST':
        adjustment_type = request.POST.get('adjustment_type')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        if adjustment_type == 'add':
            # Agregar stock
            movement_quantity = quantity
            movement_type = 'in'
            reference = 'Ajuste positivo'
        else:
            # Reducir stock
            movement_quantity = -quantity
            movement_type = 'out'
            reference = 'Ajuste negativo'
        
        # Crear movimiento de stock
        StockMovement.objects.create(
            product=stock.product,
            warehouse=stock.warehouse,
            movement_type=movement_type,
            quantity=movement_quantity,
            reference=reference,
            notes=notes,
            user=request.user
        )
        
        messages.success(request, f'Stock ajustado exitosamente. Nuevo stock: {stock.quantity}')
        return redirect('custom_admin:admin_inventory')
    
    context = {
        'stock': stock,
    }
    return render(request, 'custom_admin/adjust_stock.html', context)


@login_required
def admin_transfer_stock(request, stock_id):
    """Transferir stock entre bodegas"""
    stock = get_object_or_404(Stock.objects.select_related('product', 'warehouse'), id=stock_id)
    warehouses = Warehouse.objects.filter(is_active=True).exclude(id=stock.warehouse.id)
    
    if request.method == 'POST':
        to_warehouse_id = request.POST.get('to_warehouse')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        if not to_warehouse_id or quantity <= 0:
            messages.error(request, 'Debe seleccionar una bodega destino y una cantidad válida')
            return redirect('custom_admin:admin_transfer_stock', stock_id=stock.id)
        
        if quantity > stock.quantity:
            messages.error(request, 'La cantidad a transferir no puede ser mayor al stock disponible')
            return redirect('custom_admin:admin_transfer_stock', stock_id=stock.id)
        
        to_warehouse = get_object_or_404(Warehouse, id=to_warehouse_id)
        
        # Crear transferencia
        transfer = StockTransfer.objects.create(
            from_warehouse=stock.warehouse,
            to_warehouse=to_warehouse,
            reference=f'Transferencia {stock.product.name}',
            notes=notes,
            created_by=request.user
        )
        
        # Crear item de transferencia
        StockTransferItem.objects.create(
            transfer=transfer,
            product=stock.product,
            quantity=quantity,
            notes=notes
        )
        
        messages.success(request, f'Transferencia creada exitosamente')
        return redirect('custom_admin:admin_inventory')
    
    context = {
        'stock': stock,
        'warehouses': warehouses,
    }
    return render(request, 'custom_admin/transfer_stock.html', context)


@login_required
def admin_stock_history(request, stock_id):
    """Historial de movimientos de un producto específico"""
    stock = get_object_or_404(Stock.objects.select_related('product', 'warehouse'), id=stock_id)
    
    movements = StockMovement.objects.filter(
        product=stock.product,
        warehouse=stock.warehouse
    ).select_related('user').order_by('-created_at')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(movements, 20)
    page_number = request.GET.get('page')
    movements = paginator.get_page(page_number)
    
    context = {
        'stock': stock,
        'movements': movements,
    }
    return render(request, 'custom_admin/stock_history.html', context)


@login_required
def admin_create_transfer(request):
    """Crear nueva transferencia de stock con formulario anidado"""
    from .forms import StockTransferForm, StockTransferItemFormSetWithStock
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    if request.method == 'POST':
        transfer_form = StockTransferForm(request.POST)
        formset = StockTransferItemFormSetWithStock(request.POST, prefix='formset')
        
        if transfer_form.is_valid() and formset.is_valid():
            # Guardar los items de la transferencia primero para validar
            items = formset.save(commit=False)
            
            # Filtrar solo los items válidos (con producto y cantidad)
            valid_items = []
            for item in items:
                if item.product and item.quantity and item.quantity > 0:
                    valid_items.append(item)
            
            # Validar que hay al menos un producto válido
            if not valid_items:
                messages.error(request, 'No puedes crear una transferencia sin productos. Por favor agrega al menos un producto.')
            else:
                # Crear la transferencia primero
                transfer = transfer_form.save(commit=False)
                transfer.created_by = request.user
                transfer.save()
                
                # Asignar la transferencia a los items
                formset.instance = transfer
                
                # Validar stock disponible para cada item válido
                stock_valid = True
                for item in valid_items:
                    try:
                        stock = Stock.objects.get(
                            product=item.product,
                            warehouse=transfer.from_warehouse
                        )
                        if item.quantity > stock.quantity:
                            messages.error(request, f'Stock insuficiente para {item.product.name}. Disponible: {stock.quantity}')
                            stock_valid = False
                            break
                    except Stock.DoesNotExist:
                        messages.error(request, f'El producto {item.product.name} no tiene stock en la bodega origen')
                        stock_valid = False
                        break
                
                if stock_valid:
                    # Guardar todos los items válidos
                    for item in valid_items:
                        item.transfer = transfer
                        item.save()
                    
                    # Eliminar items marcados para eliminar
                    for item in formset.deleted_objects:
                        item.delete()
                    
                    messages.success(request, f'Transferencia {transfer.reference} creada exitosamente con {len(valid_items)} productos')
                    return redirect('custom_admin:admin_inventory')
                else:
                    # Si hay errores de stock, eliminar la transferencia creada
                    transfer.delete()
    else:
        transfer_form = StockTransferForm()
        formset = StockTransferItemFormSetWithStock(prefix='formset')
    
    context = {
        'transfer_form': transfer_form,
        'formset': formset,
        'warehouses': warehouses,
    }
    return render(request, 'custom_admin/create_transfer.html', context)


@login_required
def api_products_with_stock(request):
    """API para obtener productos con stock en una bodega específica"""
    from django.http import JsonResponse
    
    warehouse_id = request.GET.get('warehouse')
    if not warehouse_id:
        return JsonResponse({'error': 'Warehouse ID required'}, status=400)
    
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
    except Warehouse.DoesNotExist:
        return JsonResponse({'error': 'Warehouse not found'}, status=404)
    
    # Obtener productos con stock en la bodega
    products_with_stock = Product.objects.filter(
        stock__warehouse=warehouse,
        stock__quantity__gt=0,
        is_active=True
    ).select_related().prefetch_related('images').distinct().order_by('name')
    
    products_data = []
    for product in products_with_stock:
        try:
            stock = Stock.objects.get(product=product, warehouse=warehouse)
            # Obtener la imagen principal del producto
            primary_image = product.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = product.images.first()  # Si no hay principal, tomar la primera
            
            image_url = primary_image.image.url if primary_image else None
            
            # Debug: Log de imágenes
            print(f"Producto: {product.name}")
            print(f"Total imágenes: {product.images.count()}")
            print(f"Imagen principal: {primary_image}")
            print(f"URL imagen: {image_url}")
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'stock': stock.quantity,
                'image': image_url,
                'price': float(product.price) if product.price else None,
                'category': product.category.name if product.category else None,
                'brand': product.brand.name if product.brand else None,
                'description': product.short_description or product.description[:100] + '...' if product.description else None
            })
        except Stock.DoesNotExist:
            continue
    
    return JsonResponse({
        'products': products_data,
        'warehouse': {
            'id': warehouse.id,
            'name': warehouse.name
        }
    })


@login_required
def admin_transfer_list(request):
    """Lista de transferencias de stock"""
    transfers = StockTransfer.objects.select_related(
        'from_warehouse', 'to_warehouse', 'created_by'
    ).prefetch_related('items__product').order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    warehouse_id = request.GET.get('warehouse')
    
    if status:
        transfers = transfers.filter(status=status)
    
    if warehouse_id:
        transfers = transfers.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page')
    transfers = paginator.get_page(page_number)
    
    # Datos para filtros
    warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
    status_choices = StockTransfer.STATUS_CHOICES
    
    context = {
        'transfers': transfers,
        'warehouses': warehouses,
        'status_choices': status_choices,
        'current_status': status,
        'current_warehouse': warehouse_id,
    }
    
    return render(request, 'custom_admin/transfer_list.html', context)


@login_required
def admin_transfer_detail(request, transfer_id):
    """Detalle de transferencia de stock"""
    transfer = get_object_or_404(
        StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'created_by'
        ).prefetch_related('items__product'),
        id=transfer_id
    )
    
    context = {
        'transfer': transfer,
    }
    
    return render(request, 'custom_admin/transfer_detail.html', context)


@login_required
def admin_complete_transfer(request, transfer_id):
    """Completar una transferencia pendiente"""
    try:
        transfer = StockTransfer.objects.get(id=transfer_id)
        
        if transfer.status != 'pending':
            messages.error(request, f'La transferencia {transfer.reference} no está pendiente. Estado actual: {transfer.get_status_display()}')
            return redirect('custom_admin:admin_transfer_detail', transfer_id=transfer_id)
        
        # Verificar que todos los productos tengan stock suficiente en la bodega origen
        insufficient_stock = []
        for item in transfer.items.all():
            try:
                stock = Stock.objects.get(
                    product=item.product,
                    warehouse=transfer.from_warehouse
                )
                if stock.quantity < item.quantity:
                    insufficient_stock.append({
                        'product': item.product.name,
                        'required': item.quantity,
                        'available': stock.quantity
                    })
            except Stock.DoesNotExist:
                insufficient_stock.append({
                    'product': item.product.name,
                    'required': item.quantity,
                    'available': 0
                })
        
        if insufficient_stock:
            messages.error(request, 'No se puede completar la transferencia. Stock insuficiente:')
            for stock_info in insufficient_stock:
                messages.error(request, f'- {stock_info["product"]}: Requerido {stock_info["required"]}, Disponible {stock_info["available"]}')
            return redirect('custom_admin:admin_transfer_detail', transfer_id=transfer_id)
        
        # Procesar la transferencia usando transacciones atómicas
        from django.db import transaction
        from django.utils import timezone
        
        with transaction.atomic():
            # Actualizar stock en bodega origen (reducir)
            for item in transfer.items.all():
                stock_from, created = Stock.objects.get_or_create(
                    product=item.product,
                    warehouse=transfer.from_warehouse,
                    defaults={'quantity': 0}
                )
                stock_from.quantity -= item.quantity
                stock_from.save()
                
                # Crear movimiento de stock para bodega origen
                StockMovement.objects.create(
                    product=item.product,
                    warehouse=transfer.from_warehouse,
                    quantity=-item.quantity,  # Negativo porque es salida
                    movement_type='out',
                    reference=f'Transferencia {transfer.reference}',
                    notes=f'Salida por transferencia a {transfer.to_warehouse.name}',
                    user=request.user
                )
            
            # Actualizar stock en bodega destino (aumentar)
            for item in transfer.items.all():
                stock_to, created = Stock.objects.get_or_create(
                    product=item.product,
                    warehouse=transfer.to_warehouse,
                    defaults={'quantity': 0}
                )
                stock_to.quantity += item.quantity
                stock_to.save()
                
                # Crear movimiento de stock para bodega destino
                StockMovement.objects.create(
                    product=item.product,
                    warehouse=transfer.to_warehouse,
                    quantity=item.quantity,  # Positivo porque es entrada
                    movement_type='in',
                    reference=f'Transferencia {transfer.reference}',
                    notes=f'Entrada por transferencia desde {transfer.from_warehouse.name}',
                    user=request.user
                )
            
            # Marcar transferencia como completada
            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
            transfer.save()
        
        messages.success(request, f'Transferencia {transfer.reference} completada exitosamente. Stock actualizado en ambas bodegas.')
        return redirect('custom_admin:admin_transfer_detail', transfer_id=transfer_id)
        
    except StockTransfer.DoesNotExist:
        messages.error(request, 'Transferencia no encontrada')
        return redirect('custom_admin:admin_inventory')
    except Exception as e:
        messages.error(request, f'Error al completar la transferencia: {str(e)}')
        return redirect('custom_admin:admin_transfer_detail', transfer_id=transfer_id)


@login_required
def admin_warehouse_management(request):
    """Gestión de bodegas"""
    warehouses = Warehouse.objects.all().order_by('name')
    
    context = {
        'warehouses': warehouses,
    }
    return render(request, 'custom_admin/warehouse_management.html', context)


@login_required
def admin_create_warehouse(request):
    """Crear nueva bodega"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        address = request.POST.get('address')
        city = request.POST.get('city')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        is_main = request.POST.get('is_main') == 'on'
        
        if not name or not code or not address or not city:
            messages.error(request, 'Debe completar todos los campos obligatorios')
            return redirect('custom_admin:admin_create_warehouse')
        
        # Verificar que el código sea único
        if Warehouse.objects.filter(code=code).exists():
            messages.error(request, 'El código de bodega ya existe')
            return redirect('custom_admin:admin_create_warehouse')
        
        warehouse = Warehouse.objects.create(
            name=name,
            code=code,
            address=address,
            city=city,
            phone=phone,
            email=email,
            is_main=is_main
        )
        
        messages.success(request, f'Bodega {warehouse.name} creada exitosamente')
        return redirect('custom_admin:admin_warehouse_management')
    
    return render(request, 'custom_admin/create_warehouse.html')


@login_required
def admin_edit_warehouse(request, warehouse_id):
    """Editar bodega"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        address = request.POST.get('address')
        city = request.POST.get('city')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        is_main = request.POST.get('is_main') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not code or not address or not city:
            messages.error(request, 'Debe completar todos los campos obligatorios')
            return redirect('custom_admin:admin_edit_warehouse', warehouse_id=warehouse.id)
        
        # Verificar que el código sea único (excluyendo la bodega actual)
        if Warehouse.objects.filter(code=code).exclude(id=warehouse.id).exists():
            messages.error(request, 'El código de bodega ya existe')
            return redirect('custom_admin:admin_edit_warehouse', warehouse_id=warehouse.id)
        
        warehouse.name = name
        warehouse.code = code
        warehouse.address = address
        warehouse.city = city
        warehouse.phone = phone
        warehouse.email = email
        warehouse.is_main = is_main
        warehouse.is_active = is_active
        warehouse.save()
        
        messages.success(request, f'Bodega {warehouse.name} actualizada exitosamente')
        return redirect('custom_admin:admin_warehouse_management')
    
    context = {'warehouse': warehouse}
    return render(request, 'custom_admin/edit_warehouse.html', context)


@login_required
def admin_toggle_warehouse_status(request, warehouse_id):
    """Activar/Desactivar bodega"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    warehouse.is_active = not warehouse.is_active
    warehouse.save()
    
    status = "activada" if warehouse.is_active else "desactivada"
    messages.success(request, f'Bodega {warehouse.name} {status} exitosamente')
    
    return redirect('custom_admin:admin_warehouse_management')


@login_required
def admin_warehouse_detail(request, warehouse_id):
    """Detalle de bodega"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    # Obtener stocks de esta bodega
    stocks = Stock.objects.filter(warehouse=warehouse).select_related('product')
    
    # Estadísticas
    total_products = stocks.count()
    low_stock_count = stocks.filter(quantity__lte=F('min_stock')).count()
    out_of_stock_count = stocks.filter(quantity=0).count()
    
    context = {
        'warehouse': warehouse,
        'stocks': stocks,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    return render(request, 'custom_admin/warehouse_detail.html', context)


@login_required
def admin_inventory_reports(request):
    """Reportes de inventario"""
    # Estadísticas generales
    total_products = Product.objects.filter(is_active=True).count()
    total_warehouses = Warehouse.objects.filter(is_active=True).count()
    out_of_stock = Stock.objects.filter(quantity=0).count()
    low_stock = Stock.objects.filter(quantity__lte=F('min_stock')).count()
    
    # Productos con stock bajo
    low_stock_items = Stock.objects.filter(
        quantity__lte=F('min_stock')
    ).select_related('product', 'warehouse').order_by('quantity')
    
    # Productos sin stock
    out_of_stock_items = Stock.objects.filter(
        quantity=0
    ).select_related('product', 'warehouse').order_by('product__name')
    
    # Movimientos recientes
    recent_movements = StockMovement.objects.select_related(
        'product', 'warehouse', 'user'
    ).order_by('-created_at')[:10]
    
    # Transferencias pendientes
    pending_transfers = StockTransfer.objects.filter(
        status='pending'
    ).select_related('from_warehouse', 'to_warehouse', 'created_by')
    
    context = {
        'total_products': total_products,
        'total_warehouses': total_warehouses,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'recent_movements': recent_movements,
        'pending_transfers': pending_transfers,
    }
    
    return render(request, 'custom_admin/inventory_reports.html', context)


@login_required
def admin_wompi_config(request):
    """Configuración de Wompi"""
    config = WompiConfig.get_config()
    
    if request.method == 'POST':
        try:
            config.public_key = request.POST.get('public_key', '').strip()
            config.private_key = request.POST.get('private_key', '').strip()
            config.events_secret = request.POST.get('events_secret', '').strip()
            config.integrity_secret = request.POST.get('integrity_secret', '').strip()
            config.environment = request.POST.get('environment', 'sandbox')
            config.is_active = request.POST.get('is_active') == 'on'
            config.save()
            
            messages.success(request, 'Configuración de Wompi actualizada exitosamente.')
            return redirect('custom_admin:admin_wompi_config')
        except Exception as e:
            messages.error(request, f'Error al actualizar la configuración: {str(e)}')
    
    context = {
        'config': config,
    }
    
    return render(request, 'custom_admin/wompi_config.html', context)


@login_required
def admin_home_banner_config(request):
    """Configuración del banner principal del home."""
    config = HomeBannerConfig.get_config()

    if request.method == 'POST':
        form = HomeBannerConfigForm(
            request.POST,
            request.FILES,
            instance=config,
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Banner del home actualizado exitosamente.',
            )
            return redirect('custom_admin:admin_home_banner_config')
        messages.error(request, 'Revisa los campos del formulario del banner.')
    else:
        form = HomeBannerConfigForm(instance=config)

    context = {
        'form': form,
        'config': config,
    }
    return render(request, 'custom_admin/home_banner_config.html', context)


# --------- Detalle de Orden ---------
@login_required
def admin_order_detail(request, pk):
    """Muestra el detalle de una orden web"""
    from orders.models import Order
    try:
        order = Order.objects.select_related('customer__user').prefetch_related('items__product').get(pk=pk)
    except Order.DoesNotExist:
        messages.error(request, 'Orden no encontrada.')
        return redirect('custom_admin:admin_orders')

    context = {
        'order': order,
    }
    return render(request, 'custom_admin/order_detail.html', context)

