#!/usr/bin/env python
"""
扩展租车管理系统测试数据的脚本
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


def create_more_vehicles():
    """创建更多车辆数据"""
    print("创建更多车辆数据...")
    
    # 车辆品牌和型号数据
    vehicle_data = [
        {'license_plate': '京E33333', 'brand': '奥迪', 'model': 'A4', 'vehicle_type': '轿车', 'color': '白色', 'daily_rate': 650.00},
        {'license_plate': '京F44444', 'brand': '宝马', 'model': '3系', 'vehicle_type': '轿车', 'color': '蓝色', 'daily_rate': 680.00},
        {'license_plate': '京G55555', 'brand': '大众', 'model': '迈腾', 'vehicle_type': '轿车', 'color': '灰色', 'daily_rate': 300.00},
        {'license_plate': '京H66666', 'brand': '丰田', 'model': '汉兰达', 'vehicle_type': 'SUV', 'color': '黑色', 'daily_rate': 550.00},
        {'license_plate': '京J77777', 'brand': '本田', 'model': '奥德赛', 'vehicle_type': 'MPV', 'color': '银色', 'daily_rate': 400.00},
        {'license_plate': '京K88888', 'brand': '别克', 'model': 'GL8', 'vehicle_type': 'MPV', 'color': '白色', 'daily_rate': 450.00},
        {'license_plate': '京L99999', 'brand': '福特', 'model': '锐界', 'vehicle_type': 'SUV', 'color': '红色', 'daily_rate': 480.00},
        {'license_plate': '京M10000', 'brand': '日产', 'model': '天籁', 'vehicle_type': '轿车', 'color': '黑色', 'daily_rate': 350.00},
        {'license_plate': '京N20000', 'brand': '马自达', 'model': 'CX-5', 'vehicle_type': 'SUV', 'color': '白色', 'daily_rate': 420.00},
        {'license_plate': '京P30000', 'brand': '现代', 'model': '索纳塔', 'vehicle_type': '轿车', 'color': '银色', 'daily_rate': 280.00},
        {'license_plate': '京Q40000', 'brand': '起亚', 'model': 'K5', 'vehicle_type': '轿车', 'color': '蓝色', 'daily_rate': 260.00},
        {'license_plate': '京R50000', 'brand': '斯柯达', 'model': '速派', 'vehicle_type': '轿车', 'color': '灰色', 'daily_rate': 320.00},
    ]
    
    created_count = 0
    for i, data in enumerate(vehicle_data):
        try:
            vehicle = Vehicle.objects.create(
                license_plate=data['license_plate'],
                brand=data['brand'],
                model=data['model'],
                vehicle_type=data['vehicle_type'],
                color=data['color'],
                daily_rate=Decimal(str(data['daily_rate'])),
                status='AVAILABLE'
            )
            print(f"  创建车辆: {vehicle}")
            created_count += 1
        except Exception as e:
            print(f"  跳过已存在的车辆: {data['license_plate']} - {e}")
    
    print(f"成功创建 {created_count} 辆新车辆")
    return created_count


def create_more_customers():
    """创建更多客户数据"""
    print("创建更多客户数据...")
    
    # 客户姓名数据
    customers_data = [
        {'name': '陈小明', 'phone': '13811111111', 'email': 'chenxiaoming@example.com', 'id_card': '310101199001011111', 'license_number': '310101111111111111', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '刘小红', 'phone': '13922222222', 'email': 'liuxiaohong@example.com', 'id_card': '320101199002021222', 'license_number': '320101222222222222', 'license_type': 'B', 'member_level': 'VIP'},
        {'name': '周小华', 'phone': '13733333333', 'email': 'zhouxiaohua@example.com', 'id_card': '330101199003031333', 'license_number': '330101333333333333', 'license_type': 'A', 'member_level': 'NORMAL'},
        {'name': '吴小丽', 'phone': '13644444444', 'email': 'wuxiaoli@example.com', 'id_card': '340101199004041444', 'license_number': '340101444444444444', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '郑小强', 'phone': '13555555555', 'email': 'zhengxiaoqiang@example.com', 'id_card': '350101199005051555', 'license_number': '350101555555555555', 'license_type': 'C', 'member_level': 'VIP'},
        {'name': '孙小美', 'phone': '13466666666', 'email': 'sunxiaomei@example.com', 'id_card': '360101199006061666', 'license_number': '360101666666666666', 'license_type': 'B', 'member_level': 'NORMAL'},
        {'name': '马小龙', 'phone': '13377777777', 'email': 'maxiaolong@example.com', 'id_card': '370101199007071777', 'license_number': '370101777777777777', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '朱小芳', 'phone': '13288888888', 'email': 'zhuxiaofang@example.com', 'id_card': '410101199008081888', 'license_number': '410101888888888888', 'license_type': 'A', 'member_level': 'VIP'},
        {'name': '胡小军', 'phone': '13199999999', 'email': 'huxiaojun@example.com', 'id_card': '420101199009091999', 'license_number': '420101999999999999', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '林小雪', 'phone': '13000000000', 'email': 'linxiaoxue@example.com', 'id_card': '430101199010102000', 'license_number': '430101000000000000', 'license_type': 'B', 'member_level': 'NORMAL'},
        {'name': '何小东', 'phone': '18911111111', 'email': 'hexiaodong@example.com', 'id_card': '440101199011113111', 'license_number': '440101111111111111', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '罗小玉', 'phone': '18822222222', 'email': 'luoxiaoyu@example.com', 'id_card': '450101199012124222', 'license_number': '450101222222222222', 'license_type': 'C', 'member_level': 'VIP'},
        {'name': '梁小文', 'phone': '18733333333', 'email': 'liangxiaowen@example.com', 'id_card': '460101199101015333', 'license_number': '460101333333333333', 'license_type': 'B', 'member_level': 'NORMAL'},
        {'name': '谢小勇', 'phone': '18644444444', 'email': 'xiexiaoyong@example.com', 'id_card': '500101199102026444', 'license_number': '500101444444444444', 'license_type': 'C', 'member_level': 'NORMAL'},
        {'name': '韩小燕', 'phone': '18555555555', 'email': 'hanxiaoyan@example.com', 'id_card': '510101199103037555', 'license_number': '510101555555555555', 'license_type': 'A', 'member_level': 'VIP'},
    ]
    
    created_count = 0
    for i, data in enumerate(customers_data):
        try:
            customer = Customer.objects.create(
                name=data['name'],
                phone=data['phone'],
                email=data['email'],
                id_card=data['id_card'],
                license_number=data['license_number'],
                license_type=data['license_type'],
                member_level=data['member_level']
            )
            print(f"  创建客户: {customer}")
            created_count += 1
        except Exception as e:
            print(f"  跳过已存在的客户: {data['name']} - {e}")
    
    print(f"成功创建 {created_count} 个新客户")
    return created_count


def create_more_rentals():
    """创建更多租赁订单数据"""
    print("创建更多租赁订单数据...")
    
    # 获取车辆和客户
    available_vehicles = list(Vehicle.objects.filter(status='AVAILABLE'))
    all_customers = list(Customer.objects.all())
    
    rental_data = []
    
    # 创建已完成的订单
    for i in range(8):
        customer = all_customers[i % len(all_customers)]
        vehicle = available_vehicles[i % len(available_vehicles)]
        
        start_date = date.today() - timedelta(days=15 + i*2)
        end_date = start_date + timedelta(days=3)
        actual_return_date = end_date
        
        rental_data.append({
            'customer': customer,
            'vehicle': vehicle,
            'start_date': start_date,
            'end_date': end_date,
            'actual_return_date': actual_return_date,
            'status': 'COMPLETED',
            'notes': f'已完成订单 #{i+1}'
        })
    
    # 创建进行中的订单
    for i in range(4):
        customer = all_customers[(i+8) % len(all_customers)]
        vehicle = available_vehicles[(i+4) % len(available_vehicles)]
        
        start_date = date.today() - timedelta(days=i+1)
        end_date = start_date + timedelta(days=5)
        
        rental_data.append({
            'customer': customer,
            'vehicle': vehicle,
            'start_date': start_date,
            'end_date': end_date,
            'status': 'ONGOING',
            'notes': f'进行中订单 #{i+1}'
        })
    
    # 创建待开始的订单
    for i in range(3):
        customer = all_customers[(i+12) % len(all_customers)]
        vehicle = available_vehicles[(i+8) % len(available_vehicles)]
        
        start_date = date.today() + timedelta(days=i+1)
        end_date = start_date + timedelta(days=4)
        
        rental_data.append({
            'customer': customer,
            'vehicle': vehicle,
            'start_date': start_date,
            'end_date': end_date,
            'status': 'PENDING',
            'notes': f'待开始订单 #{i+1}'
        })
    
    created_count = 0
    for i, data in enumerate(rental_data):
        try:
            rental = Rental.objects.create(**data)
            print(f"  创建租赁订单: {rental} - {rental.customer.name}")
            created_count += 1
        except Exception as e:
            print(f"  创建订单失败: {data['customer']} - {e}")
    
    print(f"成功创建 {created_count} 个新租赁订单")
    return created_count


def update_statistics():
    """更新数据统计"""
    print("\n=== 数据统计 ===")
    
    # 统计各种状态
    print("车辆状态统计:")
    for status in ['AVAILABLE', 'RENTED', 'MAINTENANCE', 'UNAVAILABLE']:
        count = Vehicle.objects.filter(status=status).count()
        print(f"  {status}: {count} 辆")
    
    print("\n客户会员等级统计:")
    for level in ['NORMAL', 'VIP', 'GOLD']:
        count = Customer.objects.filter(member_level=level).count()
        print(f"  {level}: {count} 人")
    
    print("\n租赁订单状态统计:")
    for status in ['PENDING', 'ONGOING', 'COMPLETED', 'CANCELLED']:
        count = Rental.objects.filter(status=status).count()
        print(f"  {status}: {count} 个")
    
    # 总体统计
    total_vehicles = Vehicle.objects.count()
    total_customers = Customer.objects.count()
    total_rentals = Rental.objects.count()
    
    print(f"\n总体统计:")
    print(f"  总车辆数: {total_vehicles} 辆")
    print(f"  总客户数: {total_customers} 人")
    print(f"  总订单数: {total_rentals} 个")
    
    return total_vehicles, total_customers, total_rentals


if __name__ == '__main__':
    try:
        print("=== 扩展测试数据 ===\n")
        
        vehicle_count = create_more_vehicles()
        customer_count = create_more_customers()
        rental_count = create_more_rentals()
        
        print(f"\n=== 数据扩展完成 ===")
        print(f"新增车辆: {vehicle_count} 辆")
        print(f"新增客户: {customer_count} 人")
        print(f"新增订单: {rental_count} 个")
        
        total_vehicles, total_customers, total_rentals = update_statistics()
        
        # 验证是否达到要求
        print(f"\n=== 验证结果 ===")
        requirements_met = True
        if total_vehicles < 10:
            print(f"❌ 车辆数量不足: {total_vehicles}/10+")
            requirements_met = False
        else:
            print(f"✅ 车辆数量充足: {total_vehicles}/10+")
        
        if total_customers < 10:
            print(f"❌ 客户数量不足: {total_customers}/10+")
            requirements_met = False
        else:
            print(f"✅ 客户数量充足: {total_customers}/10+")
        
        if total_rentals < 15:
            print(f"❌ 订单数量不足: {total_rentals}/15+")
            requirements_met = False
        else:
            print(f"✅ 订单数量充足: {total_rentals}/15+")
        
        if requirements_met:
            print("\n🎉 所有数据量要求都已满足！")
        else:
            print("\n⚠️ 部分数据量要求未满足，可能需要手动添加数据")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()