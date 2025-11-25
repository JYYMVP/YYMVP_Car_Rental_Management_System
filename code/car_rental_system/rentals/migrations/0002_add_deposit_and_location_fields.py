# Generated manually for optimization

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0001_initial'),
    ]

    operations = [
        # 添加押金字段
        migrations.AddField(
            model_name='rental',
            name='deposit',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='租赁押金金额',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='押金'
            ),
        ),
        # 添加取车地点字段
        migrations.AddField(
            model_name='rental',
            name='pickup_location',
            field=models.CharField(
                default='门店',
                help_text='取车地点',
                max_length=200,
                verbose_name='取车地点'
            ),
        ),
        # 添加还车地点字段
        migrations.AddField(
            model_name='rental',
            name='return_location',
            field=models.CharField(
                blank=True,
                help_text='还车地点（异地还车时填写）',
                max_length=200,
                null=True,
                verbose_name='还车地点'
            ),
        ),
        # 添加是否异地还车字段
        migrations.AddField(
            model_name='rental',
            name='is_cross_location_return',
            field=models.BooleanField(
                default=False,
                help_text='是否异地还车',
                verbose_name='是否异地还车'
            ),
        ),
        # 添加异地还车费用字段
        migrations.AddField(
            model_name='rental',
            name='cross_location_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='异地还车产生的额外费用',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='异地还车费用'
            ),
        ),
    ]

