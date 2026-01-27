from django.db import models
from django.contrib.auth.models import User


class ReportTemplate(models.Model):
    REPORT_TYPES = [
        ('sales', 'Ventas'),
        ('inventory', 'Inventario'),
        ('products', 'Productos'),
        ('customers', 'Clientes'),
        ('financial', 'Financiero'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nombre")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Tipo de reporte")
    description = models.TextField(blank=True, verbose_name="Descripción")
    template_data = models.JSONField(verbose_name="Datos del template")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Template de reporte"
        verbose_name_plural = "Templates de reportes"
        ordering = ['name']

    def __str__(self):
        return self.name


class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nombre")
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name="Template")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Frecuencia")
    email_recipients = models.TextField(verbose_name="Destinatarios de email")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    last_run = models.DateTimeField(blank=True, null=True, verbose_name="Última ejecución")
    next_run = models.DateTimeField(blank=True, null=True, verbose_name="Próxima ejecución")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Programación de reporte"
        verbose_name_plural = "Programaciones de reportes"
        ordering = ['name']

    def __str__(self):
        return self.name













