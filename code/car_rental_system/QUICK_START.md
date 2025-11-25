# 快速运行指南

## 启动项目

```bash
cd /workspace/code/car_rental_system
python manage.py runserver
```

## 访问地址

- 主页面：http://127.0.0.1:8000/ （车辆管理）
- 客户管理：http://127.0.0.1:8000/customers/
- 租赁管理：http://127.0.0.1:8000/rentals/
- 管理后台：http://127.0.0.1:8000/admin/

## 创建超级用户

```bash
python manage.py createsuperuser
```

## 应用测试

访问各个URL测试基本页面：
- `/` - 车辆管理首页
- `/customers/` - 客户管理首页
- `/rentals/` - 租赁管理首页