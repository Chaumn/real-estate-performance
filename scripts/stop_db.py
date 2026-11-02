"""Helper script to gracefully stop the project's PostgreSQL instance."""

from pathlib import Path
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")
PG_DATA = PROJECT_ROOT / ".pgdata"


def stop_database():
    print("[*] Đang dừng PostgreSQL...", flush=True)
    stop_cmd = [str(PG_BIN / "pg_ctl.exe"), "-D", str(PG_DATA), "stop", "-m", "fast"]
    res = subprocess.run(stop_cmd)
    if res.returncode == 0:
        print("[+] PostgreSQL đã dừng an toàn.")
    else:
        print("[-] Không thể dừng PostgreSQL hoặc cluster chưa chạy.")


if __name__ == "__main__":
    stop_database()

