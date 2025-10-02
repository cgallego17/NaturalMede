from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'orders', api_views.OrderViewSet)
router.register(r'shipping-rates', api_views.ShippingRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('orders/<int:order_id>/status/', api_views.OrderStatusUpdateAPIView.as_view(), name='api_order_status_update'),
    path('shipping/calculate/', api_views.ShippingCostCalculateAPIView.as_view(), name='api_shipping_calculate'),
]











