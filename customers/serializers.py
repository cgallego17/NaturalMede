from rest_framework import serializers
from .models import Customer, CustomerAddress


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = [
            'id', 'name', 'address', 'city', 'phone', 'notes',
            'is_default', 'created_at'
        ]


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    total_orders = serializers.ReadOnlyField()
    total_spent = serializers.ReadOnlyField()
    addresses = CustomerAddressSerializer(many=True, read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'customer_type', 'document_type', 'document_number',
            'phone', 'address', 'city', 'birth_date', 'notes', 'is_active',
            'full_name', 'email', 'total_orders', 'total_spent', 'addresses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']











