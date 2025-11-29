# 🔍 上传前安全检查清单

在执行 Git 提交和上传之前，请务必检查以下项目：

## ✅ 必须检查的项目

### 1. 数据库文件
```bash
# 在项目根目录运行，确认数据库文件没有被跟踪
git ls-files | grep -E "\.(db|sqlite3)$"

# 如果上述命令有输出，说明数据库文件被跟踪了，需要移除：
# git rm --cached db.sqlite3
```

**预期结果**：命令应该没有输出（空结果）

### 2. 敏感配置文件
```bash
# 检查是否有 local_settings.py 或 .env 文件被跟踪
git ls-files | grep -E "(local_settings\.py|\.env)$"
```

**预期结果**：命令应该没有输出（空结果）

### 3. 查看将要提交的文件
```bash
# 查看所有将被提交的文件
git status

# 查看包括被忽略的文件
git status --ignored
```

**检查要点**：
- ❌ 不应该看到 `db.sqlite3`
- ❌ 不应该看到 `local_settings.py`（如果有的话）
- ❌ 不应该看到 `.env` 文件
- ✅ 应该看到 `.gitignore` 文件

### 4. 检查 .gitignore 文件
```bash
# 确认 .gitignore 文件存在且包含数据库文件
cat .gitignore | grep -E "db\.sqlite3|\.db"
```

**预期结果**：应该看到数据库相关的忽略规则

## 🚨 如果数据库文件已经被跟踪

如果发现数据库文件已经被 Git 跟踪，需要执行以下步骤：

```bash
# 1. 从 Git 跟踪中移除（但保留本地文件）
git rm --cached db.sqlite3

# 2. 确认 .gitignore 包含数据库文件
# （已经包含了）

# 3. 提交这个更改
git add .gitignore
git commit -m "Remove database file from Git tracking"

# 4. 验证数据库文件不再被跟踪
git ls-files | grep db.sqlite3
# 应该没有输出
```

## 📋 快速检查命令

一键检查脚本（Windows PowerShell）：
```powershell
Write-Host "检查数据库文件..." -ForegroundColor Yellow
$dbFiles = git ls-files | Select-String -Pattern "\.(db|sqlite3)$"
if ($dbFiles) {
    Write-Host "❌ 警告：发现数据库文件被跟踪！" -ForegroundColor Red
    $dbFiles
    Write-Host "`n请执行: git rm --cached db.sqlite3" -ForegroundColor Yellow
} else {
    Write-Host "✅ 数据库文件未被跟踪（安全）" -ForegroundColor Green
}

Write-Host "`n检查敏感配置文件..." -ForegroundColor Yellow
$configFiles = git ls-files | Select-String -Pattern "(local_settings\.py|\.env)$"
if ($configFiles) {
    Write-Host "❌ 警告：发现敏感配置文件被跟踪！" -ForegroundColor Red
    $configFiles
} else {
    Write-Host "✅ 敏感配置文件未被跟踪（安全）" -ForegroundColor Green
}

Write-Host "`n检查 .gitignore 文件..." -ForegroundColor Yellow
if (Test-Path .gitignore) {
    Write-Host "✅ .gitignore 文件存在" -ForegroundColor Green
    $gitignoreContent = Get-Content .gitignore -Raw
    if ($gitignoreContent -match "db\.sqlite3") {
        Write-Host "✅ .gitignore 包含数据库文件规则" -ForegroundColor Green
    } else {
        Write-Host "❌ 警告：.gitignore 可能缺少数据库文件规则" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 错误：.gitignore 文件不存在！" -ForegroundColor Red
}
```

## ✨ 安全上传步骤总结

1. ✅ 运行上述检查命令
2. ✅ 确认没有数据库文件被跟踪
3. ✅ 查看 `git status` 确认文件列表
4. ✅ 执行 `git add .`
5. ✅ 再次检查 `git status`，确认没有敏感文件
6. ✅ 执行 `git commit -m "你的提交信息"`
7. ✅ 执行 `git push`

## 📝 注意事项

- **永远不要**强制添加数据库文件：`git add -f db.sqlite3`
- 如果 GitHub 仓库已经存在，检查仓库网页确认没有敏感文件
- 如果不小心上传了敏感文件，立即更改所有密钥和密码
- 考虑使用 Git 的 `git-filter-branch` 从历史中移除敏感文件

