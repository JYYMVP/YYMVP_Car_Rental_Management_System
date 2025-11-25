#!/usr/bin/env python
"""
客户管理功能测试脚本
测试所有CRUD功能是否正常工作
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from customers.models import Customer
from customers.forms import CustomerForm, CustomerSearchForm
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum


def test_customer_crud():
    """测试客户CRUD操作"""
    print("=== 测试客户管理功能 ===\n")
    
    # 1. 测试数据创建
    print("1. 测试客户数据创建")
    test_customers = [
        {
            'name': '测试客户1',
            'phone': '13800000001',
            'email': 'test1@example.com',
            'id_card': '110101199001011111',
            'license_number': 'DL0011111111',
            'license_type': 'C',
            'member_level': 'NORMAL',
        },
        {
            'name': '测试客户2',
            'phone': '13800000002',
            'email': 'test2@example.com',
            'id_card': '110101199002021111',
            'license_number': 'DL0011111112',
            'license_type': 'B',
            'member_level': 'VIP',
        },
    ]
    
    created_customers = []
    for data in test_customers:
        try:
            customer, created = Customer.objects.get_or_create(
                phone=data['phone'],
                defaults=data
            )
            if created:
                created_customers.append(customer)
                print(f"✓ 创建客户: {customer.name}")
            else:
                print(f"- 客户已存在: {customer.name}")
        except Exception as e:
            print(f"✗ 创建客户失败: {data['name']} - {e}")
    
    # 2. 测试表单验证
    print("\n2. 测试表单验证")
    try:
        # 有效数据
        form = CustomerForm({
            'name': '表单测试客户',
            'phone': '13800000301',
            'email': 'formtest@example.com',
            'id_card': '110101199003031111',
            'license_number': 'DL0011111113',
            'license_type': 'A',
            'member_level': 'VIP',
        })
        if form.is_valid():
            print("✓ 表单验证通过")
        else:
            print(f"✗ 表单验证失败: {form.errors}")
        
        # 无效数据测试
        invalid_form = CustomerForm({
            'name': '无效测试',
            'phone': '123',  # 无效手机号
            'id_card': '123',  # 无效身份证
        })
        if not invalid_form.is_valid():
            print("✓ 无效数据验证通过（拒绝无效数据）")
        else:
            print("✗ 无效数据验证失败（应该拒绝无效数据）")
            
    except Exception as e:
        print(f"✗ 表单测试失败: {e}")
    
    # 3. 测试搜索功能
    print("\n3. 测试搜索功能")
    try:
        search_form = CustomerSearchForm({'search': '测试', 'member_level': 'VIP'})
        if search_form.is_valid():
            print("✓ 搜索表单验证通过")
        else:
            print(f"✗ 搜索表单验证失败: {search_form.errors}")
    except Exception as e:
        print(f"✗ 搜索测试失败: {e}")
    
    # 4. 测试数据库查询
    print("\n4. 测试数据库查询")
    try:
        # 基础查询
        total_customers = Customer.objects.count()
        vip_customers = Customer.objects.filter(member_level='VIP').count()
        print(f"✓ 总客户数: {total_customers}")
        print(f"✓ VIP客户数: {vip_customers}")
        
        # 搜索查询
        search_results = Customer.objects.filter(
            Q(name__icontains='测试') | Q(phone__icontains='138')
        )
        print(f"✓ 搜索结果数: {search_results.count()}")
        
        # 统计查询
        customer_stats = Customer.objects.annotate(
            rental_count=Count('rentals'),
            total_amount=Sum('rentals__total_amount')
        )
        print(f"✓ 统计查询完成: {customer_stats.count()} 条记录")
        
    except Exception as e:
        print(f"✗ 数据库查询失败: {e}")
    
    # 5. 测试分页
    print("\n5. 测试分页功能")
    try:
        all_customers = Customer.objects.all()
        paginator = Paginator(all_customers, 10)
        page_obj = paginator.get_page(1)
        print(f"✓ 分页测试: 第1页，共 {paginator.num_pages} 页")
        print(f"✓ 本页记录数: {len(page_obj.object_list)}")
    except Exception as e:
        print(f"✗ 分页测试失败: {e}")
    
    # 6. 测试数据完整性
    print("\n6. 测试数据完整性")
    try:
        # 检查所有必填字段
        customers = Customer.objects.all()
        for customer in customers[:5]:  # 只检查前5个
            required_fields = ['name', 'phone', 'id_card', 'license_number', 'license_type', 'member_level']
            missing_fields = []
            for field in required_fields:
                if not getattr(customer, field):
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"✗ 客户 {customer.name} 缺少字段: {missing_fields}")
            else:
                print(f"✓ 客户 {customer.name} 数据完整")
    except Exception as e:
        print(f"✗ 数据完整性检查失败: {e}")
    
    # 7. 测试会员等级统计
    print("\n7. 测试会员等级统计")
    try:
        vip_count = Customer.objects.filter(member_level='VIP').count()
        normal_count = Customer.objects.filter(member_level='NORMAL').count()
        total = vip_count + normal_count
        
        print(f"✓ VIP会员: {vip_count} 人")
        print(f"✓ 普通会员: {normal_count} 人")
        print(f"✓ 总计: {total} 人")
        
        vip_percentage = (vip_count / total * 100) if total > 0 else 0
        print(f"✓ VIP比例: {vip_percentage:.1f}%")
        
    except Exception as e:
        print(f"✗ 会员等级统计失败: {e}")
    
    print("\n=== 功能测试完成 ===")


def test_rental_integration():
    """测试租赁历史集成"""
    print("\n=== 测试租赁历史集成 ===\n")
    
    try:
        from rentals.models import Rental
        
        # 测试客户与租赁记录的关系
        customers_with_rentals = Customer.objects.filter(
            rentals__isnull=False
        ).distinct().count()
        
        total_customers = Customer.objects.count()
        customers_with_no_rentals = total_customers - customers_with_rentals
        
        print(f"✓ 有租赁记录的客户: {customers_with_rentals} 人")
        print(f"✓ 无租赁记录的客户: {customers_with_no_rentals} 人")
        
        # 测试统计功能
        top_customers = Customer.objects.annotate(
            total_rentals=Count('rentals'),
            total_amount=Sum('rentals__total_amount')
        ).filter(total_rentals__gt=0).order_by('-total_rentals')[:5]
        
        print("✓ 租赁次数最多的客户:")
        for i, customer in enumerate(top_customers, 1):
            print(f"  {i}. {customer.name}: {customer.total_rentals} 次, ¥{customer.total_amount or 0}")
        
        print("\n=== 租赁历史集成测试完成 ===")
        
    except Exception as e:
        print(f"✗ 租赁历史集成测试失败: {e}")


if __name__ == '__main__':
    try:
        test_customer_crud()
        test_rental_integration()
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()