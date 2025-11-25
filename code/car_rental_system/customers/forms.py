from django import forms
from django.core.exceptions import ValidationError
from .models import Customer


class CustomerForm(forms.ModelForm):
    """客户信息表单"""
    
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'id_card', 'license_number', 'license_type', 'member_level']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入客户姓名'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入手机号码'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入邮箱地址（可选）'
            }),
            'id_card': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入身份证号码'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入驾驶证号码'
            }),
            'license_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'member_level': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'name': '客户姓名',
            'phone': '联系电话',
            'email': '电子邮箱',
            'id_card': '身份证号',
            'license_number': '驾驶证号',
            'license_type': '驾照类型',
            'member_level': '会员等级',
        }
        help_texts = {
            'name': '客户真实姓名',
            'phone': '11位手机号码',
            'email': '可选，提供邮箱以便联系',
            'id_card': '18位身份证号码，必须唯一',
            'license_number': '驾驶证号码，必须唯一',
            'license_type': '驾驶证准驾车型',
            'member_level': '客户会员等级',
        }
    
    def clean_phone(self):
        """验证手机号格式和唯一性"""
        phone = self.cleaned_data['phone']
        
        # 格式验证
        import re
        if not re.match(r'^1[3-9]\d{9}$', phone):
            raise ValidationError('请输入有效的11位手机号码')
        
        # 唯一性验证（排除当前编辑的记录）
        instance = getattr(self, 'instance', None)
        if instance:
            existing = Customer.objects.filter(phone=phone).exclude(pk=instance.pk)
        else:
            existing = Customer.objects.filter(phone=phone)
        
        if existing.exists():
            raise ValidationError('该手机号码已被注册')
        
        return phone
    
    def clean_id_card(self):
        """验证身份证号格式和唯一性"""
        id_card = self.cleaned_data['id_card']
        
        # 格式验证
        import re
        if not re.match(r'^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$', id_card):
            raise ValidationError('请输入有效的18位身份证号码')
        
        # 唯一性验证（排除当前编辑的记录）
        instance = getattr(self, 'instance', None)
        if instance:
            existing = Customer.objects.filter(id_card=id_card).exclude(pk=instance.pk)
        else:
            existing = Customer.objects.filter(id_card=id_card)
        
        if existing.exists():
            raise ValidationError('该身份证号码已被注册')
        
        return id_card
    
    def clean_license_number(self):
        """验证驾驶证号唯一性"""
        license_number = self.cleaned_data['license_number']
        
        # 唯一性验证（排除当前编辑的记录）
        instance = getattr(self, 'instance', None)
        if instance:
            existing = Customer.objects.filter(license_number=license_number).exclude(pk=instance.pk)
        else:
            existing = Customer.objects.filter(license_number=license_number)
        
        if existing.exists():
            raise ValidationError('该驾驶证号码已被注册')
        
        return license_number


class CustomerSearchForm(forms.Form):
    """客户搜索表单"""
    search = forms.CharField(
        required=False,
        label='搜索',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '按姓名或手机号搜索'
        })
    )
    member_level = forms.ChoiceField(
        required=False,
        label='会员等级',
        choices=[('', '全部')] + Customer.MEMBER_LEVEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class MembershipUpdateForm(forms.ModelForm):
    """会员等级更新表单"""
    
    class Meta:
        model = Customer
        fields = ['member_level']
        widgets = {
            'member_level': forms.Select(attrs={
                'class': 'form-select',
                'id': 'membership-select'
            })
        }
        labels = {
            'member_level': '会员等级'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置所有字段为必填
        for field in self.fields.values():
            field.required = True