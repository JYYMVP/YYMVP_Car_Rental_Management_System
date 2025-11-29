from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal
from django.utils import timezone
from customers.models import Customer
from vehicles.models import Vehicle


class Rental(models.Model):
    RENTAL_STATUS_CHOICES = [
        ('PENDING', '预订中'),
        ('ONGOING', '进行中'),
        ('OVERDUE', '已超时未归还'),
        ('COMPLETED', '已完成'),
        ('CANCELLED', '已取消'),
    ]
    
    SETTLEMENT_STATUS_CHOICES = [
        ('UNSETTLED', '未结算'),
        ('PARTIAL', '部分结算'),
        ('SETTLED', '已结算'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='客户'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='车辆'
    )
    start_date = models.DateField(
        '租赁开始日期',
        help_text='租赁开始日期'
    )
    end_date = models.DateField(
        '租赁结束日期',
        help_text='租赁结束日期'
    )
    actual_return_date = models.DateField(
        '实际还车日期',
        blank=True,
        null=True,
        help_text='实际还车日期'
    )
    actual_return_location = models.CharField(
        '实际还车门店',
        max_length=200,
        blank=True,
        null=True,
        help_text='实际还车门店'
    )
    overdue_fee = models.DecimalField(
        '超时还车费用',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='超时还车产生的赔偿费用'
    )
    total_amount = models.DecimalField(
        '总金额',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='租赁总费用'
    )
    deposit = models.DecimalField(
        '押金',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='租赁押金金额'
    )
    pickup_location = models.CharField(
        '取车地点',
        max_length=200,
        default='门店',
        help_text='取车地点'
    )
    return_location = models.CharField(
        '还车地点',
        max_length=200,
        blank=True,
        null=True,
        help_text='还车地点（异地还车时填写）'
    )
    is_cross_location_return = models.BooleanField(
        '是否异地还车',
        default=False,
        help_text='是否异地还车'
    )
    cross_location_fee = models.DecimalField(
        '异地还车费用',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='异地还车产生的额外费用'
    )
    status = models.CharField(
        '订单状态',
        max_length=20,
        choices=RENTAL_STATUS_CHOICES,
        default='PENDING',
        help_text='当前订单状态'
    )
    notes = models.TextField(
        '备注',
        blank=True,
        null=True,
        help_text='订单备注信息'
    )
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )
    settlement_status = models.CharField(
        '结算状态',
        max_length=20,
        choices=SETTLEMENT_STATUS_CHOICES,
        default='UNSETTLED',
        help_text='订单费用结算状态'
    )
    settled_at = models.DateTimeField(
        '结算时间',
        blank=True,
        null=True,
        help_text='订单完成并结算的时间'
    )
    amount_paid = models.DecimalField(
        '累计支付金额',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='用户累计支付金额（不含退款）'
    )
    amount_refunded = models.DecimalField(
        '累计退款金额',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='系统累计退款金额'
    )
    
    class Meta:
        db_table = 'rentals'
        verbose_name = '租赁订单'
        verbose_name_plural = '租赁订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['vehicle', 'status']),
        ]
    
    @classmethod
    def auto_update_status(cls):
        """
        自动更新订单状态
        - 预订中 → 进行中：当到达开始日期时
        - 进行中 → 已超时未归还：当超过结束日期时
        使用缓存避免频繁更新（每5分钟最多更新一次）
        """
        from django.core.cache import cache
        from django.db import transaction
        
        cache_key = 'rental_status_auto_update'
        last_update = cache.get(cache_key)
        
        # 如果5分钟内已更新过，跳过
        if last_update:
            return
        
        today = date.today()
        updated_count = 0
        
        try:
            with transaction.atomic():
                # 1. 激活预订中订单（预订中 → 进行中）
                pending_rentals = cls.objects.filter(
                    status='PENDING',
                    start_date__lte=today
                ).select_related('vehicle')
                
                for rental in pending_rentals:
                    rental.status = 'ONGOING'
                    rental.save(update_fields=['status', 'updated_at'])
                    updated_count += 1
                    
                    # 更新车辆状态为已租
                    if rental.vehicle.status == 'AVAILABLE':
                        rental.vehicle.status = 'RENTED'
                        rental.vehicle.save(update_fields=['status'])
                
                # 2. 更新过期订单（进行中 → 已超时未归还）
                overdue_rentals = cls.objects.filter(
                    status='ONGOING',
                    end_date__lt=today
                )
                
                for rental in overdue_rentals:
                    rental.status = 'OVERDUE'
                    rental.save(update_fields=['status', 'updated_at'])
                    updated_count += 1
            
            # 设置缓存，5分钟内不再更新
            cache.set(cache_key, timezone.now(), 300)  # 5分钟缓存
            
        except Exception as e:
            # 更新失败不影响正常流程
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'自动更新订单状态失败: {e}')
    
    def clean(self):
        """自定义验证方法"""
        super().clean()
        
        # 验证日期逻辑
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError('租赁结束日期不能早于开始日期')
            
            # 如果是更新，验证实际还车日期
            if self.actual_return_date:
                if self.actual_return_date < self.start_date:
                    raise ValidationError('实际还车日期不能早于租赁开始日期')
                if self.actual_return_date > date.today():
                    raise ValidationError('实际还车日期不能晚于今天')
    
    def save(self, *args, **kwargs):
        """保存时计算总金额和押金"""
        if not self.total_amount and self.start_date and self.end_date and self.vehicle:
            # 计算租赁天数
            rental_days = (self.end_date - self.start_date).days + 1
            self.total_amount = self.vehicle.daily_rate * rental_days
        
        # VIP用户不需要押金，普通用户需要押金
        if self.customer and self.customer.member_level == 'VIP':
            # VIP用户押金为0
            self.deposit = Decimal('0.00')
        elif self.deposit == Decimal('0.00') and self.vehicle:
            # 普通用户默认押金为日租金的10倍（可根据实际业务调整）
            self.deposit = self.vehicle.daily_rate * Decimal('10')
        
        # 如果设置了异地还车，但还车地点为空，则使用取车地点
        if self.is_cross_location_return and not self.return_location:
            self.return_location = self.pickup_location
        
        # 如果异地还车但费用为0，设置默认费用（可以根据业务规则调整）
        if self.is_cross_location_return and self.cross_location_fee == Decimal('0.00'):
            # 默认异地还车费用为日租金的50%（可根据实际业务调整）
            if self.vehicle:
                self.cross_location_fee = self.vehicle.daily_rate * Decimal('0.5')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.customer.name} - {self.vehicle.license_plate} ({self.start_date})"
    
    def __repr__(self):
        return f"<Rental: {self.customer.name} - {self.vehicle.license_plate}>"
    
    @property
    def rental_days(self):
        """计算租赁天数"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def calculate_order_total(self):
        """计算订单总额（基础租金 + 押金 + 异地费用 + 超时费用）"""
        base_amount = self.total_amount or Decimal('0.00')
        deposit_amount = self.deposit or Decimal('0.00')
        cross_location_fee = self.cross_location_fee or Decimal('0.00')
        overdue_fee = self.overdue_fee or Decimal('0.00')
        if not self.is_cross_location_return:
            cross_location_fee = Decimal('0.00')
        return base_amount + deposit_amount + cross_location_fee + overdue_fee
    
    def refresh_financials(self, save=True):
        """根据支付记录刷新累计支付/退款信息"""
        from accounts.models import Payment  # 避免循环导入
        paid_total = Payment.objects.filter(
            rental=self,
            status='PAID',
            transaction_type='CHARGE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refunded_total = Payment.objects.filter(
            rental=self,
            status='REFUNDED',
            transaction_type='REFUND'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        self.amount_paid = paid_total
        self.amount_refunded = refunded_total
        
        # 根据支付情况更新结算状态
        order_total = self.calculate_order_total()
        if self.status == 'COMPLETED' and order_total <= paid_total:
            self.settlement_status = 'SETTLED'
            if not self.settled_at:
                self.settled_at = timezone.now()
        elif paid_total > Decimal('0.00'):
            self.settlement_status = 'PARTIAL'
        else:
            self.settlement_status = 'UNSETTLED'
            self.settled_at = None
        
        if save:
            self.save(update_fields=[
                'amount_paid',
                'amount_refunded',
                'settlement_status',
                'settled_at',
                'updated_at'
            ])
    
    def refund_deposit(self, user=None):
        """
        退还押金
        如果订单有押金且未退还，创建退款记录
        返回：(是否已退款, 退款金额)
        """
        from accounts.models import Payment  # 避免循环导入
        from django.db.models import Sum
        
        deposit_amount = self.deposit or Decimal('0.00')
        if deposit_amount <= Decimal('0.00'):
            return False, Decimal('0.00')
        
        # 检查已退还的押金总额
        refunded_amount = Payment.objects.filter(
            rental=self,
            transaction_type='REFUND',
            status='REFUNDED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # 计算可退还金额（押金减去已退还金额）
        refundable = deposit_amount - refunded_amount
        
        if refundable <= Decimal('0.00'):
            return False, Decimal('0.00')
        
        # 获取退款用户
        refund_user = user
        if not refund_user:
            # 优先使用支付记录中的用户
            payment_user = Payment.objects.filter(
                rental=self,
                transaction_type='CHARGE',
                status='PAID'
            ).order_by('created_at').first()
            refund_user = payment_user.user if payment_user else None
            # 如果没有支付记录，使用客户关联的用户
            if not refund_user and self.customer and self.customer.user:
                refund_user = self.customer.user
        
        if not refund_user:
            return False, Decimal('0.00')
        
        # 创建退款记录
        Payment.objects.create(
            rental=self,
            user=refund_user,
            amount=refundable,
            payment_method='BANK',
            transaction_type='REFUND',
            status='REFUNDED',
            description='订单完成，押金自动退还',
            paid_at=timezone.now(),
            transaction_id=f'REF{int(timezone.now().timestamp())}'
        )
        
        # 刷新财务信息
        self.refresh_financials()
        
        return True, refundable
    
    @property
    def outstanding_amount(self):
        """计算仍需支付的金额（不考虑退款，用于判断是否欠费）"""
        order_total = self.calculate_order_total()
        remaining = order_total - self.amount_paid
        return remaining if remaining > Decimal('0.00') else Decimal('0.00')
