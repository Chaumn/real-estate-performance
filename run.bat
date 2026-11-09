@echo off
chcp 65001 >nul
title Real Estate Performance Optimization Dashboard
cd /d "%~dp0"

echo ======================================================================
echo    ĐỒ ÁN: TỐI ƯU HIỆU NĂNG CƠ SỞ DỮ LIỆU POSTGRESQL (IDS - PTIT)
echo    Đề tài: Xây dựng bộ dữ liệu BĐS, tối ưu hệ thống khi dữ liệu quá lớn
echo ======================================================================
echo.

:: 1. Kiểm tra và khởi động PostgreSQL trên cổng 5433
echo [*] Đang kiểm tra và khởi động PostgreSQL (Port 5433)...
python scripts\start_db.py
if errorlevel 1 (
    echo [-] Khởi động PostgreSQL thất bại. Vui lòng kiểm tra lại.
    pause
    exit /b 1
)
echo.

:: 2. Khởi chạy Web Dashboard trực tiếp
echo [*] Đang mở Web Dashboard tại http://localhost:8000 ...
echo [*] Nhấn Ctrl+C trong cửa sổ này khi bạn muốn dừng hệ thống.
echo.
python -m scripts.dashboard --port 8000 --open

:: 3. Tự động dừng PostgreSQL khi đóng Dashboard
echo.
echo [*] Đang dừng PostgreSQL...
python scripts\stop_db.py
echo [+] Đã dừng hệ thống an toàn.
pause
