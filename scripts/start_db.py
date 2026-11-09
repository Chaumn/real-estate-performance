"""Helper script to start the project's dedicated PostgreSQL instance."""

import io
from pathlib import Path
import subprocess
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")
PG_DATA = PROJECT_ROOT / ".pgdata"
PORT = 5433


def is_running():
    cmd = [str(PG_BIN / "pg_isready.exe"), "-U", "postgres", "-h", "127.0.0.1", "-p", str(PORT)]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def start_database():
    if is_running():
        print(f"[+] PostgreSQL đã đang chạy trên cổng {PORT}.")
        return True

    print(f"[*] Đang khởi động PostgreSQL trên cổng {PORT}...", flush=True)
    if not PG_DATA.is_dir():
        print(f"[*] Khởi tạo cluster tại {PG_DATA}...", flush=True)
        init_cmd = [
            str(PG_BIN / "initdb.exe"),
            "-D", str(PG_DATA),
            "-U", "postgres",
            "-A", "trust",
            "--encoding=UTF8",
            "--locale=C",
        ]
        res = subprocess.run(init_cmd)
        if res.returncode != 0:
            print("[-] Khởi tạo cluster thất bại.")
            return False

        # Configure port
        conf_file = PG_DATA / "postgresql.conf"
        with conf_file.open("a", encoding="utf-8") as f:
            f.write(f"\nport = {PORT}\n")

    # Start postgres
    log_file = PROJECT_ROOT / "logfile"
    start_cmd = [
        str(PG_BIN / "pg_ctl.exe"),
        "-D", str(PG_DATA),
        "-l", str(log_file),
        "-o", f"-p {PORT}",
        "start",
    ]
    subprocess.run(start_cmd)

    for _ in range(10):
        time.sleep(1)
        if is_running():
            print(f"[+] PostgreSQL đã sẵn sàng trên cổng {PORT}!", flush=True)
            return True

    print("[-] Không thể khởi động PostgreSQL trong thời gian chờ.")
    return False


if __name__ == "__main__":
    if not start_database():
        sys.exit(1)

