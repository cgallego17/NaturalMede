from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'brand', 'price', 'is_active', 'is_featured', 'created_at']
    list_filter = ['category', 'brand', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'sku', 'barcode', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'slug', 'description', 'short_description', 'sku', 'barcode')
        }),
        ('Categorización', {
            'fields': ('category', 'brand')
        }),
        ('Precios', {
            'fields': ('price', 'cost_price', 'iva_percentage')
        }),
        ('Características', {
            'fields': ('weight', 'dimensions')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_items', 'total_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'cart', 'quantity', 'total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'cart__user__username']
    readonly_fields = ['created_at', 'updated_at']







