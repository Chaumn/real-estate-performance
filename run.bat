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

:: 2. Menu tác vụ hoặc tự động mở Dashboard sau 5 giây
echo Chọn tác vụ bạn muốn thực hiện:
echo   [1] Mở Web Dashboard trực quan (Khuyến nghị xem kết quả ngay)
echo   [2] Chạy lại toàn bộ Benchmark tự động (3 quy mô x 10 cấu hình)
echo   [3] Cập nhật lại biểu đồ và báo cáo phân tích (analyze_results)
echo   [4] Chạy toàn bộ 203 Unit & Integration Tests kiểm thử hệ thống
echo   [5] Chạy quy trình Data Science (Quality, EDA, Features, Processing Benchmark)
echo   [6] Dừng dịch vụ PostgreSQL (stop_db)
echo   [0] Thoát
echo.

choice /c 1234560 /t 5 /d 1 /m "Nhập lựa chọn của bạn [1-6, 0] (Tự động mở Dashboard sau 5s): "
set opt=%errorlevel%

if "%opt%"=="1" (
    echo.
    echo [*] Đang mở Web Dashboard tại http://localhost:8000 ...
    python -m scripts.dashboard --port 8000 --open
    goto end
)

if "%opt%"=="2" (
    echo.
    echo [*] Đang chạy Benchmark tự động trên 3 quy mô (50K, 200K, 500K)...
    python -m scripts.benchmark_runner --scales 50000,200000,500000 --runs 20 --warmups 3 --auto-import
    echo [*] Đang cập nhật biểu đồ và báo cáo...
    python -m scripts.analyze_results
    echo.
    echo [+] Benchmark hoàn tất! Mở Web Dashboard xem kết quả mới...
    python -m scripts.dashboard --port 8000 --open
    goto end
)

if "%opt%"=="3" (
    echo.
    echo [*] Đang tạo lại biểu đồ khoa học và báo cáo Markdown...
    python -m scripts.analyze_results
    echo [+] Hoàn tất! Biểu đồ lưu tại thư mục: results\benchmark\analysis\
    pause
    goto end
)

if "%opt%"=="4" (
    echo.
    echo [*] Đang chạy toàn bộ 203 Unit & Integration Tests...
    python -m pytest
    pause
    goto end
)

if "%opt%"=="5" (
    echo.
    echo [*] Đang chạy toàn bộ quy trình Data Science Pipeline...
    python -m scripts.data_quality
    python -m scripts.run_eda
    python -m scripts.feature_engineering
    python -m scripts.benchmark_processing
    echo [+] Hoàn tất Data Science Pipeline! Xem kết quả tại docs/ và results/
    pause
    goto end
)

if "%opt%"=="6" (
    echo.
    python scripts\stop_db.py
    pause
    goto end
)

if "%opt%"=="7" (
    goto end
)

:end

