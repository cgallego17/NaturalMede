from django.db import models


class HomeBannerConfig(models.Model):
    image = models.ImageField(
        upload_to='home_banners/',
        blank=True,
        null=True,
        verbose_name='Imagen banner',
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Texto alternativo',
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name='Orden')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado en',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado en',
    )

    class Meta:
        verbose_name = 'Banner Home'
        verbose_name_plural = 'Banners Home'
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f'Banner Home #{self.pk}'
