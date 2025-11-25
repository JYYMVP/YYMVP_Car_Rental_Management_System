from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
import re


class Customer(models.Model):
    MEMBER_LEVEL_CHOICES = [
        ('NORMAL', '普通会员'),
        ('VIP', 'VIP会员'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name='customer_profile',
        blank=True,
        null=True,
        verbose_name='关联用户',
        help_text='关联的用户账号'
    )
    name = models.CharField(
        '姓名',
        max_length=100,
        help_text='客户姓名'
    )
    phone = models.CharField(
        '联系电话',
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^1[3-9]\d{9}$',
                message='请输入有效的手机号码'
            )
        ],
        help_text='11位手机号码'
    )
    email = models.EmailField(
        '邮箱',
        blank=True,
        null=True,
        help_text='电子邮箱地址'
    )
    id_card = models.CharField(
        '身份证号',
        max_length=18,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$',
                message='请输入有效的身份证号码'
            )
        ],
        help_text='18位身份证号码'
    )
    license_number = models.CharField(
        '驾照号',
        max_length=20,
        unique=True,
        help_text='驾驶证号码'
    )
    license_type = models.CharField(
        '驾照类型',
        max_length=10,
        choices=[
            ('A', 'A类驾照'),
            ('B', 'B类驾照'),
            ('C', 'C类驾照'),
        ],
        default='C',
        help_text='驾驶证类型'
    )
    member_level = models.CharField(
        '会员等级',
        max_length=20,
        choices=MEMBER_LEVEL_CHOICES,
        default='NORMAL',
        help_text='客户会员等级'
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
        db_table = 'customers'
        verbose_name = '客户'
        verbose_name_plural = '客户'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id_card']),
            models.Index(fields=['license_number']),
            models.Index(fields=['phone']),
            models.Index(fields=['member_level']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    def __repr__(self):
        return f"<Customer: {self.name}>"
