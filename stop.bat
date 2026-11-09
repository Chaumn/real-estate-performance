@echo off
chcp 65001 >nul
title Stop PostgreSQL
cd /d "%~dp0"

echo [*] Đang dừng PostgreSQL (Port 5433)...
python scripts\stop_db.py
echo [+] Đã dừng PostgreSQL an toàn.
timeout /t 3 >nul

