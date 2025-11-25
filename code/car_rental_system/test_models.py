#!/usr/bin/env python
"""
Django Shell 测试脚本
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from vehicles.models import Vehicle
from customers.models import Customer
from rentals.models import Rental
from decimal import Decimal
from datetime import date

print('=== Django Shell 测试 ===')

# 测试外键关系
print('\n1. 测试外键关系:')
for rental in Rental.objects.all()[:2]:
    print(f'  订单: {rental}')
    print(f'    客户: {rental.customer.name} - {rental.customer.phone}')
    print(f'    车辆: {rental.vehicle.brand} {rental.vehicle.model} - {rental.vehicle.license_plate}')
    print(f'    租赁天数: {rental.rental_days}天')
    print(f'    总金额: {rental.total_amount}元')
    print()

# 测试反向关系
print('2. 测试反向关系:')
for customer in Customer.objects.all()[:2]:
    print(f'  客户 {customer.name} 的租赁记录:')
    for rental in customer.rentals.all():
        print(f'    - {rental.vehicle.license_plate} ({rental.status})')
    print()

# 测试车辆的反向关系
print('3. 测试车辆租赁情况:')
for vehicle in Vehicle.objects.all()[:2]:
    print(f'  车辆 {vehicle.license_plate} 的租赁记录:')
    for rental in vehicle.rentals.all():
        print(f'    - {rental.customer.name} ({rental.status})')
    print()

# 测试复杂查询
print('4. 复杂查询测试:')
# 查询VIP客户的所有订单
vip_rentals = Rental.objects.filter(customer__member_level='VIP')
print(f'  VIP客户的订单数量: {vip_rentals.count()}')

# 查询高价值订单（大于500元）
high_value_rentals = Rental.objects.filter(total_amount__gt=500)
print(f'  高价值订单数量: {high_value_rentals.count()}')

# 查询特定车辆类型的车辆
suv_vehicles = Vehicle.objects.filter(vehicle_type='SUV')
print(f'  SUV车辆数量: {suv_vehicles.count()}')

# 测试模型验证
print('\n5. 模型验证测试:')
# 测试车辆状态
for vehicle in Vehicle.objects.all():
    print(f'  {vehicle.license_plate}: {vehicle.get_status_display()}')

# 测试客户等级
for customer in Customer.objects.all():
    print(f'  {customer.name}: {customer.get_member_level_display()}')

# 测试订单状态
for rental in Rental.objects.all():
    print(f'  订单{rental.id}: {rental.get_status_display()}')

print('\n✅ Django Shell 测试完成！')