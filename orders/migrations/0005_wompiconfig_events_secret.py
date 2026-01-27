from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_wompiconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='wompiconfig',
            name='events_secret',
            field=models.CharField(blank=True, max_length=200, verbose_name='Secreto de Eventos'),
        ),
    ]
