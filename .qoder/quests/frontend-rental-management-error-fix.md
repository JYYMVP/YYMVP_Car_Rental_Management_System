# 租赁管理界面模型字段冗余修复设计

## 问题描述

访问租赁管理列表页面 `/rentals/list/` 时出现数据库错误：

```
OperationalError: no such column: vehicles.exterior_image
```

错误发生在 `rentals.views.rental_list` 视图函数中。

## 根本原因分析

Vehicle 模型定义中包含 `exterior_image` 和 `interior_image` 两个图片字段，但这些字段：

1. 当前业务不需要图片功能
2. 数据库表中没有对应的列
3. 模型定义与实际需求不匹配

## 解决方案

### 方案概述

从 Vehicle 模型中移除不需要的图片字段，使模型定义与数据库结构保持一致。

### 核心变更策略

**模型字段清理**

需要从 vehicles/models.py 的 Vehicle 模型中删除以下字段定义：

- exterior_image（外观图）
- interior_image（内饰图）

**涉及文件**

- 目标文件：vehicles/models.py
- 变更内容：移除两个 ImageField 字段定义
- 变更位置：Vehicle 类的字段声明部分

### 操作流程

1. 修改模型定义
   - 打开 vehicles/models.py
   - 删除 exterior_image 字段定义（包括完整的字段声明）
   - 删除 interior_image 字段定义（包括完整的字段声明）
   - 保留其他所有字段不变

2. 验证修复
   - 重新加载 Django 应用
   - 访问租赁管理列表页面 /rentals/list/
   - 确认页面正常加载
   - 验证车辆数据正常展示

### 注意事项

- 仅删除字段定义，不涉及数据库迁移
- 不影响现有车辆数据
- 模型中其他字段保持不变
- 如未来需要图片功能，可重新添加字段并执行迁移

## 预期结果

- 数据库表结构与模型定义保持一致
- 租赁管理列表页面正常访问
- 不再出现字段缺失错误
- 系统功能完全恢复正常
