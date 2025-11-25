@echo off
chcp 65001 >nul
echo ==========================================
echo 租车系统 - 订单自动更新工具
echo ==========================================
echo.

cd /d "%~dp0"

echo 正在执行订单状态自动更新...
echo.

python manage.py update_expired_rentals

echo.
echo ==========================================
echo 执行完成! 按任意键退出...
echo ==========================================
pause >nul
