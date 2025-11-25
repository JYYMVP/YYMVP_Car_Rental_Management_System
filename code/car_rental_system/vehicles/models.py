from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Vehicle(models.Model):
    VEHICLE_STATUS_CHOICES = [
        ('AVAILABLE', '可用'),
        ('RENTED', '已租'),
        ('MAINTENANCE', '维修中'),
    ]
    
    license_plate = models.CharField(
        '车牌号',
        max_length=20,
        unique=True,
        help_text='车辆唯一标识'
    )
    brand = models.CharField(
        '品牌',
        max_length=50,
        help_text='汽车品牌'
    )
    model = models.CharField(
        '型号',
        max_length=50,
        help_text='汽车型号'
    )
    vehicle_type = models.CharField(
        '车辆类型',
        max_length=20,
        help_text='如：轿车、SUV、MPV等'
    )
    color = models.CharField(
        '颜色',
        max_length=20,
        help_text='车身颜色'
    )
    seats = models.PositiveIntegerField(
        '座位数',
        default=5,
        validators=[MinValueValidator(2)],
        help_text='车辆座位数（2-50座）'
    )
    daily_rate = models.DecimalField(
        '日租金',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='每日租金价格'
    )
    status = models.CharField(
        '车辆状态',
        max_length=20,
        choices=VEHICLE_STATUS_CHOICES,
        default='AVAILABLE',
        help_text='当前车辆状态'
    )
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = '车辆'
        verbose_name_plural = '车辆'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_plate']),
            models.Index(fields=['status']),
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['seats']),  # 为座位数添加索引，优化搜索性能
        ]
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"
    
    def __repr__(self):
        return f"<Vehicle: {self.license_plate}>"
