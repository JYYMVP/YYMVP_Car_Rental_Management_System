from django import forms
from django.core.exceptions import ValidationError
from .models import Rental
from customers.models import Customer
from vehicles.models import Vehicle
from datetime import date
from decimal import Decimal


class RentalForm(forms.ModelForm):
    """租赁订单表单"""
    
    class Meta:
        model = Rental
        fields = [
            'customer', 'vehicle', 'start_date', 'end_date', 
            'deposit', 'pickup_location', 'is_cross_location_return', 
            'return_location', 'cross_location_fee', 'status', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'vehicle': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'deposit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入押金金额，如：1000.00',
                'min': 0,
                'step': 0.01
            }),
            'pickup_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入取车地点，如：北京门店',
                'maxlength': 200
            }),
            'is_cross_location_return': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_cross_location_return'
            }),
            'return_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入还车地点，如：上海门店',
                'maxlength': 200
            }),
            'cross_location_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '异地还车费用（自动计算或手动输入）',
                'min': 0,
                'step': 0.01
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '订单备注信息...'
            }),
        }
        labels = {
            'customer': '客户',
            'vehicle': '车辆',
            'start_date': '开始日期',
            'end_date': '结束日期',
            'deposit': '押金（元）',
            'pickup_location': '取车地点',
            'is_cross_location_return': '是否异地还车',
            'return_location': '还车地点',
            'cross_location_fee': '异地还车费用（元）',
            'status': '订单状态',
            'notes': '备注',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置默认值
        if not self.instance.pk:  # 创建新订单时
            self.fields['start_date'].initial = date.today()
            self.fields['end_date'].initial = date.today()
            self.fields['status'].initial = 'PENDING'
            self.fields['pickup_location'].initial = '门店'
            self.fields['deposit'].initial = Decimal('0.00')
            self.fields['is_cross_location_return'].initial = False
            self.fields['cross_location_fee'].initial = Decimal('0.00')
        
        # 过滤出可用的客户和车辆
        self.fields['customer'].queryset = Customer.objects.all().order_by('name')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            status='AVAILABLE'
        ).order_by('license_plate')
        
        # 如果未选择异地还车，还车地点和费用字段可以为空
        if not self.instance.pk or not self.instance.is_cross_location_return:
            self.fields['return_location'].required = False
            self.fields['cross_location_fee'].required = False

        # 押金和异地还车费用自动计算，对用户隐藏输入框
        self.fields['deposit'].required = False
        self.fields['deposit'].widget = forms.HiddenInput()
        self.fields['cross_location_fee'].required = False
        self.fields['cross_location_fee'].widget = forms.HiddenInput()
    
    def clean_customer(self):
        """验证客户"""
        customer = self.cleaned_data.get('customer')
        if not customer:
            raise ValidationError('请选择一个客户')
        return customer
    
    def clean_vehicle(self):
        """验证车辆"""
        vehicle = self.cleaned_data.get('vehicle')
        if not vehicle:
            raise ValidationError('请选择一辆车辆')
        
        # 检查车辆是否可用（除了更新当前订单的情况）
        if self.instance.pk:
            # 如果是更新订单，排除当前订单中的车辆
            if not vehicle.rentals.filter(pk=self.instance.pk).exists():
                if vehicle.status != 'AVAILABLE':
                    raise ValidationError('该车辆当前不可用')
        else:
            # 如果是新订单，检查车辆状态
            if vehicle.status != 'AVAILABLE':
                raise ValidationError('该车辆当前不可用')
        
        return vehicle
    
    def clean_start_date(self):
        """验证开始日期"""
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            raise ValidationError('请选择开始日期')
        
        # 开始日期不能早于今天
        if start_date < date.today():
            raise ValidationError('开始日期不能早于今天')
        
        return start_date
    
    def clean_end_date(self):
        """验证结束日期"""
        end_date = self.cleaned_data.get('end_date')
        if not end_date:
            raise ValidationError('请选择结束日期')
        
        return end_date
    
    def clean_deposit(self):
        """验证押金"""
        deposit = self.cleaned_data.get('deposit')
        # 如果为 None 或空，设置为默认值 0.00
        if deposit is None or deposit == '':
            return Decimal('0.00')
        if deposit < 0:
            raise ValidationError('押金不能为负数')
        return deposit
    
    def clean_cross_location_fee(self):
        """验证异地还车费用"""
        cross_location_fee = self.cleaned_data.get('cross_location_fee')
        # 如果为 None 或空，设置为默认值 0.00
        if cross_location_fee is None or cross_location_fee == '':
            return Decimal('0.00')
        if cross_location_fee < 0:
            raise ValidationError('异地还车费用不能为负数')
        return cross_location_fee
    
    def clean(self):
        """跨字段验证"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        vehicle = cleaned_data.get('vehicle')
        customer = cleaned_data.get('customer')
        is_cross_location_return = cleaned_data.get('is_cross_location_return', False)
        return_location = cleaned_data.get('return_location', '')
        pickup_location = cleaned_data.get('pickup_location', '')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('租赁结束日期不能早于开始日期')
        
        # 验证异地还车逻辑
        if is_cross_location_return:
            if not return_location:
                raise ValidationError('选择异地还车时，必须填写还车地点')
            if return_location == pickup_location:
                raise ValidationError('异地还车时，还车地点不能与取车地点相同')
        else:
            # 如果不是异地还车，清空还车地点和费用
            cleaned_data['return_location'] = None
            cleaned_data['cross_location_fee'] = Decimal('0.00')
        
        # 允许同一客户在同一时间段有多个订单（例如：客户可能同时租用多辆车）
        # 因此不检查客户时间冲突
        
        # 检查车辆时间冲突（同一辆车在同一时间段只能租给一个客户）
        if vehicle and start_date and end_date:
            conflicts = Rental.objects.filter(
                vehicle=vehicle,
                status__in=['PENDING', 'ONGOING', 'OVERDUE']  # 预订中、进行中或已超时未归还的订单
            ).exclude(pk=self.instance.pk)
            
            for rental in conflicts:
                # 检查时间是否重叠
                if not (end_date < rental.start_date or start_date > rental.end_date):
                    raise ValidationError(
                        f'车辆 {vehicle.license_plate} 在 {rental.start_date} 至 {rental.end_date} 时间段已被租赁'
                    )
        
        return cleaned_data


class RentalStatusForm(forms.ModelForm):
    """租赁状态更新表单"""
    
    class Meta:
        model = Rental
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
    
    def clean_status(self):
        """验证状态转换"""
        new_status = self.cleaned_data.get('status')
        current_status = self.instance.status
        
        # 状态转换规则
        valid_transitions = {
            'PENDING': ['ONGOING', 'CANCELLED'],  # 预订中 → 进行中/已取消
            'ONGOING': ['COMPLETED', 'CANCELLED'],  # 进行中 → 已完成/已取消
            'COMPLETED': [],  # 已完成不能转换
            'CANCELLED': [],  # 已取消不能转换
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f'不能从状态 "{dict(Rental.RENTAL_STATUS_CHOICES)[current_status]}" '
                f'转换为 "{dict(Rental.RENTAL_STATUS_CHOICES)[new_status]}"'
            )
        
        return new_status


class ReturnForm(forms.Form):
    """车辆归还表单"""
    actual_return_date = forms.DateField(
        label='实际还车日期',
        initial=date.today(),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True
        })
    )
    actual_return_location = forms.CharField(
        label='实际还车门店',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入实际还车门店，如：北京门店',
            'maxlength': 200
        })
    )
    
    def clean_actual_return_date(self):
        """验证还车日期"""
        actual_return_date = self.cleaned_data.get('actual_return_date')
        if not actual_return_date:
            raise ValidationError('请选择实际还车日期')
        
        if actual_return_date > date.today():
            raise ValidationError('还车日期不能晚于今天')
        
        return actual_return_date
    
    def clean_actual_return_location(self):
        """验证还车门店"""
        actual_return_location = self.cleaned_data.get('actual_return_location', '').strip()
        if not actual_return_location:
            return None
        return actual_return_location


class CancelForm(forms.Form):
    """取消订单表单"""
    cancel_reason = forms.CharField(
        label='取消原因',
        max_length=200,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入取消订单的原因...',
            'required': True
        })
    )