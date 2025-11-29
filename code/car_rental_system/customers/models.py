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
    
    def check_vip_upgrade_eligibility(self):
        """
        检查客户是否符合VIP升级条件
        条件：连续10个已完成订单都满足：
        1. 没有超时归还（overdue_fee == 0）
        2. 没有不诚信的异地还车（选择了异地还车实际也异地还车，或没选择异地还车实际也没异地还车）
        
        返回：(是否符合条件, 连续诚信订单数)
        """
        from rentals.models import Rental
        from decimal import Decimal
        
        # 获取所有已完成的订单，按创建时间倒序排列（最新的在前）
        completed_rentals = Rental.objects.filter(
            customer=self,
            status='COMPLETED',
            actual_return_date__isnull=False
        ).order_by('-created_at')
        
        consecutive_good_count = 0
        
        # 从最近的订单开始检查，连续计数满足条件的订单
        for rental in completed_rentals:
            # 检查是否超时归还
            has_overdue = rental.overdue_fee and rental.overdue_fee > Decimal('0.00')
            
            # 检查是否不诚信的异地还车
            is_dishonest_cross_location = False
            if rental.actual_return_location and rental.pickup_location:
                actual_is_cross = rental.actual_return_location.strip() != rental.pickup_location.strip()
                expected_is_cross = rental.is_cross_location_return
                # 如果不匹配，说明不诚信
                if actual_is_cross != expected_is_cross:
                    is_dishonest_cross_location = True
            
            # 如果订单满足条件（没有超时且诚信）
            if not has_overdue and not is_dishonest_cross_location:
                consecutive_good_count += 1
            else:
                # 一旦遇到不满足条件的订单，就中断计数
                break
        
        # 如果连续10个订单都满足条件
        is_eligible = consecutive_good_count >= 10
        return is_eligible, consecutive_good_count
    
    def upgrade_to_vip(self):
        """将客户升级为VIP"""
        if self.member_level != 'VIP':
            self.member_level = 'VIP'
            self.save(update_fields=['member_level', 'updated_at'])
            return True
        return False
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    def __repr__(self):
        return f"<Customer: {self.name}>"
