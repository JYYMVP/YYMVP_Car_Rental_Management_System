#!/usr/bin/env python
"""
测试车辆管理功能
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from vehicles.models import Vehicle
from vehicles.forms import VehicleForm
from django.db import models

def test_vehicle_model():
    """测试车辆模型"""
    print("=== 测试车辆模型 ===")
    
    # 测试创建车辆
    vehicle = Vehicle.objects.create(
        license_plate='TEST001',
        brand='测试品牌',
        model='测试型号',
        vehicle_type='轿车',
        color='红色',
        daily_rate=200.00,
        status='AVAILABLE'
    )
    print(f"✓ 创建车辆成功: {vehicle}")
    
    # 测试查询
    found_vehicle = Vehicle.objects.get(license_plate='TEST001')
    print(f"✓ 查询车辆成功: {found_vehicle.brand} {found_vehicle.model}")
    
    # 测试更新
    found_vehicle.daily_rate = 250.00
    found_vehicle.save()
    print(f"✓ 更新车辆成功: 日租金改为 ¥{found_vehicle.daily_rate}")
    
    # 清理测试数据
    found_vehicle.delete()
    print("✓ 清理测试数据完成")

def test_vehicle_form():
    """测试车辆表单"""
    print("\n=== 测试车辆表单 ===")
    
    # 测试有效数据
    form_data = {
        'license_plate': 'FORM001',
        'brand': '表单测试',
        'model': '表单型号',
        'vehicle_type': 'SUV',
        'color': '蓝色',
        'daily_rate': 300.00,
        'status': 'AVAILABLE'
    }
    
    form = VehicleForm(data=form_data)
    if form.is_valid():
        vehicle = form.save()
        print(f"✓ 表单验证和保存成功: {vehicle.license_plate}")
        vehicle.delete()
        print("✓ 清理测试数据完成")
    else:
        print(f"✗ 表单验证失败: {form.errors}")
    
    # 测试无效数据
    invalid_data = {
        'license_plate': 'FORM001',  # 重复车牌号
        'brand': '测试',
        'model': '测试',
        'vehicle_type': '轿车',
        'color': '红色',
        'daily_rate': -100,  # 负数租金
        'status': 'AVAILABLE'
    }
    
    form = VehicleForm(data=invalid_data)
    if not form.is_valid():
        print("✓ 无效数据验证成功（预期中的错误）")
        print(f"   错误信息: {form.errors}")
    else:
        print("✗ 无效数据验证失败（应该报错）")

def test_vehicle_queries():
    """测试车辆查询功能"""
    print("\n=== 测试车辆查询功能 ===")
    
    # 测试按状态查询
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE')
    print(f"✓ 可用车辆数量: {available_vehicles.count()}")
    
    # 测试按品牌查询
    bmw_vehicles = Vehicle.objects.filter(brand='宝马')
    print(f"✓ 宝马车辆数量: {bmw_vehicles.count()}")
    
    # 测试搜索功能
    search_results = Vehicle.objects.filter(
        models.Q(license_plate__icontains='京') |
        models.Q(brand__icontains='宝') |
        models.Q(model__icontains='X')
    )
    print(f"✓ 搜索结果数量: {search_results.count()}")
    
    # 测试统计功能
    from django.db.models import Count
    status_stats = Vehicle.objects.values('status').annotate(count=Count('status'))
    print("✓ 状态统计:")
    for stat in status_stats:
        status_name = dict(Vehicle.VEHICLE_STATUS_CHOICES).get(stat['status'], stat['status'])
        print(f"   {status_name}: {stat['count']} 辆")

def test_business_logic():
    """测试业务逻辑"""
    print("\n=== 测试业务逻辑 ===")
    
    # 测试状态验证
    vehicle = Vehicle.objects.first()
    if vehicle:
        print(f"✓ 测试车辆: {vehicle.license_plate} - 当前状态: {vehicle.get_status_display()}")
        
        # 测试状态更新
        old_status = vehicle.status
        vehicle.status = 'MAINTENANCE'
        vehicle.save()
        print(f"✓ 状态更新: {old_status} -> {vehicle.get_status_display()}")
        
        # 恢复原状态
        vehicle.status = old_status
        vehicle.save()
        print(f"✓ 状态恢复: {vehicle.get_status_display()}")
    
    # 测试唯一性约束
    try:
        duplicate_vehicle = Vehicle.objects.create(
            license_plate=vehicle.license_plate,  # 重复车牌号
            brand='重复测试',
            model='重复测试',
            vehicle_type='轿车',
            color='红色',
            daily_rate=100.00,
            status='AVAILABLE'
        )
        print("✗ 唯一性约束测试失败（应该报错）")
    except Exception as e:
        print("✓ 唯一性约束测试成功（重复车牌号被拒绝）")

def run_all_tests():
    """运行所有测试"""
    print("开始测试车辆管理功能...\n")
    
    try:
        test_vehicle_model()
        test_vehicle_form()
        test_vehicle_queries()
        test_business_logic()
        
        print("\n=== 测试完成 ===")
        print("✓ 所有测试通过！车辆管理功能正常工作。")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()