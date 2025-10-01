from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'products', api_views.ProductViewSet)
router.register(r'categories', api_views.CategoryViewSet)
router.register(r'brands', api_views.BrandViewSet)
router.register(r'cart', api_views.CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/add/', api_views.CartAddAPIView.as_view(), name='api_cart_add'),
    path('cart/remove/', api_views.CartRemoveAPIView.as_view(), name='api_cart_remove'),
    path('cart/update/', api_views.CartUpdateAPIView.as_view(), name='api_cart_update'),
    path('products/search/', api_views.ProductSearchAPIView.as_view(), name='api_product_search'),
]







