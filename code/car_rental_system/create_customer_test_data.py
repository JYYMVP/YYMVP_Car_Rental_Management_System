#!/usr/bin/env python
"""
创建客户管理功能的测试数据
包括不同会员等级的客户、完整的租赁历史记录等
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta
import random
from django.db.models import Sum, Count

# 设置Django环境
sys.path.append('/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental


def create_customer_test_data():
    """创建客户测试数据"""
    print("开始创建客户测试数据...")
    
    # 清空现有数据（可选）
    # Customer.objects.all().delete()
    
    # 客户测试数据
    customer_data = [
        # VIP客户
        {
            'name': '张伟',
            'phone': '13800138001',
            'email': 'zhangwei@example.com',
            'id_card': '110101199101011234',
            'license_number': 'DL0012345678',
            'license_type': 'C',
            'member_level': 'VIP',
        },
        {
            'name': '李娜',
            'phone': '13800138002',
            'email': 'lina@example.com',
            'id_card': '110101199202021234',
            'license_number': 'DL0012345679',
            'license_type': 'B',
            'member_level': 'VIP',
        },
        {
            'name': '王强',
            'phone': '13800138003',
            'email': 'wangqiang@example.com',
            'id_card': '110101199303031234',
            'license_number': 'DL0012345680',
            'license_type': 'A',
            'member_level': 'VIP',
        },
        {
            'name': '赵丽',
            'phone': '13800138004',
            'email': 'zhaoli@example.com',
            'id_card': '110101199404041234',
            'license_number': 'DL0012345681',
            'license_type': 'C',
            'member_level': 'VIP',
        },
        {
            'name': '钱七',
            'phone': '13800138005',
            'email': 'qianqi@example.com',
            'id_card': '110101199005051234',
            'license_number': 'DL0012345682',
            'license_type': 'B',
            'member_level': 'VIP',
        },
        
        # 普通客户
        {
            'name': '孙八',
            'phone': '13800138006',
            'email': 'sunba@example.com',
            'id_card': '110101199006061234',
            'license_number': 'DL0012345683',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '周九',
            'phone': '13800138007',
            'email': 'zhoujiu@example.com',
            'id_card': '110101199007071234',
            'license_number': 'DL0012345684',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '吴十',
            'phone': '13800138008',
            'email': 'wushi@example.com',
            'id_card': '110101199008081234',
            'license_number': 'DL0012345685',
            'license_type': 'B',
            'member_level': 'NORMAL',
        },
        {
            'name': '郑十一',
            'phone': '13800138009',
            'email': 'zhengshiyi@example.com',
            'id_card': '110101199009091234',
            'license_number': 'DL0012345686',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '陈十二',
            'phone': '13800138010',
            'email': 'chenshier@example.com',
            'id_card': '110101199010101234',
            'license_number': 'DL0012345687',
            'license_type': 'A',
            'member_level': 'NORMAL',
        },
        {
            'name': '黄十三',
            'phone': '13800138011',
            'email': '',
            'id_card': '110101199011111234',
            'license_number': 'DL0012345688',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '林十四',
            'phone': '13800138012',
            'email': 'linshisi@example.com',
            'id_card': '110101199012121234',
            'license_number': 'DL0012345689',
            'license_type': 'B',
            'member_level': 'NORMAL',
        },
        {
            'name': '何十五',
            'phone': '13800138013',
            'email': 'heshiwu@example.com',
            'id_card': '110101200001011234',
            'license_number': 'DL0012345690',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '高十六',
            'phone': '13800138014',
            'email': 'gaoshiliu@example.com',
            'id_card': '110101200002021234',
            'license_number': 'DL0012345691',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '罗十七',
            'phone': '13800138015',
            'email': 'luoshqi@example.com',
            'id_card': '110101200003031234',
            'license_number': 'DL0012345692',
            'license_type': 'B',
            'member_level': 'VIP',
        },
        {
            'name': '宋十八',
            'phone': '13800138016',
            'email': 'songshiba@example.com',
            'id_card': '110101200004041234',
            'license_number': 'DL0012345693',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '梁十九',
            'phone': '13800138017',
            'email': 'liangshijiu@example.com',
            'id_card': '110101200005051234',
            'license_number': 'DL0012345694',
            'license_type': 'A',
            'member_level': 'VIP',
        },
        {
            'name': '谢二十',
            'phone': '13800138018',
            'email': 'xieershi@example.com',
            'id_card': '110101200006061234',
            'license_number': 'DL0012345695',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '韩二一',
            'phone': '13800138019',
            'email': '',
            'id_card': '110101200007071234',
            'license_number': 'DL0012345696',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
    ]
    
    customers = []
    for data in customer_data:
        # 先尝试通过手机号查找
        customer = Customer.objects.filter(phone=data['phone']).first()
        
        if not customer:
            # 如果不存在，创建新客户
            try:
                customer = Customer.objects.create(**data)
                customers.append(customer)
                print(f"✓ 创建客户: {customer.name} ({customer.phone})")
            except Exception as e:
                print(f"✗ 创建客户失败: {data['name']} - {e}")
        else:
            print(f"- 客户已存在: {customer.name} ({customer.phone})")
    
    print(f"共创建了 {len(customers)} 个新客户")
    return customers


def create_rental_history():
    """为客户创建租赁历史记录"""
    print("\n开始创建租赁历史记录...")
    
    customers = Customer.objects.all()
    vehicles = Vehicle.objects.all()
    
    if not vehicles.exists():
        print("警告: 没有可用车辆，请先创建车辆数据")
        return
    
    rental_statuses = ['COMPLETED', 'ONGOING', 'PENDING', 'CANCELLED']
    rental_notes = [
        '客户提前还车',
        '正常还车',
        '客户要求延期',
        '车辆正常磨损',
        '客户满意度高',
        '续租客户',
        '新客户首租',
        'VIP客户优惠',
    ]
    
    rental_count = 0
    for customer in customers:
        # 每个客户创建 1-8 个租赁记录
        num_rentals = random.randint(1, 8)
        
        for i in range(num_rentals):
            # 随机选择车辆
            vehicle = random.choice(vehicles)
            
            # 生成租赁日期（过去1年内）
            rental_start = date.today() - timedelta(days=random.randint(1, 365))
            rental_days = random.randint(1, 30)
            rental_end = rental_start + timedelta(days=rental_days - 1)
            
            # 实际还车日期
            if random.choice([True, False]):  # 50% 概率有实际还车日期
                actual_return = rental_end + timedelta(days=random.randint(-2, 5))
                if actual_return > date.today():
                    actual_return = date.today()
            else:
                actual_return = None
            
            # 状态分布
            if rental_end < date.today():
                status = random.choices(
                    rental_statuses,
                    weights=[70, 0, 0, 30]  # 已完成和已取消较多
                )[0]
            elif rental_start <= date.today() <= rental_end:
                status = random.choices(
                    rental_statuses,
                    weights=[0, 60, 30, 10]  # 进行中和预订中
                )[0]
            else:
                status = 'PENDING'
            
            # 计算租赁金额
            total_amount = vehicle.daily_rate * rental_days
            
            # 某些情况下调整金额（延期、提前还车等）
            if actual_return and actual_return > rental_end:
                # 延期
                extra_days = (actual_return - rental_end).days
                total_amount += vehicle.daily_rate * extra_days
                note = '客户延期还车'
            elif actual_return and actual_return < rental_end:
                # 提前还车
                note = '客户提前还车，退费已处理'
            else:
                note = random.choice(rental_notes)
            
            # 创建租赁记录
            rental, created = Rental.objects.get_or_create(
                customer=customer,
                vehicle=vehicle,
                start_date=rental_start,
                end_date=rental_end,
                defaults={
                    'actual_return_date': actual_return,
                    'total_amount': total_amount,
                    'status': status,
                    'notes': note,
                }
            )
            
            if created:
                rental_count += 1
    
    print(f"✓ 创建了 {rental_count} 条租赁记录")


def update_customer_statistics():
    """更新客户统计信息"""
    print("\n更新客户统计信息...")
    
    customers = Customer.objects.all()
    for customer in customers:
        rentals = customer.rentals.all()
        total_rentals = rentals.count()
        total_amount = rentals.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        print(f"客户 {customer.name}: {total_rentals} 次租赁，总金额 ¥{total_amount}")
    
    print("客户统计信息更新完成")


def display_customer_summary():
    """显示客户摘要信息"""
    print("\n=== 客户管理测试数据摘要 ===")
    
    total_customers = Customer.objects.count()
    vip_customers = Customer.objects.filter(member_level='VIP').count()
    normal_customers = Customer.objects.filter(member_level='NORMAL').count()
    
    total_rentals = Rental.objects.count()
    total_revenue = Rental.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    print(f"总客户数: {total_customers}")
    print(f"VIP客户: {vip_customers}")
    print(f"普通客户: {normal_customers}")
    print(f"总租赁记录: {total_rentals}")
    print(f"总收入: ¥{total_revenue}")
    
    # 显示各驾照类型分布
    from django.db.models import Count
    license_stats = Customer.objects.values('license_type').annotate(
        count=Count('id')
    ).order_by('license_type')
    
    print("\n驾照类型分布:")
    license_type_choices = {'A': 'A类驾照', 'B': 'B类驾照', 'C': 'C类驾照'}
    for stat in license_stats:
        license_type = license_type_choices[stat['license_type']]
        print(f"  {license_type}: {stat['count']} 人")
    
    # 显示客户租赁前10名
    top_customers = Customer.objects.annotate(
        total_rentals=Count('rentals'),
        total_amount=Sum('rentals__total_amount')
    ).filter(total_rentals__gt=0).order_by('-total_rentals')[:10]
    
    print("\n租赁次数最多的客户:")
    for customer in top_customers:
        print(f"  {customer.name} ({customer.member_level}): {customer.total_rentals} 次, ¥{customer.total_amount or 0}")


if __name__ == '__main__':
    try:
        # 创建客户数据
        customers = create_customer_test_data()
        
        # 创建租赁历史
        create_rental_history()
        
        # 显示摘要
        display_customer_summary()
        
        print("\n✅ 客户管理测试数据创建完成！")
        print("现在可以访问以下功能:")
        print("  - 客户管理首页: http://localhost:8000/customers/")
        print("  - 客户列表: http://localhost:8000/customers/list/")
        print("  - 添加客户: http://localhost:8000/customers/create/")
        
    except Exception as e:
        print(f"❌ 创建测试数据时发生错误: {e}")
        import traceback
        traceback.print_exc()