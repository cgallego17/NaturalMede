from rest_framework import serializers
from .models import Order, OrderItem, ShippingRate
from customers.serializers import CustomerSerializer
from catalog.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'unit_price', 'iva_percentage',
            'subtotal', 'iva_amount', 'total'
        ]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'status', 'payment_method',
            'subtotal', 'iva_amount', 'shipping_cost', 'total',
            'shipping_address', 'shipping_city', 'shipping_phone', 'shipping_notes',
            'notes', 'internal_notes', 'items',
            'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class ShippingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRate
        fields = [
            'id', 'city', 'min_weight', 'max_weight', 'cost',
            'estimated_days', 'is_active'
        ]











