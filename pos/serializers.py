from rest_framework import serializers
from .models import POSSale, POSSaleItem, POSSession
from customers.serializers import CustomerSerializer
from catalog.serializers import ProductSerializer


class POSSaleItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = POSSaleItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 'unit_price',
            'iva_percentage', 'discount_percentage', 'subtotal',
            'iva_amount', 'discount_amount', 'total'
        ]


class POSSaleSerializer(serializers.ModelSerializer):
    items = POSSaleItemSerializer(many=True, read_only=True)
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = POSSale
        fields = [
            'id', 'order_type', 'order_type_display', 'sale_number',
            'customer', 'customer_id', 'payment_method', 'payment_method_display',
            'subtotal', 'iva_amount', 'discount_amount', 'total',
            'notes', 'barcode_scanned', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['sale_number', 'created_at', 'updated_at']


class POSSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = POSSession
        fields = [
            'id', 'session_id', 'user', 'user_name', 'warehouse',
            'status', 'opening_cash', 'closing_cash', 'total_sales',
            'total_transactions', 'opened_at', 'closed_at'
        ]
        read_only_fields = ['session_id', 'opened_at', 'closed_at']










