from django import forms
from django.core.exceptions import ValidationError
from .models import Vehicle


class VehicleForm(forms.ModelForm):
    """车辆表单"""
    
    class Meta:
        model = Vehicle
        fields = [
            'license_plate', 'brand', 'model', 'vehicle_type', 
            'color', 'seats', 'daily_rate', 'status'
        ]
        widgets = {
            'license_plate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入车牌号，如：京A12345',
                'maxlength': 20
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入汽车品牌，如：宝马、奔驰',
                'maxlength': 50
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入车型，如：X5、E级',
                'maxlength': 50
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('', '请选择车辆类型'),
                ('轿车', '轿车'),
                ('SUV', 'SUV'),
                ('MPV', 'MPV'),
                ('跑车', '跑车'),
                ('敞篷车', '敞篷车'),
                ('皮卡', '皮卡'),
                ('货车', '货车'),
                ('客车', '客车'),
            ]),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入车身颜色，如：黑色、白色',
                'maxlength': 20
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入座位数，如：5',
                'min': 2,
                'max': 50,
                'step': 1
            }),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入日租金，如：200.00',
                'min': 0.01,
                'step': 0.01
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }, choices=Vehicle.VEHICLE_STATUS_CHOICES)
        }
        labels = {
            'license_plate': '车牌号',
            'brand': '品牌',
            'model': '型号',
            'vehicle_type': '车辆类型',
            'color': '颜色',
            'seats': '座位数',
            'daily_rate': '日租金（元/天）',
            'status': '状态',
        }
        help_texts = {
            'license_plate': '车辆唯一标识，必须唯一',
            'brand': '汽车品牌，如：宝马、奔驰',
            'model': '车型，如：X5、E级',
            'vehicle_type': '车辆类型，如：轿车、SUV',
            'color': '车身颜色',
            'seats': '车辆座位数，范围2-50座',
            'daily_rate': '每日租金价格，必须为正数',
            'status': '当前车辆状态',
        }
    
    def clean_license_plate(self):
        """验证车牌号唯一性"""
        license_plate = self.cleaned_data['license_plate']
        
        # 检查是否已存在相同车牌号（除了当前编辑的车辆）
        if self.instance.pk:
            if Vehicle.objects.filter(license_plate=license_plate).exclude(pk=self.instance.pk).exists():
                raise ValidationError('该车牌号已存在')
        else:
            if Vehicle.objects.filter(license_plate=license_plate).exists():
                raise ValidationError('该车牌号已存在')
        
        return license_plate
    
    def clean_daily_rate(self):
        """验证日租金"""
        daily_rate = self.cleaned_data['daily_rate']
        
        if daily_rate <= 0:
            raise ValidationError('日租金必须为正数')
        
        if daily_rate > 10000:
            raise ValidationError('日租金不能超过10000元')
        
        return daily_rate
    
    def clean_brand(self):
        """标准化品牌名称"""
        brand = self.cleaned_data['brand']
        return brand.strip()
    
    def clean_model(self):
        """标准化型号名称"""
        model = self.cleaned_data['model']
        return model.strip()
    
    def clean_color(self):
        """标准化颜色名称"""
        color = self.cleaned_data['color']
        return color.strip()
    
    def clean_seats(self):
        """验证座位数"""
        seats = self.cleaned_data['seats']
        
        if seats < 2:
            raise ValidationError('座位数不能少于2座')
        
        if seats > 50:
            raise ValidationError('座位数不能超过50座')
        
        return seats
    
    def save(self, commit=True):
        """保存时清理数据"""
        instance = super().save(commit=False)
        
        # 清理空格
        instance.brand = instance.brand.strip()
        instance.model = instance.model.strip()
        instance.color = instance.color.strip()
        instance.license_plate = instance.license_plate.strip()
        
        if commit:
            instance.save()
        
        return instance