#!/usr/bin/env python
"""
创建租车管理系统测试数据的脚本
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from vehicles.models import Vehicle
from customers.models import Customer
from rentals.models import Rental


def create_test_data():
    """创建测试数据"""
    print("开始创建测试数据...")
    
    # 清理现有数据
    print("清理现有数据...")
    Rental.objects.all().delete()
    Vehicle.objects.all().delete()
    Customer.objects.all().delete()
    
    # 创建车辆数据
    print("创建车辆数据...")
    vehicles_data = [
        {
            'license_plate': '京A12345',
            'brand': '大众',
            'model': '帕萨特',
            'vehicle_type': '轿车',
            'color': '黑色',
            'daily_rate': Decimal('280.00'),
            'status': 'AVAILABLE'
        },
        {
            'license_plate': '京B67890',
            'brand': '丰田',
            'model': '凯美瑞',
            'vehicle_type': '轿车',
            'color': '白色',
            'daily_rate': Decimal('320.00'),
            'status': 'AVAILABLE'
        },
        {
            'license_plate': '京C11111',
            'brand': '本田',
            'model': 'CR-V',
            'vehicle_type': 'SUV',
            'color': '银色',
            'daily_rate': Decimal('450.00'),
            'status': 'AVAILABLE'
        },
        {
            'license_plate': '京D22222',
            'brand': '奔驰',
            'model': 'E级',
            'vehicle_type': '轿车',
            'color': '黑色',
            'daily_rate': Decimal('680.00'),
            'status': 'AVAILABLE'
        },
    ]
    
    vehicles = []
    for vehicle_data in vehicles_data:
        vehicle = Vehicle.objects.create(**vehicle_data)
        vehicles.append(vehicle)
        print(f"  创建车辆: {vehicle}")
    
    # 创建客户数据
    print("\n创建客户数据...")
    customers_data = [
        {
            'name': '张三',
            'phone': '13812345678',
            'email': 'zhangsan@example.com',
            'id_card': '110101199001011234',
            'license_number': '110101123456789012',
            'license_type': 'C',
            'member_level': 'NORMAL'
        },
        {
            'name': '李四',
            'phone': '13987654321',
            'email': 'lisi@example.com',
            'id_card': '110101199002021234',
            'license_number': '110101123456789013',
            'license_type': 'B',
            'member_level': 'VIP'
        },
        {
            'name': '王五',
            'phone': '13712345678',
            'email': 'wangwu@example.com',
            'id_card': '110101199003031234',
            'license_number': '110101123456789014',
            'license_type': 'A',
            'member_level': 'NORMAL'
        },
        {
            'name': '赵六',
            'phone': '13698765432',
            'email': 'zhaoliu@example.com',
            'id_card': '110101199004041234',
            'license_number': '110101123456789015',
            'license_type': 'C',
            'member_level': 'VIP'
        },
    ]
    
    customers = []
    for customer_data in customers_data:
        customer = Customer.objects.create(**customer_data)
        customers.append(customer)
        print(f"  创建客户: {customer}")
    
    # 创建租赁订单数据
    print("\n创建租赁订单数据...")
    rental_data = [
        {
            'customer': customers[0],  # 张三
            'vehicle': vehicles[0],    # 京A12345 大众帕萨特
            'start_date': date.today() - timedelta(days=5),
            'end_date': date.today() - timedelta(days=2),
            'actual_return_date': date.today() - timedelta(days=2),
            'status': 'COMPLETED',
            'notes': '按时还车，无任何问题'
        },
        {
            'customer': customers[1],  # 李四
            'vehicle': vehicles[1],    # 京B67890 丰田凯美瑞
            'start_date': date.today() - timedelta(days=2),
            'end_date': date.today() + timedelta(days=2),
            'status': 'ONGOING',
            'notes': '正在租赁中'
        },
        {
            'customer': customers[2],  # 王五
            'vehicle': vehicles[2],    # 京C11111 本田CR-V
            'start_date': date.today() + timedelta(days=1),
            'end_date': date.today() + timedelta(days=4),
            'status': 'PENDING',
            'notes': '预订3天'
        },
    ]
    
    rentals = []
    for rental_data in rental_data:
        rental = Rental.objects.create(**rental_data)
        rentals.append(rental)
        print(f"  创建租赁订单: {rental}")
    
    print("\n=== 测试数据创建完成 ===")
    print(f"创建了 {len(vehicles)} 辆车")
    print(f"创建了 {len(customers)} 个客户")
    print(f"创建了 {len(rentals)} 个租赁订单")


def test_relationships():
    """测试模型关系和查询"""
    print("\n=== 测试模型关系和查询 ===")
    
    # 测试车辆查询
    print("\n1. 可用车辆列表:")
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE')
    for vehicle in available_vehicles:
        print(f"  {vehicle}")
    
    # 测试客户查询
    print("\n2. VIP客户列表:")
    vip_customers = Customer.objects.filter(member_level='VIP')
    for customer in vip_customers:
        print(f"  {customer}")
    
    # 测试租赁订单查询
    print("\n3. 进行中的订单:")
    ongoing_rentals = Rental.objects.filter(status='ONGOING')
    for rental in ongoing_rentals:
        print(f"  {rental} - 客户: {rental.customer.name} - 车辆: {rental.vehicle.license_plate}")
    
    # 测试关联查询
    print("\n4. 客户租赁历史:")
    for customer in Customer.objects.all()[:2]:  # 只显示前2个客户
        print(f"  {customer.name} 的租赁历史:")
        for rental in customer.rentals.all():
            print(f"    - {rental.vehicle.license_plate} ({rental.start_date} 到 {rental.end_date})")
    
    # 测试聚合查询
    print("\n5. 统计数据:")
    total_vehicles = Vehicle.objects.count()
    total_customers = Customer.objects.count()
    total_rentals = Rental.objects.count()
    total_revenue = Rental.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    print(f"  总车辆数: {total_vehicles}")
    print(f"  总客户数: {total_customers}")
    print(f"  总订单数: {total_rentals}")
    print(f"  总收入: {total_revenue} 元")


if __name__ == '__main__':
    try:
        create_test_data()
        test_relationships()
        print("\n✅ 所有测试完成！")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()