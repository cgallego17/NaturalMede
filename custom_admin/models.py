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
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado en',
    )

    class Meta:
        verbose_name = 'Configuración Banner Home'
        verbose_name_plural = 'Configuración Banner Home'

    def __str__(self):
        return 'Banner principal home'

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config
