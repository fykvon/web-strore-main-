# Generated by Django 4.2.6 on 2023-10-30 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_comparison'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='discount',
            field=models.ManyToManyField(related_name='products', to='store.discount', verbose_name='Скидка'),
        ),
    ]
