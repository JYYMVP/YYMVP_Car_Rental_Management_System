"""
创建租赁管理功能的测试数据
"""
import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# 设置Django环境
sys.path.append('/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental


def create_rental_test_data():
    """创建租赁测试数据"""
    print("开始创建租赁测试数据...")
    
    # 清空现有数据
    Rental.objects.all().delete()
    print("已清空现有租赁数据")
    
    # 获取客户和车辆数据
    customers = list(Customer.objects.all())
    vehicles = list(Vehicle.objects.all())
    
    if not customers:
        print("错误：没有客户数据，请先创建客户数据")
        return
    
    if not vehicles:
        print("错误：没有车辆数据，请先创建车辆数据")
        return
    
    # 创建各种状态的租赁订单
    rentals_data = [
        {
            'customer': customers[0],
            'vehicle': vehicles[0],
            'start_date': date.today() - timedelta(days=2),
            'end_date': date.today() + timedelta(days=3),
            'status': 'ONGOING',
            'total_amount': Decimal('1000.00'),
            'notes': 'VIP客户，长期租赁'
        },
        {
            'customer': customers[1],
            'vehicle': vehicles[1],
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=5),
            'status': 'PENDING',
            'total_amount': Decimal('1200.00'),
            'notes': '新客户首次租赁'
        },
        {
            'customer': customers[2],
            'vehicle': vehicles[2],
            'start_date': date.today() - timedelta(days=10),
            'end_date': date.today() - timedelta(days=3),
            'actual_return_date': date.today() - timedelta(days=3),
            'status': 'COMPLETED',
            'total_amount': Decimal('1400.00'),
            'notes': '按时归还，无超期'
        },
        {
            'customer': customers[0],
            'vehicle': vehicles[3],
            'start_date': date.today() - timedelta(days=5),
            'end_date': date.today() - timedelta(days=2),
            'actual_return_date': date.today(),  # 超期2天归还
            'status': 'COMPLETED',
            'total_amount': Decimal('800.00'),
            'notes': '超期2天归还'
        },
        {
            'customer': customers[3],
            'vehicle': vehicles[4],
            'start_date': date.today() + timedelta(days=7),
            'end_date': date.today() + timedelta(days=14),
            'status': 'PENDING',
            'total_amount': Decimal('1400.00'),
            'notes': '未来订单，夏季出行'
        },
        {
            'customer': customers[1],
            'vehicle': vehicles[5],
            'start_date': date.today() - timedelta(days=1),
            'end_date': date.today() + timedelta(days=2),
            'status': 'ONGOING',
            'total_amount': Decimal('600.00'),
            'notes': '短期商务租赁'
        },
        {
            'customer': customers[2],
            'vehicle': vehicles[6],
            'start_date': date.today() - timedelta(days=15),
            'end_date': date.today() - timedelta(days=10),
            'actual_return_date': date.today() - timedelta(days=10),
            'status': 'COMPLETED',
            'total_amount': Decimal('1000.00'),
            'notes': '历史订单，已完成'
        },
        {
            'customer': customers[4],
            'vehicle': vehicles[7],
            'start_date': date.today() - timedelta(days=3),
            'end_date': date.today() + timedelta(days=2),
            'status': 'CANCELLED',
            'total_amount': Decimal('800.00'),
            'notes': '客户临时取消行程'
        },
        {
            'customer': customers[0],
            'vehicle': vehicles[8],
            'start_date': date.today() - timedelta(days=7),
            'end_date': date.today() - timedelta(days=1),
            'actual_return_date': date.today() - timedelta(days=1),
            'status': 'COMPLETED',
            'total_amount': Decimal('1200.00'),
            'notes': '周末短途旅行'
        },
        {
            'customer': customers[3],
            'vehicle': vehicles[9],
            'start_date': date.today() + timedelta(days=3),
            'end_date': date.today() + timedelta(days=10),
            'status': 'PENDING',
            'total_amount': Decimal('1400.00'),
            'notes': '家庭出游预订'
        },
    ]
    
    created_rentals = []
    
    for i, rental_data in enumerate(rentals_data, 1):
        try:
            rental = Rental.objects.create(**rental_data)
            created_rentals.append(rental)
            print(f"创建租赁订单 {i}: {rental}")
            
            # 根据订单状态更新车辆状态
            if rental.status in ['PENDING', 'ONGOING']:
                rental.vehicle.status = 'RENTED'
                rental.vehicle.save()
            
        except Exception as e:
            print(f"创建租赁订单 {i} 失败: {e}")
    
    print(f"成功创建 {len(created_rentals)} 条租赁订单")
    
    # 更新车辆状态
    print("更新车辆状态...")
    for rental in Rental.objects.filter(status__in=['PENDING', 'ONGOING']):
        rental.vehicle.status = 'RENTED'
        rental.vehicle.save()
    
    for rental in Rental.objects.filter(status__in=['COMPLETED', 'CANCELLED']):
        rental.vehicle.status = 'AVAILABLE'
        rental.vehicle.save()
    
    print("车辆状态更新完成")
    
    # 显示统计信息
    total_rentals = Rental.objects.count()
    pending_rentals = Rental.objects.filter(status='PENDING').count()
    ongoing_rentals = Rental.objects.filter(status='ONGOING').count()
    completed_rentals = Rental.objects.filter(status='COMPLETED').count()
    cancelled_rentals = Rental.objects.filter(status='CANCELLED').count()
    
    from django.db.models import Sum
    total_revenue = Rental.objects.filter(status='COMPLETED').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    print("\n=== 租赁数据统计 ===")
    print(f"总订单数: {total_rentals}")
    print(f"预订中: {pending_rentals}")
    print(f"进行中: {ongoing_rentals}")
    print(f"已完成: {completed_rentals}")
    print(f"已取消: {cancelled_rentals}")
    print(f"总收入: ¥{total_revenue}")
    
    return created_rentals


if __name__ == '__main__':
    create_rental_test_data()