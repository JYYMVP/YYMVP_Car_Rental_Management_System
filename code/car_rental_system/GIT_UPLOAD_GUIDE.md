# GitHub 上传指南

本指南将帮助您安全地将项目上传到 GitHub，确保不会泄露敏感信息。

## ⚠️ 重要：保护敏感信息

在将代码上传到 GitHub 之前，请确保以下内容：

### 1. 数据库文件（已自动忽略）
- ✅ `db.sqlite3` - 数据库文件已添加到 `.gitignore`
- ✅ 所有 `.db` 和 `.sqlite3` 文件都不会被上传

### 2. 敏感配置文件
- ✅ `local_settings.py` - 本地配置已添加到 `.gitignore`
- ✅ `.env` 文件已添加到 `.gitignore`

### 3. Python 缓存文件
- ✅ `__pycache__/` 目录已自动忽略
- ✅ `*.pyc` 文件已自动忽略

## 📋 上传前检查清单

在上传之前，请执行以下检查：

### 步骤 1: 检查 .gitignore 文件
```bash
# 确认 .gitignore 文件存在
cat .gitignore
```

### 步骤 2: 检查是否有敏感文件
```bash
# 查看哪些文件将被上传（不包括被忽略的文件）
git status

# 查看所有文件（包括被忽略的）
git status --ignored
```

### 步骤 3: 确认数据库文件未被跟踪
```bash
# 检查 db.sqlite3 是否在 Git 跟踪列表中
git ls-files | grep db.sqlite3

# 如果没有输出，说明数据库文件未被跟踪（这是正确的）
```

### 步骤 4: 如果数据库文件已经被跟踪
如果 `db.sqlite3` 已经被 Git 跟踪，需要从 Git 中移除（但保留本地文件）：

```bash
# 从 Git 跟踪中移除数据库文件（但不删除本地文件）
git rm --cached db.sqlite3

# 提交这个更改
git add .gitignore
git commit -m "Remove database file from Git tracking"
```

## 🚀 上传步骤

### 方法 1: 使用 GitHub Desktop（推荐初学者）

1. 打开 GitHub Desktop
2. 点击 "File" → "Add Local Repository"
3. 选择项目目录：`E:\新建文件夹\jyymvp\zuche\zuche\code\car_rental_system`
4. 检查更改的文件列表，确保没有 `db.sqlite3`
5. 填写提交信息，例如："Initial commit: Car rental system"
6. 点击 "Commit to main"
7. 点击 "Publish repository" 创建 GitHub 仓库并上传

### 方法 2: 使用 Git 命令行

```bash
# 1. 进入项目目录
cd E:\新建文件夹\jyymvp\zuche\zuche\code\car_rental_system

# 2. 初始化 Git 仓库（如果还没有初始化）
git init

# 3. 添加所有文件（.gitignore 会自动排除敏感文件）
git add .

# 4. 检查将要提交的文件列表
git status

# 5. 确认没有 db.sqlite3 或其他敏感文件
# 如果看到 db.sqlite3，执行: git rm --cached db.sqlite3

# 6. 提交更改
git commit -m "Initial commit: Car rental system"

# 7. 在 GitHub 上创建新仓库（在网页上操作）
# 8. 添加远程仓库
git remote add origin https://github.com/your-username/your-repo-name.git

# 9. 上传代码
git branch -M main
git push -u origin main
```

## 🔒 安全建议

### 1. 使用环境变量存储敏感信息（推荐）

创建 `.env` 文件（已在 .gitignore 中）：
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

在 `settings.py` 中使用：
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-for-development')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

### 2. 使用 local_settings.py（当前项目方式）

1. 复制 `local_settings.py.example` 为 `local_settings.py`：
   ```bash
   cp car_rental_system/local_settings.py.example car_rental_system/local_settings.py
   ```

2. 在 `local_settings.py` 中填写真实的配置信息

3. 在 `settings.py` 中导入：
   ```python
   try:
       from .local_settings import *
   except ImportError:
       pass
   ```

### 3. 检查 settings.py 中的硬编码密钥

当前 `settings.py` 中有硬编码的 SECRET_KEY。在生产环境，建议：
- 从环境变量读取
- 或从 `local_settings.py` 读取
- 不要将真实的 SECRET_KEY 提交到 Git

## ✅ 验证上传

上传完成后，在 GitHub 网页上检查：

1. ✅ 确认没有 `db.sqlite3` 文件
2. ✅ 确认没有 `local_settings.py` 文件
3. ✅ 确认没有 `__pycache__/` 目录
4. ✅ 确认 `.gitignore` 文件已上传

## 📝 项目初始化说明（给其他开发者）

在 README.md 中建议添加以下说明：

```markdown
## 初始设置

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 创建数据库：`python manage.py migrate`
4. 创建本地配置：复制 `local_settings.py.example` 为 `local_settings.py`
5. 运行服务器：`python manage.py runserver`
```

## ⚠️ 如果已经上传了敏感文件

如果不小心已经上传了敏感文件到 GitHub：

1. **立即更改所有密钥和密码**
2. **从 Git 历史中移除文件**（需要重写历史）：
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch db.sqlite3" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **强制推送**（会覆盖远程历史）：
   ```bash
   git push origin --force --all
   ```
4. **警告**：这会重写 Git 历史，如果是团队项目，需要通知所有成员

## 📞 需要帮助？

如果遇到问题：
1. 检查 `.gitignore` 文件是否正确
2. 使用 `git status` 查看将要上传的文件
3. 如果有疑问，不要上传，先检查

