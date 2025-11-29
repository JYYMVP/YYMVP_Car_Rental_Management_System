# Generated manually for return location and overdue fee

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0003_settlement_fields'),
    ]

    operations = [
        # 添加实际还车门店字段
        migrations.AddField(
            model_name='rental',
            name='actual_return_location',
            field=models.CharField(
                blank=True,
                help_text='实际还车门店',
                max_length=200,
                null=True,
                verbose_name='实际还车门店'
            ),
        ),
        # 添加超时还车费用字段
        migrations.AddField(
            model_name='rental',
            name='overdue_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='超时还车产生的赔偿费用',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='超时还车费用'
            ),
        ),
    ]

