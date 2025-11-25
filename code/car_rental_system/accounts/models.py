from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from vehicles.models import Vehicle
from rentals.models import Rental


class UserProfile(models.Model):
    """用户扩展信息"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户'
    )
    phone = models.CharField(
        '手机号',
        max_length=20,
        blank=True,
        null=True,
        help_text='联系电话'
    )
    avatar = models.ImageField(
        '头像',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='用户头像'
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
        db_table = 'user_profiles'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
    
    def __str__(self):
        return f"{self.user.username} 的资料"


class Favorite(models.Model):
    """车辆收藏"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='用户'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='车辆'
    )
    created_at = models.DateTimeField(
        '收藏时间',
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'favorites'
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
        unique_together = ['user', 'vehicle']  # 防止重复收藏
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        models.Index(fields=['vehicle']),
        ]
    
    def __str__(self):
        return f"{self.user.username} 收藏了 {self.vehicle}"


class Review(models.Model):
    """订单评价"""
    RATING_CHOICES = [
        (1, '1星'),
        (2, '2星'),
        (3, '3星'),
        (4, '4星'),
        (5, '5星'),
    ]
    
    rental = models.OneToOneField(
        Rental,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='订单'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='用户'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='车辆'
    )
    rating = models.IntegerField(
        '评分',
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1-5星评分'
    )
    comment = models.TextField(
        '评价内容',
        max_length=1000,
        blank=True,
        null=True,
        help_text='评价详情'
    )
    created_at = models.DateTimeField(
        '评价时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        '更新时间',
        auto_now=True
    )
    
    class Meta:
        db_table = 'reviews'
        verbose_name = '评价'
        verbose_name_plural = '评价'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'rating']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} 对 {self.vehicle} 的评价 ({self.rating}星)"


class Payment(models.Model):
    """支付记录"""
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', '待支付'),
        ('PAID', '已支付'),
        ('FAILED', '支付失败'),
        ('REFUNDED', '已退款'),
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('CHARGE', '支付'),
        ('REFUND', '退款'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('ALIPAY', '支付宝'),
        ('WECHAT', '微信支付'),
        ('BANK', '银行卡'),
        ('CASH', '现金'),
    ]
    
    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='订单'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='用户'
    )
    amount = models.DecimalField(
        '支付金额',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='支付金额'
    )
    payment_method = models.CharField(
        '支付方式',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='ALIPAY',
        help_text='支付方式'
    )
    transaction_type = models.CharField(
        '交易类型',
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='CHARGE',
        help_text='区分支付或退款'
    )
    status = models.CharField(
        '支付状态',
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        help_text='支付状态'
    )
    description = models.CharField(
        '备注',
        max_length=255,
        blank=True,
        null=True,
        help_text='支付或退款说明'
    )
    transaction_id = models.CharField(
        '交易号',
        max_length=100,
        blank=True,
        null=True,
        help_text='第三方交易号'
    )
    paid_at = models.DateTimeField(
        '支付时间',
        blank=True,
        null=True,
        help_text='实际支付时间'
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
        db_table = 'payments'
        verbose_name = '支付记录'
        verbose_name_plural = '支付记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['rental']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - ¥{self.amount} ({self.get_status_display()})"


class Notification(models.Model):
    """消息通知"""
    NOTIFICATION_TYPE_CHOICES = [
        ('ORDER_CREATED', '订单创建'),
        ('ORDER_CONFIRMED', '订单确认'),
        ('ORDER_CANCELLED', '订单取消'),
        ('ORDER_COMPLETED', '订单完成'),
        ('PAYMENT_SUCCESS', '支付成功'),
        ('PAYMENT_FAILED', '支付失败'),
        ('SYSTEM', '系统通知'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='用户'
    )
    notification_type = models.CharField(
        '通知类型',
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='SYSTEM',
        help_text='通知类型'
    )
    title = models.CharField(
        '标题',
        max_length=200,
        help_text='通知标题'
    )
    content = models.TextField(
        '内容',
        max_length=1000,
        help_text='通知内容'
    )
    is_read = models.BooleanField(
        '已读',
        default=False,
        help_text='是否已读'
    )
    related_rental = models.ForeignKey(
        Rental,
        on_delete=models.SET_NULL,
        related_name='notifications',
        blank=True,
        null=True,
        verbose_name='关联订单'
    )
    created_at = models.DateTimeField(
        '创建时间',
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = '消息通知'
        verbose_name_plural = '消息通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
