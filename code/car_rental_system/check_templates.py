#!/usr/bin/env python
"""
检查Django模板配置
"""
import os
import django
import sys

# 设置Django环境
sys.path.insert(0, '/workspace/code/car_rental_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
django.setup()

from django.conf import settings
from django.template.loader import get_template

print("=== Django模板配置检查 ===")
print(f"BASE_DIR: {settings.BASE_DIR}")
print(f"TEMPLATES: {settings.TEMPLATES}")
print()

# 检查应用模板目录
print("=== 应用模板目录检查 ===")
for app in settings.INSTALLED_APPS:
    if app.startswith('django') or app == 'car_rental_system':
        continue
    try:
        app_module = __import__(app)
        if hasattr(app_module, '__path__'):
            app_path = app_module.__path__[0]
            template_path = os.path.join(app_path, 'templates')
            print(f"{app}: {template_path}")
            print(f"  存在: {os.path.exists(template_path)}")
            if os.path.exists(template_path):
                files = os.listdir(template_path)
                print(f"  文件: {files[:5]}...")  # 只显示前5个文件
        else:
            print(f"{app}: 无__path__属性")
    except Exception as e:
        print(f"{app}: 错误 - {e}")
    print()

# 尝试加载模板
print("=== 模板加载测试 ===")
templates_to_test = [
    'base.html',
    'dashboard.html', 
    'vehicles/index.html',
    'customers/index.html'
]

for template_name in templates_to_test:
    try:
        template = get_template(template_name)
        print(f"✅ {template_name} - 加载成功")
    except Exception as e:
        print(f"❌ {template_name} - 加载失败: {e}")