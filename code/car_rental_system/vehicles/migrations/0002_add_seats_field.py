# Generated manually for optimization

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        # 添加座位数字段
        migrations.AddField(
            model_name='vehicle',
            name='seats',
            field=models.PositiveIntegerField(
                default=5,
                help_text='车辆座位数（2-50座）',
                validators=[django.core.validators.MinValueValidator(2)],
                verbose_name='座位数'
            ),
        ),
        # 为座位数添加索引，优化搜索性能
        migrations.AddIndex(
            model_name='vehicle',
            index=models.Index(fields=['seats'], name='vehicles_seats_idx'),
        ),
    ]

