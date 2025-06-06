# Generated by Django 5.1.6 on 2025-04-01 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authapp', '0010_order_unique_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'Cash on Delivery'), ('ONLINE', 'Online Payment')], default='COD', max_length=20),
        ),
    ]
