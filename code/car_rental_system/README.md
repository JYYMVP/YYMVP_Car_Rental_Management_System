# 租车管理系统 (Car Rental System)

这是一个基于Django框架开发的租车管理系统，提供车辆管理、客户管理和租赁管理的功能。

## 项目结构

```
car_rental_system/
├── manage.py                 # Django管理脚本
├── db.sqlite3               # SQLite数据库文件
├── car_rental_system/       # 主项目目录
│   ├── __init__.py
│   ├── settings.py          # 项目设置
│   ├── urls.py              # 主URL配置
│   ├── wsgi.py
│   └── asgi.py
├── vehicles/                # 车辆管理应用
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
├── customers/               # 客户管理应用
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
└── rentals/                 # 租赁管理应用
    ├── models.py
    ├── views.py
    ├── urls.py
    └── ...
```

## 应用功能

### 车辆管理 (vehicles)
- 车辆列表查看
- 添加新车辆
- 编辑车辆信息
- 查看车辆详情
- 删除车辆

### 客户管理 (customers)
- 客户列表查看
- 添加新客户
- 编辑客户信息
- 查看客户详情
- 删除客户

### 租赁管理 (rentals)
- 租赁记录列表
- 创建新租赁
- 编辑租赁信息
- 查看租赁详情
- 归还车辆

## 快速开始

### 1. 环境要求
- Python 3.8 或更高版本
- pip（Python 包管理器）

### 2. 安装依赖
进入项目目录，使用以下命令安装依赖：

```bash
cd code/car_rental_system
pip install -r requirements.txt
```

或者直接安装 Django：
```bash
pip install Django==5.2.8
```

### 3. 运行项目
在项目根目录（包含 manage.py 的目录）执行：

```bash
python manage.py runserver
```

或者指定端口：
```bash
python manage.py runserver 8000
```

### 4. 访问系统
启动成功后，打开浏览器访问以下地址：

- **主页面（车辆管理）**：http://127.0.0.1:8000/
- **客户管理**：http://127.0.0.1:8000/customers/
- **租赁管理**：http://127.0.0.1:8000/rentals/
- **管理后台**：http://127.0.0.1:8000/admin/

### 5. 创建超级用户（可选）
如果需要访问管理后台，可以创建超级用户：

```bash
python manage.py createsuperuser
```

然后按照提示输入用户名、邮箱和密码。

### 6. 数据库迁移（如果需要）
如果数据库文件不存在或需要重新创建，执行：

```bash
python manage.py migrate
```

## URL结构

- `/` - 车辆管理首页
- `/customers/` - 客户管理
- `/customers/list/` - 客户列表
- `/customers/add/` - 添加客户
- `/rentals/` - 租赁管理
- `/rentals/list/` - 租赁列表
- `/rentals/add/` - 添加租赁
- `/admin/` - 管理员界面

## 数据库配置

项目使用SQLite数据库，文件名为 `db.sqlite3`，位于项目根目录。

## 时区和语言

- 时区：Asia/Shanghai
- 语言：zh-hans（简体中文）

## 下一步开发

1. **模型设计**：
   - 设计车辆、客户、租赁相关的数据库模型
   - 创建数据库迁移文件

2. **前端界面**：
   - 创建HTML模板
   - 设计用户界面
   - 添加CSS和JavaScript

3. **业务逻辑**：
   - 实现租赁流程
   - 添加数据验证
   - 完善错误处理

4. **功能扩展**：
   - 用户认证系统
   - 权限管理
   - 数据统计和报表

## 许可证

本项目仅供学习和演示使用。