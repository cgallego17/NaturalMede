from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('custom_admin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='homebannerconfig',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                verbose_name='Creado en',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='homebannerconfig',
            name='display_order',
            field=models.PositiveIntegerField(default=0, verbose_name='Orden'),
        ),
        migrations.AlterModelOptions(
            name='homebannerconfig',
            options={
                'ordering': ['display_order', '-created_at'],
                'verbose_name': 'Banner Home',
                'verbose_name_plural': 'Banners Home',
            },
        ),
    ]
