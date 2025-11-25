"""
测试订单和车辆状态自动更新功能
创建过期订单测试数据并验证自动更新效果
"""

import os
import django
from datetime import date, timedelta

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental


def create_test_data():
    """创建测试数据"""
    print("\n" + "="*60)
    print("正在创建测试数据...")
    print("="*60)
    
    # 创建测试客户(如果不存在)
    customer1, created = Customer.objects.get_or_create(
        phone='13800138001',
        defaults={
            'name': '测试客户A',
            'email': 'testA@example.com',
            'address': '测试地址A'
        }
    )
    if created:
        print(f"✓ 创建客户: {customer1.name}")
    else:
        print(f"✓ 使用已存在客户: {customer1.name}")
    
    customer2, created = Customer.objects.get_or_create(
        phone='13800138002',
        defaults={
            'name': '测试客户B',
            'email': 'testB@example.com',
            'address': '测试地址B'
        }
    )
    if created:
        print(f"✓ 创建客户: {customer2.name}")
    else:
        print(f"✓ 使用已存在客户: {customer2.name}")
    
    # 创建测试车辆(如果不存在)
    vehicle1, created = Vehicle.objects.get_or_create(
        license_plate='京TEST01',
        defaults={
            'brand': '测试品牌',
            'model': '测试型号A',
            'vehicle_type': '轿车',
            'color': '黑色',
            'daily_rate': 200.00,
            'status': 'RENTED'
        }
    )
    if created:
        print(f"✓ 创建车辆: {vehicle1.license_plate}")
    else:
        vehicle1.status = 'RENTED'
        vehicle1.save()
        print(f"✓ 使用已存在车辆: {vehicle1.license_plate} (状态已更新为已租)")
    
    vehicle2, created = Vehicle.objects.get_or_create(
        license_plate='京TEST02',
        defaults={
            'brand': '测试品牌',
            'model': '测试型号B',
            'vehicle_type': 'SUV',
            'color': '白色',
            'daily_rate': 300.00,
            'status': 'RENTED'
        }
    )
    if created:
        print(f"✓ 创建车辆: {vehicle2.license_plate}")
    else:
        vehicle2.status = 'RENTED'
        vehicle2.save()
        print(f"✓ 使用已存在车辆: {vehicle2.license_plate} (状态已更新为已租)")
    
    # 创建过期订单
    today = date.today()
    
    # 订单1: 5天前结束,应该被更新
    rental1, created = Rental.objects.get_or_create(
        customer=customer1,
        vehicle=vehicle1,
        start_date=today - timedelta(days=10),
        end_date=today - timedelta(days=5),
        defaults={
            'total_amount': 1000.00,
            'status': 'ONGOING',
            'notes': '测试过期订单1'
        }
    )
    if not created and rental1.status != 'ONGOING':
        rental1.status = 'ONGOING'
        rental1.save()
    print(f"✓ 创建订单1: {rental1.customer.name} - {rental1.vehicle.license_plate} "
          f"({rental1.start_date} ~ {rental1.end_date}) - 状态:{rental1.get_status_display()}")
    
    # 订单2: 1天前结束,应该被更新
    rental2, created = Rental.objects.get_or_create(
        customer=customer2,
        vehicle=vehicle2,
        start_date=today - timedelta(days=3),
        end_date=today - timedelta(days=1),
        defaults={
            'total_amount': 600.00,
            'status': 'ONGOING',
            'notes': '测试过期订单2'
        }
    )
    if not created and rental2.status != 'ONGOING':
        rental2.status = 'ONGOING'
        rental2.save()
    print(f"✓ 创建订单2: {rental2.customer.name} - {rental2.vehicle.license_plate} "
          f"({rental2.start_date} ~ {rental2.end_date}) - 状态:{rental2.get_status_display()}")
    
    # 订单3: 当天结束,不应该被更新
    rental3, created = Rental.objects.get_or_create(
        customer=customer1,
        vehicle=vehicle1,
        start_date=today - timedelta(days=2),
        end_date=today,
        defaults={
            'total_amount': 400.00,
            'status': 'ONGOING',
            'notes': '测试当天结束订单'
        }
    )
    if not created and rental3.status != 'ONGOING':
        rental3.status = 'ONGOING'
        rental3.save()
    print(f"✓ 创建订单3: {rental3.customer.name} - {rental3.vehicle.license_plate} "
          f"({rental3.start_date} ~ {rental3.end_date}) - 状态:{rental3.get_status_display()}")
    
    print("\n" + "="*60)
    print("测试数据创建完成!")
    print("="*60)
    
    return rental1, rental2, rental3, vehicle1, vehicle2


def check_status():
    """检查当前状态"""
    print("\n" + "="*60)
    print("检查当前数据状态...")
    print("="*60)
    
    today = date.today()
    print(f"当前日期: {today}\n")
    
    # 检查过期的进行中订单
    expired_rentals = Rental.objects.filter(
        status='ONGOING',
        end_date__lt=today
    )
    
    print(f"过期的进行中订单数量: {expired_rentals.count()}")
    for rental in expired_rentals:
        print(f"  - 订单 #{rental.id}: {rental.customer.name} - {rental.vehicle.license_plate} "
              f"({rental.start_date} ~ {rental.end_date})")
    
    # 检查已租的车辆
    rented_vehicles = Vehicle.objects.filter(status='RENTED')
    print(f"\n已租车辆数量: {rented_vehicles.count()}")
    for vehicle in rented_vehicles:
        ongoing_count = Rental.objects.filter(vehicle=vehicle, status='ONGOING').count()
        print(f"  - {vehicle.license_plate} ({vehicle.brand} {vehicle.model}) - "
              f"进行中订单: {ongoing_count}")
    
    print("="*60)


if __name__ == '__main__':
    print("\n开始测试订单和车辆状态自动更新功能")
    
    # 创建测试数据
    rental1, rental2, rental3, vehicle1, vehicle2 = create_test_data()
    
    # 检查更新前状态
    print("\n【更新前状态】")
    check_status()
    
    # 提示用户执行更新命令
    print("\n" + "="*60)
    print("请执行以下命令来更新过期订单:")
    print("python manage.py update_expired_rentals")
    print("="*60)
    
    # 等待用户执行命令后,再次检查状态
    input("\n按回车键查看更新后的状态...")
    
    print("\n【更新后状态】")
    check_status()
    
    # 验证结果
    print("\n" + "="*60)
    print("验证结果:")
    print("="*60)
    
    rental1.refresh_from_db()
    rental2.refresh_from_db()
    rental3.refresh_from_db()
    vehicle1.refresh_from_db()
    vehicle2.refresh_from_db()
    
    print(f"✓ 订单1状态: {rental1.get_status_display()} (预期: 已完成)")
    print(f"✓ 订单2状态: {rental2.get_status_display()} (预期: 已完成)")
    print(f"✓ 订单3状态: {rental3.get_status_display()} (预期: 进行中)")
    print(f"✓ 车辆1状态: {vehicle1.get_status_display()} (预期: 已租 - 因为订单3仍在进行中)")
    print(f"✓ 车辆2状态: {vehicle2.get_status_display()} (预期: 可用)")
    
    print("\n测试完成!")
