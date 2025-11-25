"""
数据库优化脚本
用于创建索引以提高查询性能
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from django.db import connection

def create_indexes():
    """创建数据库索引以提高查询性能"""
    with connection.cursor() as cursor:
        # 车辆表索引
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_status ON vehicles_vehicle(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_brand ON vehicles_vehicle(brand)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_type ON vehicles_vehicle(vehicle_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_license_plate ON vehicles_vehicle(license_plate)")
            print("✓ 车辆表索引创建成功")
        except Exception as e:
            print(f"车辆表索引创建失败: {e}")
        
        # 客户表索引
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_member_level ON customers_customer(member_level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_name ON customers_customer(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_phone ON customers_customer(phone)")
            print("✓ 客户表索引创建成功")
        except Exception as e:
            print(f"客户表索引创建失败: {e}")
        
        # 租赁表索引
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_status ON rentals_rental(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_customer ON rentals_rental(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_vehicle ON rentals_rental(vehicle_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_created_at ON rentals_rental(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_start_date ON rentals_rental(start_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rental_end_date ON rentals_rental(end_date)")
            print("✓ 租赁表索引创建成功")
        except Exception as e:
            print(f"租赁表索引创建失败: {e}")
        
        connection.commit()
        print("\n所有索引创建完成！")

if __name__ == '__main__':
    print("开始创建数据库索引...")
    create_indexes()
    print("\n优化完成！")

