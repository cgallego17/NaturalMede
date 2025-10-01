from rest_framework import serializers
from .models import Product, Category, Brand, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'short_description',
            'price', 'cost_price', 'iva_percentage', 'barcode',
            'weight', 'dimensions', 'is_active', 'is_featured',
            'created_at', 'updated_at', 'category', 'brand',
            'category_name', 'brand_name', 'images', 'stock'
        ]
    
    def get_stock(self, obj):
        # Obtener el stock total de todas las bodegas
        from inventory.models import Stock
        from django.db.models import Sum
        total_stock = Stock.objects.filter(product=obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        return total_stock


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'is_active']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'logo', 'website', 'is_active']