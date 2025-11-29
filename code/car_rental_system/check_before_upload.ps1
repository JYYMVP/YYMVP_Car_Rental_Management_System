# GitHub 上传前安全检查脚本
# 使用方法：在 PowerShell 中运行：.\check_before_upload.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub 上传前安全检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$hasError = $false

# 1. 检查 .gitignore 文件
Write-Host "[1/5] 检查 .gitignore 文件..." -ForegroundColor Yellow
if (Test-Path .gitignore) {
    Write-Host "  ✅ .gitignore 文件存在" -ForegroundColor Green
    $gitignoreContent = Get-Content .gitignore -Raw
    if ($gitignoreContent -match "db\.sqlite3|\.db|\.sqlite") {
        Write-Host "  ✅ .gitignore 包含数据库文件规则" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 警告：.gitignore 可能缺少数据库文件规则" -ForegroundColor Red
        $hasError = $true
    }
} else {
    Write-Host "  ❌ 错误：.gitignore 文件不存在！" -ForegroundColor Red
    Write-Host "  请先创建 .gitignore 文件" -ForegroundColor Yellow
    $hasError = $true
}
Write-Host ""

# 2. 检查数据库文件是否被跟踪
Write-Host "[2/5] 检查数据库文件..." -ForegroundColor Yellow
$dbFiles = git ls-files 2>$null | Select-String -Pattern "\.(db|sqlite3|sqlite)$"
if ($dbFiles) {
    Write-Host "  ❌ 警告：发现数据库文件被 Git 跟踪！" -ForegroundColor Red
    Write-Host "  以下文件将被上传（危险！）：" -ForegroundColor Red
    $dbFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  解决方法：" -ForegroundColor Yellow
    Write-Host "    git rm --cached db.sqlite3" -ForegroundColor Cyan
    Write-Host "    git add .gitignore" -ForegroundColor Cyan
    Write-Host "    git commit -m 'Remove database file from tracking'" -ForegroundColor Cyan
    $hasError = $true
} else {
    Write-Host "  ✅ 数据库文件未被跟踪（安全）" -ForegroundColor Green
}
Write-Host ""

# 3. 检查敏感配置文件
Write-Host "[3/5] 检查敏感配置文件..." -ForegroundColor Yellow
$configFiles = git ls-files 2>$null | Select-String -Pattern "(local_settings\.py|\.env)$"
if ($configFiles) {
    Write-Host "  ❌ 警告：发现敏感配置文件被跟踪！" -ForegroundColor Red
    $configFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  解决方法：" -ForegroundColor Yellow
    Write-Host "    git rm --cached local_settings.py" -ForegroundColor Cyan
    $hasError = $true
} else {
    Write-Host "  ✅ 敏感配置文件未被跟踪（安全）" -ForegroundColor Green
}
Write-Host ""

# 4. 检查本地是否有数据库文件
Write-Host "[4/5] 检查本地数据库文件..." -ForegroundColor Yellow
$localDbFiles = Get-ChildItem -Path . -Filter "*.sqlite3" -ErrorAction SilentlyContinue
if ($localDbFiles) {
    Write-Host "  ⚠️  发现本地数据库文件（这是正常的）" -ForegroundColor Yellow
    $localDbFiles | ForEach-Object { 
        Write-Host "    - $($_.Name) (大小: $([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Yellow 
    }
    Write-Host "  ✅ 这些文件已经在 .gitignore 中，不会被上传" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  未发现本地数据库文件" -ForegroundColor Gray
}
Write-Host ""

# 5. 查看将要提交的文件概览
Write-Host "[5/5] 查看将要提交的文件..." -ForegroundColor Yellow
$status = git status --short 2>$null
if ($status) {
    Write-Host "  将要提交的文件：" -ForegroundColor Cyan
    $status | Select-Object -First 20 | ForEach-Object {
        $line = $_
        if ($line -match "^\?\?") {
            Write-Host "    [新增] $($line.Substring(3))" -ForegroundColor Green
        } elseif ($line -match "^M") {
            Write-Host "    [修改] $($line.Substring(3))" -ForegroundColor Yellow
        } else {
            Write-Host "    $line" -ForegroundColor Gray
        }
    }
    $totalCount = ($status | Measure-Object).Count
    if ($totalCount -gt 20) {
        Write-Host "    ... 还有 $($totalCount - 20) 个文件" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  总文件数: $totalCount" -ForegroundColor Cyan
} else {
    Write-Host "  ℹ️  没有待提交的文件" -ForegroundColor Gray
}
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
if ($hasError) {
    Write-Host "  ❌ 检查未通过，请修复上述问题后再上传！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "  ✅ 安全检查通过，可以安全上传到 GitHub！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步操作：" -ForegroundColor Cyan
    Write-Host "  1. git add ." -ForegroundColor Yellow
    Write-Host "  2. git commit -m 'Your commit message'" -ForegroundColor Yellow
    Write-Host "  3. git push" -ForegroundColor Yellow
    exit 0
}

