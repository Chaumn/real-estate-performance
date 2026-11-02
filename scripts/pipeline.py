"""Unified Orchestration Pipeline for Real Estate Performance Project.

Provides a unified interface to:
1. Verify system prerequisites and environment (.env, PostgreSQL, Python packages).
2. Build 50K, 200K, 500K datasets from Hugging Face if missing.
3. Import datasets transactionally into PostgreSQL.
4. Execute automated benchmark (3 scales x 10 configs).
5. Analyze results, generate comparison charts, and produce markdown reports.
6. Serve the interactive dashboard.
"""

import argparse
import io
from pathlib import Path
import subprocess
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results" / "benchmark"


def step_check_env():
    """Verify .env file and PostgreSQL connection."""
    print("\n[BƯỚC 1/5] Kiểm tra cấu hình môi trường...", flush=True)
    env_file = PROJECT_ROOT / ".env"
    if not env_file.is_file():
        print("[-] Chưa tìm thấy file .env. Đang sao chép từ .env.example...")
        example = PROJECT_ROOT / ".env.example"
        if example.is_file():
            env_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print("[+] Đã tạo .env. Vui lòng cập nhật PGPASSWORD trong .env nếu cần.")
    
    cmd = [sys.executable, "-m", "scripts.benchmark_runner", "--check-only"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode == 0:
        print("[+] Kết nối PostgreSQL thành công!")
        return True
    else:
        print("[-] Kết nối PostgreSQL thất bại. Vui lòng kiểm tra lại .env (host, port, user, password, dbname).")
        return False


def step_build_datasets():
    """Build datasets if missing."""
    print("\n[BƯỚC 2/5] Kiểm tra dữ liệu (50K, 200K, 500K)...", flush=True)
    targets = [50000, 200000, 500000]
    missing = [t for t in targets if not (DATA_DIR / f"properties_{t}.csv").is_file()]
    if not missing:
        print("[+] Toàn bộ 3 file CSV đã tồn tại trong data/processed/.")
        return True
    
    print(f"[*] Cần tạo {len(missing)} dataset: {missing}")
    cmd = [
        sys.executable, "-X", "utf8", "-m", "scripts.build_large_dataset",
        "--targets", ",".join(str(t) for t in targets),
        "--seed", "42",
        "--batch-size", "2000",
        "--shuffle-buffer", "10000",
    ]
    print(f"[*] Thực thi: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return res.returncode == 0


def step_benchmark(runs=20, warmups=3):
    """Run benchmark runner across all 3 scales."""
    print("\n[BƯỚC 3/5] Thực thi Automated Benchmark...", flush=True)
    cmd = [
        sys.executable, "-m", "scripts.benchmark_runner",
        "--scales", "50000,200000,500000",
        "--runs", str(runs),
        "--warmups", str(warmups),
        "--auto-import",
    ]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return res.returncode == 0


def step_analyze():
    """Run results analysis and chart generator."""
    print("\n[BƯỚC 4/5] Phân tích kết quả và sinh biểu đồ...", flush=True)
    csv_file = RESULTS_DIR / "benchmark_results.csv"
    if not csv_file.is_file():
        print(f"[-] Chưa có {csv_file}. Cần chạy benchmark trước.")
        return False
    cmd = [sys.executable, "-m", "scripts.analyze_results", "--input", str(csv_file)]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return res.returncode == 0


def step_dashboard(port=8000):
    """Launch interactive dashboard."""
    print("\n[BƯỚC 5/5] Khởi động Interactive Dashboard...", flush=True)
    cmd = [sys.executable, "-m", "scripts.dashboard", "--port", str(port), "--open"]
    subprocess.run(cmd, cwd=PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=["all", "check", "build", "benchmark", "analyze", "dashboard"], default="all")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.action == "check":
        step_check_env()
    elif args.action == "build":
        step_build_datasets()
    elif args.action == "benchmark":
        step_benchmark(runs=args.runs, warmups=args.warmups)
    elif args.action == "analyze":
        step_analyze()
    elif args.action == "dashboard":
        step_dashboard(port=args.port)
    elif args.action == "all":
        if step_check_env():
            if step_build_datasets():
                if step_benchmark(runs=args.runs, warmups=args.warmups):
                    step_analyze()
                    step_dashboard(port=args.port)


if __name__ == "__main__":
    main()

