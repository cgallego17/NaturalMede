from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('normal', 'Normal'),
        ('vip', 'VIP'),
    ]

    CHANNEL_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('whatsapp', 'WhatsApp'),
        ('google', 'Google'),
        ('referral', 'Referido por cliente'),
        ('walk_in', 'Cliente de tienda física'),
        ('website', 'Sitio web'),
        ('email', 'Email'),
        ('phone', 'Llamada telefónica'),
        ('other', 'Otro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPES, default='normal', verbose_name="Tipo de cliente")
    document_type = models.CharField(max_length=20, verbose_name="Tipo de documento")
    document_number = models.CharField(max_length=20, unique=True, verbose_name="Número de documento")
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="El número de teléfono debe tener el formato: '+999999999'. Hasta 15 dígitos permitidos.")
    phone = models.CharField(validators=[phone_regex], max_length=17, verbose_name="Teléfono")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='other', verbose_name="Canal de llegada")
    notes = models.TextField(blank=True, verbose_name="Notas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_customer_type_display()})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def total_spent(self):
        from orders.models import Order
        return sum(order.total for order in self.orders.filter(status='delivered'))


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses', verbose_name="Cliente")
    name = models.CharField(max_length=100, verbose_name="Nombre de la dirección")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    notes = models.TextField(blank=True, verbose_name="Notas")
    is_default = models.BooleanField(default=False, verbose_name="Dirección por defecto")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")

    class Meta:
        verbose_name = "Dirección de cliente"
        verbose_name_plural = "Direcciones de clientes"
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.customer.full_name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Solo puede haber una dirección por defecto por cliente
            CustomerAddress.objects.filter(customer=self.customer, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Country(models.Model):
    external_id = models.PositiveIntegerField(unique=True, verbose_name="ID Externo")
    name = models.CharField(max_length=100, unique=True, verbose_name="País")
    iso2 = models.CharField(max_length=2, blank=True, null=True, verbose_name="ISO2")
    iso3 = models.CharField(max_length=3, blank=True, null=True, verbose_name="ISO3")

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='departments', verbose_name="País")
    external_id = models.PositiveIntegerField(verbose_name="ID Externo")
    name = models.CharField(max_length=150, verbose_name="Departamento")
    iso2 = models.CharField(max_length=10, blank=True, null=True, verbose_name="ISO2")

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['country__name', 'name']
        constraints = [
            models.UniqueConstraint(fields=['country', 'external_id'], name='uniq_department_external_id'),
            models.UniqueConstraint(fields=['country', 'name'], name='uniq_department_name'),
        ]

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class City(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cities', verbose_name="Departamento")
    external_id = models.PositiveIntegerField(verbose_name="ID Externo")
    name = models.CharField(max_length=150, verbose_name="Ciudad")

    class Meta:
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        ordering = ['department__country__name', 'department__name', 'name']
        constraints = [
            models.UniqueConstraint(fields=['department', 'external_id'], name='uniq_city_external_id'),
            models.UniqueConstraint(fields=['department', 'name'], name='uniq_city_name'),
        ]

    def __str__(self):
        return f"{self.name} ({self.department.name})"
