"""
订单状态自动更新功能测试脚本

测试场景:
1. 预订中 → 进行中: 开始日期到达时自动激活
2. 进行中 → 已完成: 结束日期过期时自动完成
3. 边界场景: 未到开始/结束日期不触发更新
4. 车辆状态联动: 订单状态变化时同步更新车辆状态
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from django.db import transaction
from customers.models import Customer
from vehicles.models import Vehicle
from rentals.models import Rental


class OrderStatusUpdateTester:
    """订单状态自动更新测试类"""
    
    def __init__(self):
        self.test_customer = None
        self.test_vehicles = []
        self.test_rentals = []
        
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n清理旧的测试数据...")
        
        # 删除测试订单
        Rental.objects.filter(
            customer__name='测试客户-自动更新'
        ).delete()
        
        # 删除测试车辆
        Vehicle.objects.filter(
            license_plate__startswith='测试'
        ).delete()
        
        # 删除测试客户
        Customer.objects.filter(
            name='测试客户-自动更新'
        ).delete()
        
        print("✓ 清理完成")
    
    def create_test_data(self):
        """创建测试数据"""
        print("\n创建测试数据...")
        
        # 创建测试客户(使用get_or_create避免重复)
        self.test_customer, created = Customer.objects.get_or_create(
            id_card='110101199001011234',
            defaults={
                'name': '测试客户-自动更新',
                'phone': '13800138000',
                'license_number': '110101199001011234',
                'license_type': 'C',
                'member_level': 'NORMAL'
            }
        )
        if not created:
            # 如果已存在,更新信息
            self.test_customer.name = '测试客户-自动更新'
            self.test_customer.phone = '13800138000'
            self.test_customer.save()
        print(f"✓ 创建测试客户: {self.test_customer.name}")
        
        # 创建测试车辆
        today = date.today()
        
        vehicle1 = Vehicle.objects.create(
            license_plate='测试A001',
            brand='测试品牊A',
            model='测试型号A',
            vehicle_type='轿车',
            color='白色',
            daily_rate=Decimal('200.00'),
            status='AVAILABLE'
        )
        self.test_vehicles.append(vehicle1)
        
        vehicle2 = Vehicle.objects.create(
            license_plate='测试B002',
            brand='测试品牊B',
            model='测试型号B',
            vehicle_type='SUV',
            color='黑色',
            daily_rate=Decimal('300.00'),
            status='AVAILABLE'
        )
        self.test_vehicles.append(vehicle2)
        
        vehicle3 = Vehicle.objects.create(
            license_plate='测试C003',
            brand='测试品牊C',
            model='测试型号C',
            vehicle_type='轿车',
            color='红色',
            daily_rate=Decimal('250.00'),
            status='AVAILABLE'
        )
        self.test_vehicles.append(vehicle3)
        
        print(f"✓ 创建 {len(self.test_vehicles)} 个测试车辆")
        
        # 创建测试订单
        # 订单1: 预订中,开始日期=今天 (应该被激活)
        rental1 = Rental.objects.create(
            customer=self.test_customer,
            vehicle=vehicle1,
            start_date=today,
            end_date=today + timedelta(days=3),
            status='PENDING',
            total_amount=Decimal('600.00'),
            notes='测试订单1: 预订中,开始日期=今天'
        )
        self.test_rentals.append(rental1)
        
        # 订单2: 预订中,开始日期=明天 (不应该被激活)
        rental2 = Rental.objects.create(
            customer=self.test_customer,
            vehicle=vehicle2,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=4),
            status='PENDING',
            total_amount=Decimal('900.00'),
            notes='测试订单2: 预订中,开始日期=明天'
        )
        self.test_rentals.append(rental2)
        
        # 订单3: 进行中,结束日期=昨天 (应该被完成)
        rental3 = Rental.objects.create(
            customer=self.test_customer,
            vehicle=vehicle3,
            start_date=today - timedelta(days=5),
            end_date=today - timedelta(days=1),
            status='ONGOING',
            total_amount=Decimal('1000.00'),
            notes='测试订单3: 进行中,结束日期=昨天'
        )
        self.test_rentals.append(rental3)
        # 手动设置车辆为已租状态
        vehicle3.status = 'RENTED'
        vehicle3.save()
        
        print(f"✓ 创建 {len(self.test_rentals)} 个测试订单")
        
    def display_status_before(self):
        """显示更新前的状态"""
        print("\n" + "="*60)
        print("更新前的订单和车辆状态")
        print("="*60)
        
        for rental in self.test_rentals:
            rental.refresh_from_db()
            rental.vehicle.refresh_from_db()
            
            print(f"\n订单 #{rental.id}:")
            print(f"  客户: {rental.customer.name}")
            print(f"  车辆: {rental.vehicle.license_plate}")
            print(f"  开始日期: {rental.start_date}")
            print(f"  结束日期: {rental.end_date}")
            print(f"  订单状态: {rental.get_status_display()} ({rental.status})")
            print(f"  车辆状态: {rental.vehicle.get_status_display()} ({rental.vehicle.status})")
            print(f"  备注: {rental.notes}")
    
    def run_update_command(self):
        """提示执行更新命令"""
        print("\n" + "="*60)
        print("请执行以下命令进行订单状态更新:")
        print("="*60)
        print("\n  python manage.py update_expired_rentals\n")
        input("执行完命令后按回车键继续验证结果...")
    
    def verify_results(self):
        """验证更新结果"""
        print("\n" + "="*60)
        print("验证更新结果")
        print("="*60)
        
        all_passed = True
        
        # 验证订单1: 应该从预订中变为进行中
        rental1 = self.test_rentals[0]
        rental1.refresh_from_db()
        rental1.vehicle.refresh_from_db()
        
        print(f"\n✓ 订单1 验证 (开始日期=今天,预订中→进行中):")
        print(f"  订单状态: {rental1.get_status_display()} ({rental1.status})")
        print(f"  车辆状态: {rental1.vehicle.get_status_display()} ({rental1.vehicle.status})")
        
        if rental1.status == 'ONGOING' and rental1.vehicle.status == 'RENTED':
            print(f"  结果: ✓ 通过 - 订单已激活,车辆已标记为已租")
        else:
            print(f"  结果: ✗ 失败 - 预期订单状态=ONGOING,车辆状态=RENTED")
            all_passed = False
        
        # 验证订单2: 应该保持预订中
        rental2 = self.test_rentals[1]
        rental2.refresh_from_db()
        rental2.vehicle.refresh_from_db()
        
        print(f"\n✓ 订单2 验证 (开始日期=明天,保持预订中):")
        print(f"  订单状态: {rental2.get_status_display()} ({rental2.status})")
        print(f"  车辆状态: {rental2.vehicle.get_status_display()} ({rental2.vehicle.status})")
        
        if rental2.status == 'PENDING' and rental2.vehicle.status == 'AVAILABLE':
            print(f"  结果: ✓ 通过 - 订单保持预订中,车辆保持可用")
        else:
            print(f"  结果: ✗ 失败 - 预期订单状态=PENDING,车辆状态=AVAILABLE")
            all_passed = False
        
        # 验证订单3: 应该从进行中变为已完成
        rental3 = self.test_rentals[2]
        rental3.refresh_from_db()
        rental3.vehicle.refresh_from_db()
        
        print(f"\n✓ 订单3 验证 (结束日期=昨天,进行中→已完成):")
        print(f"  订单状态: {rental3.get_status_display()} ({rental3.status})")
        print(f"  车辆状态: {rental3.vehicle.get_status_display()} ({rental3.vehicle.status})")
        
        if rental3.status == 'COMPLETED' and rental3.vehicle.status == 'AVAILABLE':
            print(f"  结果: ✓ 通过 - 订单已完成,车辆已释放")
        else:
            print(f"  结果: ✗ 失败 - 预期订单状态=COMPLETED,车辆状态=AVAILABLE")
            all_passed = False
        
        # 输出总结
        print("\n" + "="*60)
        if all_passed:
            print("测试总结: ✓ 所有测试通过!")
        else:
            print("测试总结: ✗ 部分测试失败,请检查")
        print("="*60)
        
        return all_passed
    
    def run(self):
        """执行完整的测试流程"""
        print("\n" + "="*60)
        print("订单状态自动更新功能测试")
        print("="*60)
        
        try:
            # 1. 清理旧数据
            self.cleanup_test_data()
            
            # 2. 创建测试数据
            self.create_test_data()
            
            # 3. 显示更新前状态
            self.display_status_before()
            
            # 4. 提示执行更新命令
            self.run_update_command()
            
            # 5. 验证结果
            self.verify_results()
            
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 询问是否清理测试数据
            print("\n是否清理测试数据? (y/n): ", end='')
            choice = input().strip().lower()
            if choice == 'y':
                self.cleanup_test_data()
                print("✓ 测试数据已清理")


if __name__ == '__main__':
    tester = OrderStatusUpdateTester()
    tester.run()
