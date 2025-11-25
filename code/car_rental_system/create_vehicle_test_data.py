#!/usr/bin/env python
"""
为车辆管理功能创建测试数据
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from vehicles.models import Vehicle

def create_test_vehicles():
    """创建测试车辆数据"""
    
    # 清空现有数据
    Vehicle.objects.all().delete()
    
    # 创建测试车辆
    vehicles_data = [
        {
            'license_plate': '京A12345',
            'brand': '宝马',
            'model': 'X5',
            'vehicle_type': 'SUV',
            'color': '黑色',
            'daily_rate': 500.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京B67890',
            'brand': '奔驰',
            'model': 'E级',
            'vehicle_type': '轿车',
            'color': '白色',
            'daily_rate': 450.00,
            'status': 'RENTED',
        },
        {
            'license_plate': '京C11111',
            'brand': '奥迪',
            'model': 'A4',
            'vehicle_type': '轿车',
            'color': '银色',
            'daily_rate': 380.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京D22222',
            'brand': '大众',
            'model': '帕萨特',
            'vehicle_type': '轿车',
            'color': '灰色',
            'daily_rate': 280.00,
            'status': 'MAINTENANCE',
        },
        {
            'license_plate': '京E33333',
            'brand': '丰田',
            'model': '凯美瑞',
            'vehicle_type': '轿车',
            'color': '白色',
            'daily_rate': 320.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京F44444',
            'brand': '本田',
            'model': '雅阁',
            'vehicle_type': '轿车',
            'color': '黑色',
            'daily_rate': 300.00,
            'status': 'RENTED',
        },
        {
            'license_plate': '京G55555',
            'brand': '福特',
            'model': '锐界',
            'vehicle_type': 'SUV',
            'color': '蓝色',
            'daily_rate': 420.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京H66666',
            'brand': '通用',
            'model': 'GL8',
            'vehicle_type': 'MPV',
            'color': '灰色',
            'daily_rate': 350.00,
            'status': 'MAINTENANCE',
        },
        {
            'license_plate': '京J77777',
            'brand': '特斯拉',
            'model': 'Model 3',
            'vehicle_type': '轿车',
            'color': '红色',
            'daily_rate': 600.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京K88888',
            'brand': '比亚迪',
            'model': '汉',
            'vehicle_type': '轿车',
            'color': '白色',
            'daily_rate': 250.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京L99999',
            'brand': '小鹏',
            'model': 'P7',
            'vehicle_type': '轿车',
            'color': '蓝色',
            'daily_rate': 280.00,
            'status': 'AVAILABLE',
        },
        {
            'license_plate': '京M00000',
            'brand': '理想',
            'model': 'ONE',
            'vehicle_type': 'SUV',
            'color': '黑色',
            'daily_rate': 480.00,
            'status': 'RENTED',
        },
    ]
    
    created_count = 0
    for vehicle_data in vehicles_data:
        try:
            vehicle = Vehicle.objects.create(**vehicle_data)
            created_count += 1
            print(f"✓ 创建车辆: {vehicle.license_plate} - {vehicle.brand} {vehicle.model}")
        except Exception as e:
            print(f"✗ 创建车辆失败: {vehicle_data['license_plate']} - {e}")
    
    print(f"\n成功创建 {created_count} 辆测试车辆")
    
    # 打印统计信息
    total = Vehicle.objects.count()
    available = Vehicle.objects.filter(status='AVAILABLE').count()
    rented = Vehicle.objects.filter(status='RENTED').count()
    maintenance = Vehicle.objects.filter(status='MAINTENANCE').count()
    
    print(f"\n=== 车辆统计 ===")
    print(f"总车辆数: {total}")
    print(f"可用: {available}")
    print(f"已租: {rented}")
    print(f"维修中: {maintenance}")

if __name__ == '__main__':
    create_test_vehicles()