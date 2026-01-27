from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product, Category, Brand, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer
from customers.models import City, Country, Department


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
    serializer_class = ProductSerializer


@api_view(['GET'])
def product_list_api(request):
    """API simple para obtener productos para el POS"""
    products = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
    
    # Filtros opcionales
    search = request.GET.get('search')
    category = request.GET.get('category')
    featured = request.GET.get('featured')
    
    if search:
        products = products.filter(
            name__icontains=search
        ) | products.filter(
            sku__icontains=search
        ) | products.filter(
            barcode__icontains=search
        )
    
    if category:
        products = products.filter(category_id=category)
    
    if featured:
        products = products.filter(is_featured=True)
    
    # Serializar datos
    data = []
    for product in products:
        # Obtener imagen principal
        main_image = None
        if product.images.exists():
            main_image_obj = product.images.filter(is_primary=True).first()
            if not main_image_obj:
                main_image_obj = product.images.first()
            if main_image_obj:
                main_image = main_image_obj.image.url
        
        # Obtener stock total
        from inventory.models import Stock
        from django.db.models import Sum
        total_stock = Stock.objects.filter(product=product).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.price),
            'barcode': product.barcode,
            'is_active': product.is_active,
            'is_featured': product.is_featured,
            'stock': total_stock,
            'image': main_image,
            'category': {
                'id': product.category.id,
                'name': product.category.name
            },
            'brand': {
                'id': product.brand.id,
                'name': product.brand.name
            }
        })
    
    return Response(data)


@api_view(['GET'])
def location_countries_api(request):
    countries = Country.objects.all().order_by('name')
    return Response([
        {'id': c.id, 'name': c.name}
        for c in countries
    ])


@api_view(['GET'])
def location_departments_api(request):
    country_id = request.GET.get('country_id')
    if not country_id:
        return Response([], status=status.HTTP_200_OK)

    departments = Department.objects.filter(country_id=country_id).order_by('name')
    return Response([
        {'id': d.id, 'name': d.name}
        for d in departments
    ])


@api_view(['GET'])
def location_cities_api(request):
    department_id = request.GET.get('department_id')
    if not department_id:
        return Response([], status=status.HTTP_200_OK)

    cities = City.objects.filter(department_id=department_id).order_by('name')
    return Response([
        {'id': c.id, 'name': c.name}
        for c in cities
    ])


# ViewSets
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        featured = self.request.query_params.get('featured', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = None  # We'll handle serialization manually
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return Cart.objects.filter(id=cart.id)
    
    def list(self, request, *args, **kwargs):
        cart = self.get_queryset().first()
        if not cart:
            return Response({'items': [], 'total_items': 0, 'total_amount': 0})
        
        items = []
        for item in cart.items.all():
            items.append({
                'id': item.id,
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'price': float(item.product.price),
                    'barcode': item.product.barcode,
                },
                'quantity': item.quantity,
                'total': float(item.total),
                'iva_amount': float(item.iva_amount),
                'total_with_iva': float(item.total_with_iva),
            })
        
        return Response({
            'items': items,
            'total_items': cart.total_items,
            'total_amount': float(cart.total_amount),
            'total_iva': float(cart.total_iva),
            'total_with_iva': float(cart.total_with_iva),
        })


# API Views for Cart operations
class CartAddAPIView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        
        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'message': 'Product added to cart',
            'cart_item_id': cart_item.id,
            'quantity': cart_item.quantity
        })


class CartRemoveAPIView(generics.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cart
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                return Response({'error': 'No cart found'}, status=status.HTTP_404_NOT_FOUND)
            cart = get_object_or_404(Cart, session_key=session_key)
        
        # Remove cart item
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.delete()
        
        return Response({'message': 'Product removed from cart'})


class CartUpdateAPIView(generics.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0:
            return Response({'error': 'quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cart
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                return Response({'error': 'No cart found'}, status=status.HTTP_404_NOT_FOUND)
            cart = get_object_or_404(Cart, session_key=session_key)
        
        # Update cart item
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'message': 'Cart item updated',
            'quantity': cart_item.quantity
        })


class ProductSearchAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
        
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        featured = self.request.query_params.get('featured', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        return queryset