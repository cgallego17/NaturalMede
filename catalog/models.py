from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descripción")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Imagen")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descripción")
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name="Logo")
    website = models.URLField(blank=True, verbose_name="Sitio web")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Descripción")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="Descripción corta")
    
    # Relaciones
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Categoría")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Marca")
    
    # Precios
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Precio")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Precio de costo")
    iva_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'), verbose_name="% IVA")
    
    # Características del producto
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    barcode = models.CharField(max_length=50, blank=True, verbose_name="Código de barras")
    weight = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True, verbose_name="Peso (kg)")
    dimensions = models.CharField(max_length=100, blank=True, verbose_name="Dimensiones")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def price_with_iva(self):
        """Calcula el precio con IVA incluido"""
        return self.price * (1 + self.iva_percentage / 100)

    @property
    def iva_amount(self):
        """Calcula el monto del IVA"""
        return self.price * (self.iva_percentage / 100)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Producto")
    image = models.ImageField(upload_to='products/', verbose_name="Imagen")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Texto alternativo")
    is_primary = models.BooleanField(default=False, verbose_name="Imagen principal")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de productos"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Imagen {self.order}"


class Cart(models.Model):
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Clave de sesión")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Usuario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        if self.user:
            return f"Carrito de {self.user.username}"
        return f"Carrito de sesión {self.session_key}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.total for item in self.items.all())

    @property
    def total_iva(self):
        return sum(item.iva_amount for item in self.items.all())

    @property
    def total_with_iva(self):
        return self.total_amount + self.total_iva


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Carrito")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Item del carrito"
        verbose_name_plural = "Items del carrito"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total(self):
        return self.product.price * self.quantity

    @property
    def iva_amount(self):
        return self.total * (self.product.iva_percentage / 100)

    @property
    def total_with_iva(self):
        return self.total + self.iva_amount











