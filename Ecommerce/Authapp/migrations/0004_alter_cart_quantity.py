# Generated by Django 5.1.6 on 2025-03-29 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authapp', '0003_alter_cart_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
