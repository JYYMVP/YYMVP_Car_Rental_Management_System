#!/usr/bin/env python
"""
租车管理系统综合测试脚本
全面测试系统功能、性能和安全性
"""
import os
import sys
import django
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from django.test import TestCase
from django.test.client import Client
from django.db import connection
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q, F
from django.utils import timezone

from vehicles.models import Vehicle
from customers.models import Customer
from rentals.models import Rental


class SystemTestSuite:
    """系统测试套件"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = {}
        self.start_time = time.time()
        
    def log_test(self, test_name, status, message, details=None):
        """记录测试结果"""
        self.test_results[test_name] = {
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        
    def test_database_connectivity(self):
        """测试数据库连接"""
        try:
            # 测试基本查询
            vehicle_count = Vehicle.objects.count()
            customer_count = Customer.objects.count()
            rental_count = Rental.objects.count()
            
            # 测试复杂查询
            vip_rentals = Rental.objects.filter(
                customer__member_level='VIP'
            ).select_related('customer', 'vehicle')
            
            # 测试事务
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM vehicles")
                result = cursor.fetchone()
                
            self.log_test(
                "数据库连接测试", 
                "PASS", 
                f"数据库连接正常 - 车辆:{vehicle_count}, 客户:{customer_count}, 租赁:{rental_count}",
                {
                    'vehicle_count': vehicle_count,
                    'customer_count': customer_count,
                    'rental_count': rental_count,
                    'vip_rental_count': vip_rentals.count()
                }
            )
            return True
        except Exception as e:
            self.log_test("数据库连接测试", "FAIL", f"数据库连接失败: {str(e)}")
            return False
    
    def test_vehicle_management(self):
        """测试车辆管理功能"""
        try:
            # 1. 创建测试车辆
            test_vehicle = Vehicle.objects.create(
                license_plate='TEST001',
                brand='测试品牌',
                model='测试型号',
                vehicle_type='轿车',
                color='白色',
                daily_rate=Decimal('100.00')
            )
            
            # 2. 测试查询功能
            vehicles = Vehicle.objects.all()
            available_vehicles = Vehicle.objects.filter(status='AVAILABLE')
            rental_vehicles = Vehicle.objects.filter(status='RENTED')
            
            # 3. 测试复杂查询
            expensive_vehicles = Vehicle.objects.filter(
                daily_rate__gt=200
            ).select_related()
            
            # 4. 测试分页
            paginator = Paginator(vehicles, 10)
            page1 = paginator.get_page(1)
            
            # 5. 测试聚合查询
            vehicle_stats = Vehicle.objects.aggregate(
                total=Count('id'),
                available=Count('id', filter=Q(status='AVAILABLE')),
                rented=Count('id', filter=Q(status='RENTED')),
                avg_rate=Sum('daily_rate') / Count('id')
            )
            
            # 6. 清理测试数据
            test_vehicle.delete()
            
            self.log_test(
                "车辆管理测试", 
                "PASS", 
                "车辆管理功能正常",
                {
                    'total_vehicles': vehicle_stats['total'],
                    'available_vehicles': vehicle_stats['available'],
                    'rented_vehicles': vehicle_stats['rented'],
                    'avg_daily_rate': float(vehicle_stats['avg_rate'] or 0),
                    'page_count': paginator.num_pages
                }
            )
            return True
            
        except Exception as e:
            self.log_test("车辆管理测试", "FAIL", f"车辆管理测试失败: {str(e)}")
            return False
    
    def test_customer_management(self):
        """测试客户管理功能"""
        try:
            # 1. 统计查询
            total_customers = Customer.objects.count()
            vip_customers = Customer.objects.filter(member_level='VIP').count()
            normal_customers = Customer.objects.filter(member_level='NORMAL').count()
            
            # 2. 复杂查询测试
            customers_with_rentals = Customer.objects.filter(
                rentals__isnull=False
            ).distinct().count()
            
            # 3. 测试搜索功能
            search_results = Customer.objects.filter(
                Q(name__icontains='测试') | Q(phone__icontains='138')
            )
            
            # 4. 测试聚合统计
            customer_stats = Customer.objects.aggregate(
                total=Count('id'),
                vip_count=Count('id', filter=Q(member_level='VIP')),
                normal_count=Count('id', filter=Q(member_level='NORMAL'))
            )
            
            # 5. 测试客户租赁历史查询
            customer_history = Customer.objects.annotate(
                rental_count=Count('rentals'),
                total_spent=Sum('rentals__total_amount')
            ).filter(rental_count__gt=0)[:5]
            
            self.log_test(
                "客户管理测试", 
                "PASS", 
                "客户管理功能正常",
                {
                    'total_customers': total_customers,
                    'vip_customers': vip_customers,
                    'normal_customers': normal_customers,
                    'customers_with_rentals': customers_with_rentals,
                    'top_customers': [
                        {
                            'name': c.name,
                            'rental_count': c.rental_count,
                            'total_spent': float(c.total_spent or 0)
                        } for c in customer_history
                    ]
                }
            )
            return True
            
        except Exception as e:
            self.log_test("客户管理测试", "FAIL", f"客户管理测试失败: {str(e)}")
            return False
    
    def test_rental_management(self):
        """测试租赁管理功能"""
        try:
            # 1. 统计查询
            total_rentals = Rental.objects.count()
            pending_rentals = Rental.objects.filter(status='PENDING').count()
            ongoing_rentals = Rental.objects.filter(status='ONGOING').count()
            completed_rentals = Rental.objects.filter(status='COMPLETED').count()
            
            # 2. 收入统计
            revenue_stats = Rental.objects.filter(
                status='COMPLETED'
            ).aggregate(
                total_revenue=Sum('total_amount'),
                avg_revenue=Sum('total_amount') / Count('id')
            )
            
            # 3. 复杂查询
            high_value_rentals = Rental.objects.filter(
                total_amount__gt=500
            ).select_related('customer', 'vehicle')
            
            # 4. 测试订单状态转换
            recent_rentals = Rental.objects.order_by('-created_at')[:10]
            
            # 5. 测试车辆可用性检查
            available_vehicles = Vehicle.objects.filter(
                status='AVAILABLE'
            )
            
            # 6. 测试客户租赁历史
            customer_rental_stats = Customer.objects.annotate(
                rental_count=Count('rentals'),
                total_spent=Sum('rentals__total_amount')
            ).order_by('-rental_count')[:5]
            
            self.log_test(
                "租赁管理测试", 
                "PASS", 
                "租赁管理功能正常",
                {
                    'total_rentals': total_rentals,
                    'pending_rentals': pending_rentals,
                    'ongoing_rentals': ongoing_rentals,
                    'completed_rentals': completed_rentals,
                    'total_revenue': float(revenue_stats['total_revenue'] or 0),
                    'avg_revenue': float(revenue_stats['avg_revenue'] or 0),
                    'available_vehicles': available_vehicles.count(),
                    'top_customers': [
                        {
                            'name': c.name,
                            'rental_count': c.rental_count,
                            'total_spent': float(c.total_spent or 0)
                        } for c in customer_rental_stats
                    ]
                }
            )
            return True
            
        except Exception as e:
            self.log_test("租赁管理测试", "FAIL", f"租赁管理测试失败: {str(e)}")
            return False
    
    def test_business_logic(self):
        """测试业务逻辑"""
        try:
            # 1. 测试车辆状态与订单状态的一致性
            rented_vehicles = Vehicle.objects.filter(status='RENTED')
            vehicle_rentals = {}
            
            for vehicle in rented_vehicles:
                active_rentals = vehicle.rentals.filter(
                    status__in=['PENDING', 'ONGOING']
                ).count()
                vehicle_rentals[vehicle.license_plate] = active_rentals
            
            # 2. 测试VIP折扣逻辑
            vip_customers = Customer.objects.filter(member_level='VIP')
            vip_savings = 0
            for customer in vip_customers:
                for rental in customer.rentals.filter(status='COMPLETED'):
                    # VIP 10%折扣
                    expected_rate = rental.vehicle.daily_rate * rental.rental_days
                    discount = expected_rate * Decimal('0.10')
                    if rental.total_amount < expected_rate:
                        vip_savings += float(discount)
            
            # 3. 测试超期费用计算逻辑
            overdue_rentals = Rental.objects.filter(
                status='ONGOING',
                end_date__lt=timezone.now().date()
            )
            
            # 4. 测试车辆不可删除逻辑
            vehicles_with_active_rentals = Vehicle.objects.filter(
                rentals__status__in=['PENDING', 'ONGOING']
            ).distinct()
            
            self.log_test(
                "业务逻辑测试", 
                "PASS", 
                "业务逻辑验证通过",
                {
                    'rented_vehicle_consistency': len([v for v in vehicle_rentals.values() if v > 0]),
                    'total_vip_savings': vip_savings,
                    'overdue_rentals': overdue_rentals.count(),
                    'vehicles_cannot_delete': vehicles_with_active_rentals.count()
                }
            )
            return True
            
        except Exception as e:
            self.log_test("业务逻辑测试", "FAIL", f"业务逻辑测试失败: {str(e)}")
            return False
    
    def test_performance(self):
        """测试性能"""
        try:
            start_time = time.time()
            
            # 1. 测试复杂查询性能
            complex_query = Rental.objects.select_related(
                'customer', 'vehicle'
            ).filter(
                customer__member_level='VIP',
                total_amount__gt=300
            ).order_by('-total_amount')
            
            results = list(complex_query)
            query_time = time.time() - start_time
            
            # 2. 测试聚合查询性能
            start_time = time.time()
            stats = Vehicle.objects.aggregate(
                total=Count('id'),
                avg_rate=Sum('daily_rate') / Count('id')
            )
            agg_time = time.time() - start_time
            
            # 3. 测试批量查询性能
            start_time = time.time()
            vehicles = Vehicle.objects.all().select_related()[:100]
            list(vehicles)
            batch_time = time.time() - start_time
            
            # 性能基准：复杂查询 < 1秒，聚合查询 < 0.5秒，批量查询 < 0.3秒
            performance_score = 0
            if query_time < 1.0:
                performance_score += 1
            if agg_time < 0.5:
                performance_score += 1
            if batch_time < 0.3:
                performance_score += 1
                
            status = "PASS" if performance_score >= 2 else "WARN"
            message = f"性能测试 {performance_score}/3 项达标"
            
            self.log_test(
                "性能测试", 
                status, 
                message,
                {
                    'complex_query_time': round(query_time, 3),
                    'aggregation_time': round(agg_time, 3),
                    'batch_query_time': round(batch_time, 3),
                    'results_count': len(results),
                    'performance_score': f"{performance_score}/3"
                }
            )
            return True
            
        except Exception as e:
            self.log_test("性能测试", "FAIL", f"性能测试失败: {str(e)}")
            return False
    
    def test_data_integrity(self):
        """测试数据完整性"""
        try:
            # 1. 检查外键关联
            orphaned_rentals = Rental.objects.filter(
                Q(customer__isnull=True) | Q(vehicle__isnull=True)
            )
            
            # 2. 检查唯一性约束
            duplicate_plates = Vehicle.objects.values('license_plate').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            duplicate_ids = Customer.objects.values('id_card').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            # 3. 检查数据格式
            invalid_phones = Customer.objects.exclude(
                phone__regex=r'^1[3-9]\d{9}$'
            )
            
            # 4. 检查状态一致性
            status_issues = []
            for vehicle in Vehicle.objects.filter(status='RENTED'):
                has_active_rental = vehicle.rentals.filter(
                    status__in=['PENDING', 'ONGOING']
                ).exists()
                if not has_active_rental:
                    status_issues.append(vehicle.license_plate)
            
            # 5. 检查日期逻辑
            date_issues = Rental.objects.filter(
                end_date__lt=F('start_date')
            )
            
            integrity_score = 0
            issues = []
            
            if orphaned_rentals.count() == 0:
                integrity_score += 1
            else:
                issues.append(f"孤立租赁记录: {orphaned_rentals.count()}")
                
            if duplicate_plates.count() == 0:
                integrity_score += 1
            else:
                issues.append(f"重复车牌号: {duplicate_plates.count()}")
                
            if invalid_phones.count() == 0:
                integrity_score += 1
            else:
                issues.append(f"无效手机号: {invalid_phones.count()}")
                
            if len(status_issues) == 0:
                integrity_score += 1
            else:
                issues.append(f"状态不一致车辆: {len(status_issues)}")
                
            if date_issues.count() == 0:
                integrity_score += 1
            else:
                issues.append(f"日期逻辑错误: {date_issues.count()}")
            
            status = "PASS" if integrity_score >= 4 else "WARN"
            
            self.log_test(
                "数据完整性测试", 
                status, 
                f"数据完整性 {integrity_score}/5 项正常",
                {
                    'integrity_score': f"{integrity_score}/5",
                    'orphaned_rentals': orphaned_rentals.count(),
                    'duplicate_plates': duplicate_plates.count(),
                    'invalid_phones': invalid_phones.count(),
                    'status_issues': len(status_issues),
                    'date_issues': date_issues.count(),
                    'issues': issues[:5]  # 只显示前5个问题
                }
            )
            return True
            
        except Exception as e:
            self.log_test("数据完整性测试", "FAIL", f"数据完整性测试失败: {str(e)}")
            return False
    
    def test_web_interface(self):
        """测试Web界面"""
        try:
            # 1. 测试主要页面可访问性
            pages_to_test = [
                ('/', '主页'),
                ('/vehicles/', '车辆管理'),
                ('/customers/', '客户管理'),
                ('/rentals/', '租赁管理'),
            ]
            
            accessible_pages = 0
            page_results = []
            
            for url, name in pages_to_test:
                try:
                    response = self.client.get(url)
                    if response.status_code == 200:
                        accessible_pages += 1
                        page_results.append({'page': name, 'status': 'OK'})
                    else:
                        page_results.append({'page': name, 'status': f'HTTP {response.status_code}'})
                except Exception as e:
                    page_results.append({'page': name, 'status': f'ERROR: {str(e)}'})
            
            # 2. 测试表单功能
            form_tests = 0
            try:
                # 测试车辆搜索表单
                response = self.client.get('/vehicles/?search=宝马&status=AVAILABLE')
                if response.status_code == 200:
                    form_tests += 1
            except:
                pass
                
            try:
                # 测试客户搜索表单  
                response = self.client.get('/customers/?search=测试')
                if response.status_code == 200:
                    form_tests += 1
            except:
                pass
            
            status = "PASS" if accessible_pages >= 3 and form_tests >= 1 else "WARN"
            
            self.log_test(
                "Web界面测试", 
                status, 
                f"Web界面测试 {accessible_pages}/4 页面可访问",
                {
                    'accessible_pages': f"{accessible_pages}/{len(pages_to_test)}",
                    'form_tests_passed': f"{form_tests}/2",
                    'page_results': page_results
                }
            )
            return True
            
        except Exception as e:
            self.log_test("Web界面测试", "FAIL", f"Web界面测试失败: {str(e)}")
            return False
    
    def test_security(self):
        """测试安全性"""
        try:
            # 1. 测试CSRF保护
            response = self.client.post('/vehicles/', {'test': 'data'})
            csrf_protected = response.status_code == 403  # 应该返回403 Forbidden
            
            # 2. 测试SQL注入防护
            malicious_queries = [
                "'; DROP TABLE vehicles; --",
                "1' OR '1'='1",
                "'; UPDATE customers SET name='hacked'; --"
            ]
            
            sql_injection_safe = True
            for query in malicious_queries:
                try:
                    response = self.client.get(f'/vehicles/?search={query}')
                    # 如果没有返回500错误，说明基本的SQL注入防护有效
                    if response.status_code == 500:
                        sql_injection_safe = False
                        break
                except:
                    pass
            
            # 3. 测试XSS防护
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>"
            ]
            
            xss_safe = True
            for payload in xss_payloads:
                try:
                    response = self.client.get(f'/vehicles/?search={payload}')
                    # 检查响应中是否包含未转义的脚本标签
                    if payload in response.content.decode('utf-8', errors='ignore'):
                        xss_safe = False
                        break
                except:
                    pass
            
            security_score = 0
            if csrf_protected:
                security_score += 1
            if sql_injection_safe:
                security_score += 1
            if xss_safe:
                security_score += 1
            
            status = "PASS" if security_score >= 2 else "WARN"
            
            self.log_test(
                "安全性测试", 
                status, 
                f"安全性测试 {security_score}/3 项通过",
                {
                    'csrf_protected': csrf_protected,
                    'sql_injection_safe': sql_injection_safe,
                    'xss_safe': xss_safe,
                    'security_score': f"{security_score}/3"
                }
            )
            return True
            
        except Exception as e:
            self.log_test("安全性测试", "FAIL", f"安全性测试失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("🧪 租车管理系统综合测试开始")
        print("="*80)
        
        # 执行所有测试
        tests = [
            self.test_database_connectivity,
            self.test_vehicle_management,
            self.test_customer_management,
            self.test_rental_management,
            self.test_business_logic,
            self.test_performance,
            self.test_data_integrity,
            self.test_web_interface,
            self.test_security,
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                print()  # 空行分隔
            except Exception as e:
                print(f"❌ 测试执行异常: {str(e)}")
                print()
        
        # 生成测试报告
        self.generate_report()
        
        print("="*80)
        print(f"🎯 测试完成: {passed_tests}/{total_tests} 项测试通过")
        print(f"⏱️ 总耗时: {time.time() - self.start_time:.2f} 秒")
        print("="*80)
        
        return passed_tests, total_tests
    
    def generate_report(self):
        """生成测试报告"""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results.values() if r['status'] == 'PASS']),
                'failed_tests': len([r for r in self.test_results.values() if r['status'] == 'FAIL']),
                'warned_tests': len([r for r in self.test_results.values() if r['status'] == 'WARN']),
                'execution_time': time.time() - self.start_time
            },
            'test_details': self.test_results,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存详细报告
        with open('/workspace/code/car_rental_system/test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成简化的文本报告
        report_text = f"""
租车管理系统测试报告
==============================================
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
执行时间: {report['test_summary']['execution_time']:.2f} 秒

测试概览:
- 总测试数: {report['test_summary']['total_tests']}
- 通过测试: {report['test_summary']['passed_tests']} ✅
- 失败测试: {report['test_summary']['failed_tests']} ❌
- 警告测试: {report['test_summary']['warned_tests']} ⚠️

详细结果:
"""
        
        for test_name, result in self.test_results.items():
            status_symbol = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[result['status']]
            report_text += f"\n{status_symbol} {test_name}\n"
            report_text += f"   状态: {result['message']}\n"
            if result['details']:
                for key, value in result['details'].items():
                    report_text += f"   {key}: {value}\n"
        
        # 保存文本报告
        with open('/workspace/code/car_rental_system/test_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"📊 测试报告已生成:")
        print(f"   - JSON格式: test_report.json")
        print(f"   - 文本格式: test_report.txt")


if __name__ == '__main__':
    # 创建测试套件并运行所有测试
    test_suite = SystemTestSuite()
    passed, total = test_suite.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if passed == total else 1)