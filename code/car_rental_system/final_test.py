#!/usr/bin/env python
"""租车管理系统最终测试脚本"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.test.utils import get_runner
from django.conf import settings

# 设置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')

# 初始化Django
django.setup()

def test_models():
    """测试数据模型"""
    print("=== 测试数据模型 ===")
    from vehicles.models import Vehicle
    from customers.models import Customer
    from rentals.models import Rental
    
    vehicle_count = Vehicle.objects.count()
    customer_count = Customer.objects.count()
    rental_count = Rental.objects.count()
    
    print(f"车辆数量: {vehicle_count}")
    print(f"客户数量: {customer_count}")
    print(f"租赁订单数量: {rental_count}")
    
    if vehicle_count > 0 and customer_count > 0 and rental_count > 0:
        print("✅ 数据模型测试通过")
        return True
    else:
        print("❌ 数据模型测试失败 - 缺少测试数据")
        return False

def test_database():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ 数据库连接正常")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_urls():
    """测试URL配置"""
    print("\n=== 测试URL配置 ===")
    try:
        from django.urls import resolve
        from django.test import Client
        
        client = Client()
        
        # 测试主页
        response = client.get('/')
        if response.status_code == 200:
            print("✅ 主页URL测试通过")
        else:
            print(f"❌ 主页URL测试失败: {response.status_code}")
            return False
        
        # 测试车辆管理
        response = client.get('/vehicles/')
        if response.status_code == 200:
            print("✅ 车辆管理URL测试通过")
        else:
            print(f"❌ 车辆管理URL测试失败: {response.status_code}")
            return False
        
        # 测试客户管理
        response = client.get('/customers/')
        if response.status_code == 200:
            print("✅ 客户管理URL测试通过")
        else:
            print(f"❌ 客户管理URL测试失败: {response.status_code}")
            return False
        
        # 测试租赁管理
        response = client.get('/rentals/')
        if response.status_code == 200:
            print("✅ 租赁管理URL测试通过")
            return True
        else:
            print(f"❌ 租赁管理URL测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ URL配置测试失败: {e}")
        return False

def test_templates():
    """测试模板加载"""
    print("\n=== 测试模板加载 ===")
    try:
        from django.template import loader
        from django.template.engine import Engine
        
        # 测试主模板
        template = loader.get_template('dashboard.html')
        print("✅ 主模板加载成功")
        
        # 测试车辆模板
        template = loader.get_template('vehicles/vehicle_list.html')
        print("✅ 车辆模板加载成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板加载失败: {e}")
        return False

def test_static_files():
    """测试静态文件"""
    print("\n=== 测试静态文件 ===")
    try:
        from django.contrib.staticfiles.finders import get_finders
        
        found_files = 0
        for finder in get_finders():
            try:
                files_list = finder.list(ignore_patterns=['*.pyc', '__pycache__'])
                for path, storage in files_list:
                    found_files += 1
                    if found_files > 5:  # 只检查前5个文件
                        break
                if found_files > 5:
                    break
            except Exception:
                continue
        
        if found_files > 0:
            print(f"✅ 找到 {found_files} 个静态文件")
            return True
        else:
            print("❌ 未找到静态文件")
            return False
            
    except Exception as e:
        print(f"❌ 静态文件测试失败: {e}")
        return False

def run_django_check():
    """运行Django系统检查"""
    print("\n=== 运行Django系统检查 ===")
    try:
        execute_from_command_line(['manage.py', 'check'])
        print("✅ Django系统检查通过")
        return True
    except Exception as e:
        print(f"❌ Django系统检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 租车管理系统最终测试开始")
    print("=" * 50)
    
    tests = [
        ("Django系统检查", run_django_check),
        ("数据库连接", test_database),
        ("数据模型", test_models),
        ("URL配置", test_urls),
        ("模板加载", test_templates),
        ("静态文件", test_static_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"⚠️  测试 '{test_name}' 失败")
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统已准备好投入使用！")
        return True
    else:
        print("⚠️  部分测试失败，请检查系统配置")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)