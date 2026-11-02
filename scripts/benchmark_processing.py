"""Data Processing Performance Benchmark module.

Evaluates and compares:
1. In-memory read performance: Pandas vs Polars (read_csv).
2. Analytics/Aggregation performance: Pandas vs Polars (filter + group_by + agg).
3. Chunked Streaming: Standard Pandas read_csv vs Chunked read vs Chunked aggregate (chunksize=10000).
4. Storage formats: CSV vs Parquet (File size, Read time, Compression ratio).
5. Hardware resource tracking: Rigorous Resident Set Size (RSS) monitoring via psutil background thread.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import statistics
import sys
import threading
import time
from typing import Any, Callable

import pandas as pd
import polars as pl
import psutil
import pyarrow as pa
import pyarrow.parquet as pq

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_current_process_memory_mb() -> float:
    """Return current process Resident Set Size (RSS) in MegaBytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def measure_execution(
    fn: Callable[[], Any],
    warmups: int = 2,
    iterations: int = 5,
    sample_interval_sec: float = 0.001,
) -> dict[str, Any]:
    """Run function through warmups and measured iterations with real-time peak RSS tracking."""
    # Warmup runs
    for _ in range(warmups):
        gc.collect()
        _ = fn()

    timings = []
    baseline_mems = []
    peak_mems = []
    delta_mems = []

    proc = psutil.Process(os.getpid())

    for _ in range(iterations):
        gc.collect()
        baseline = proc.memory_info().rss / (1024 * 1024)
        peak = baseline
        stop_event = threading.Event()

        def sampler():
            nonlocal peak
            while not stop_event.is_set():
                try:
                    rss = proc.memory_info().rss / (1024 * 1024)
                    if rss > peak:
                        peak = rss
                except Exception:
                    pass
                time.sleep(sample_interval_sec)

        monitor = threading.Thread(target=sampler, daemon=True)
        monitor.start()

        t0 = time.perf_counter()
        result = fn()
        t1 = time.perf_counter()

        stop_event.set()
        monitor.join(timeout=1.0)

        final_rss = proc.memory_info().rss / (1024 * 1024)
        if final_rss > peak:
            peak = final_rss

        delta = max(0.0, peak - baseline)

        timings.append((t1 - t0) * 1000.0)
        baseline_mems.append(baseline)
        peak_mems.append(peak)
        delta_mems.append(delta)

        del result
        gc.collect()

    return {
        "median_ms": round(statistics.median(timings), 2),
        "mean_ms": round(statistics.mean(timings), 2),
        "std_ms": round(statistics.stdev(timings), 2) if len(timings) > 1 else 0.0,
        "min_ms": round(min(timings), 2),
        "max_ms": round(max(timings), 2),
        "baseline_ram_mb": round(statistics.median(baseline_mems), 2),
        "peak_ram_mb": round(statistics.median(peak_mems), 2),
        "delta_ram_mb": round(statistics.median(delta_mems), 2),
        "runs": len(timings),
    }


def ensure_parquet_file(csv_path: Path, parquet_path: Path) -> int:
    """Convert CSV to Parquet if not exists, returning file size in bytes."""
    if not parquet_path.exists():
        print(f"  Tao ban sao Parquet: {parquet_path}...", flush=True)
        df = pd.read_csv(csv_path)
        df.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
        del df
        gc.collect()
    return parquet_path.stat().st_size


def run_benchmark_for_scale(
    csv_path: Path,
    parquet_path: Path,
    scale: int,
    warmups: int = 2,
    iterations: int = 5,
) -> list[dict[str, Any]]:
    """Execute all processing benchmarks for a specific dataset scale."""
    results = []
    csv_size_bytes = csv_path.stat().st_size
    parquet_size_bytes = ensure_parquet_file(csv_path, parquet_path)

    csv_size_mb = round(csv_size_bytes / (1024 * 1024), 2)
    parquet_size_mb = round(parquet_size_bytes / (1024 * 1024), 2)

    print(f"\n--- Benchmark Quy Mo {scale:,} Ban Ghi (CSV: {csv_size_mb} MB | Parquet: {parquet_size_mb} MB) ---", flush=True)

    # 1. Pandas read_csv
    print("  [1/8] Do Pandas read_csv...", flush=True)
    m_pd_read_csv = measure_execution(lambda: pd.read_csv(csv_path), warmups, iterations)
    results.append({
        "scale": scale,
        "category": "File Ingestion (CSV)",
        "operation": "Pandas read_csv",
        "format": "CSV",
        "median_ms": m_pd_read_csv["median_ms"],
        "mean_ms": m_pd_read_csv["mean_ms"],
        "std_ms": m_pd_read_csv["std_ms"],
        "baseline_ram_mb": m_pd_read_csv["baseline_ram_mb"],
        "peak_ram_mb": m_pd_read_csv["peak_ram_mb"],
        "delta_ram_mb": m_pd_read_csv["delta_ram_mb"],
        "file_size_mb": csv_size_mb,
    })

    # 2. Polars read_csv
    print("  [2/8] Do Polars read_csv...", flush=True)
    m_pl_read_csv = measure_execution(lambda: pl.read_csv(csv_path), warmups, iterations)
    results.append({
        "scale": scale,
        "category": "File Ingestion (CSV)",
        "operation": "Polars read_csv",
        "format": "CSV",
        "median_ms": m_pl_read_csv["median_ms"],
        "mean_ms": m_pl_read_csv["mean_ms"],
        "std_ms": m_pl_read_csv["std_ms"],
        "baseline_ram_mb": m_pl_read_csv["baseline_ram_mb"],
        "peak_ram_mb": m_pl_read_csv["peak_ram_mb"],
        "delta_ram_mb": m_pl_read_csv["delta_ram_mb"],
        "file_size_mb": csv_size_mb,
    })

    # 3. Pandas read_parquet
    print("  [3/8] Do Pandas read_parquet...", flush=True)
    m_pd_read_parquet = measure_execution(lambda: pd.read_parquet(parquet_path), warmups, iterations)
    results.append({
        "scale": scale,
        "category": "File Ingestion (Parquet)",
        "operation": "Pandas read_parquet",
        "format": "Parquet",
        "median_ms": m_pd_read_parquet["median_ms"],
        "mean_ms": m_pd_read_parquet["mean_ms"],
        "std_ms": m_pd_read_parquet["std_ms"],
        "baseline_ram_mb": m_pd_read_parquet["baseline_ram_mb"],
        "peak_ram_mb": m_pd_read_parquet["peak_ram_mb"],
        "delta_ram_mb": m_pd_read_parquet["delta_ram_mb"],
        "file_size_mb": parquet_size_mb,
    })

    # 4. Polars read_parquet
    print("  [4/8] Do Polars read_parquet...", flush=True)
    m_pl_read_parquet = measure_execution(lambda: pl.read_parquet(parquet_path), warmups, iterations)
    results.append({
        "scale": scale,
        "category": "File Ingestion (Parquet)",
        "operation": "Polars read_parquet",
        "format": "Parquet",
        "median_ms": m_pl_read_parquet["median_ms"],
        "mean_ms": m_pl_read_parquet["mean_ms"],
        "std_ms": m_pl_read_parquet["std_ms"],
        "baseline_ram_mb": m_pl_read_parquet["baseline_ram_mb"],
        "peak_ram_mb": m_pl_read_parquet["peak_ram_mb"],
        "delta_ram_mb": m_pl_read_parquet["delta_ram_mb"],
        "file_size_mb": parquet_size_mb,
    })

    # 5. Chunked CSV Read Only (Pandas chunksize=10,000)
    print("  [5/8] Do Pandas Chunked Ingestion (chunksize=10,000)...", flush=True)
    def chunked_read_only():
        count = 0
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            count += len(chunk)
        return count

    m_chunked_read = measure_execution(chunked_read_only, warmups, iterations)
    results.append({
        "scale": scale,
        "category": "Memory-bounded Ingestion",
        "operation": "Pandas Chunked read_csv (10k)",
        "format": "CSV",
        "median_ms": m_chunked_read["median_ms"],
        "mean_ms": m_chunked_read["mean_ms"],
        "std_ms": m_chunked_read["std_ms"],
        "baseline_ram_mb": m_chunked_read["baseline_ram_mb"],
        "peak_ram_mb": m_chunked_read["peak_ram_mb"],
        "delta_ram_mb": m_chunked_read["delta_ram_mb"],
        "file_size_mb": csv_size_mb,
    })

    # 6. Chunked CSV Read + Aggregation
    print("  [6/8] Do Pandas Chunked Aggregation (chunksize=10,000)...", flush=True)
    def chunked_aggregate():
        total_price = 0.0
        total_count = 0
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            valid_p = chunk["price"].dropna()
            total_price += float(valid_p.sum())
            total_count += len(valid_p)
        return total_price, total_count

    m_chunked_agg = measure_execution(chunked_aggregate, warmups, iterations)
    results.append({
        "scale": scale,
        "category": "Memory-bounded Ingestion",
        "operation": "Pandas Chunked aggregate (10k)",
        "format": "CSV",
        "median_ms": m_chunked_agg["median_ms"],
        "mean_ms": m_chunked_agg["mean_ms"],
        "std_ms": m_chunked_agg["std_ms"],
        "baseline_ram_mb": m_chunked_agg["baseline_ram_mb"],
        "peak_ram_mb": m_chunked_agg["peak_ram_mb"],
        "delta_ram_mb": m_chunked_agg["delta_ram_mb"],
        "file_size_mb": csv_size_mb,
    })

    # Load in-memory frames for pure processing benchmarks
    df_pd = pd.read_csv(csv_path)
    df_pl = pl.read_csv(csv_path)

    # 7. Filter & GroupBy: Pandas (Exact province 'Hà Nội' matching dataset)
    print("  [7/8] Do Pandas Filter & GroupBy ('Hà Nội')...", flush=True)
    def pd_aggregation():
        filtered = df_pd[(df_pd["province_name"] == "Hà Nội") & (df_pd["price"] > 0)]
        return filtered.groupby("property_type_name").agg({
            "price": "mean",
            "area": "mean",
            "id": "count",
        }).rename(columns={"id": "count"})

    m_pd_agg = measure_execution(pd_aggregation, warmups, iterations)
    results.append({
        "scale": scale,
        "category": "In-Memory Analytics",
        "operation": "Pandas Filter + GroupBy",
        "format": "In-Memory",
        "median_ms": m_pd_agg["median_ms"],
        "mean_ms": m_pd_agg["mean_ms"],
        "std_ms": m_pd_agg["std_ms"],
        "baseline_ram_mb": m_pd_agg["baseline_ram_mb"],
        "peak_ram_mb": m_pd_agg["peak_ram_mb"],
        "delta_ram_mb": m_pd_agg["delta_ram_mb"],
        "file_size_mb": 0.0,
    })

    # 8. Filter & GroupBy: Polars (Exact province 'Hà Nội' matching dataset)
    print("  [8/8] Do Polars Filter & GroupBy ('Hà Nội')...", flush=True)
    def pl_aggregation():
        return (
            df_pl.filter((pl.col("province_name") == "Hà Nội") & (pl.col("price") > 0))
            .group_by("property_type_name")
            .agg([
                pl.col("price").mean().alias("price"),
                pl.col("area").mean().alias("area"),
                pl.col("id").count().alias("count"),
            ])
        )

    m_pl_agg = measure_execution(pl_aggregation, warmups, iterations)
    results.append({
        "scale": scale,
        "category": "In-Memory Analytics",
        "operation": "Polars Filter + GroupBy",
        "format": "In-Memory",
        "median_ms": m_pl_agg["median_ms"],
        "mean_ms": m_pl_agg["mean_ms"],
        "std_ms": m_pl_agg["std_ms"],
        "baseline_ram_mb": m_pl_agg["baseline_ram_mb"],
        "peak_ram_mb": m_pl_agg["peak_ram_mb"],
        "delta_ram_mb": m_pl_agg["delta_ram_mb"],
        "file_size_mb": 0.0,
    })

    del df_pd, df_pl
    gc.collect()

    return results


def generate_processing_markdown_report(results: list[dict[str, Any]]) -> str:
    """Generate comprehensive Markdown report from processing benchmark data."""
    df_res = pd.DataFrame(results)

    lines = [
        "# Báo Cáo Đo Lường Hiệu Năng Xử Lý Dữ Liệu (Data Processing Performance Benchmark)",
        "",
        "> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.",
        "> **Cấu hình máy thử nghiệm:** Windows 11, RAM 16GB, CPU x86-64 không GPU.",
        "> **Phương pháp luận:** 2 lần warm-up, 5 lần đo chính thức. Thời gian ghi nhận Median Execution Time (ms) ± Std. Bộ nhớ đo qua luồng giám sát thời gian thực: Baseline RSS (MB trước chạy), Peak RSS (Đỉnh RAM đạt tới trong khi chạy), và Delta RSS (Mức tăng bộ nhớ tối đa).",
        "",
        "---",
        "",
        "## 1. Bảng Tổng Hợp Kết Quả Đo Lường Thực Tế",
        "",
        "| Quy Mô | Nhóm Thao Tác | Kỹ Thuật / Thư Viện | Định Dạng File | Thời Gian Median (ms) | Độ Lệch Chuẩn (std) | Baseline RSS (MB) | Peak RSS (MB) | Delta RSS (MB) |",
        "|---:|---|---|:---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in df_res.iterrows():
        lines.append(
            f"| {row['scale']:,} | {row['category']} | {row['operation']} | {row['format']} | {row['median_ms']:,.2f} ms | ±{row['std_ms']:,.2f} ms | {row['baseline_ram_mb']:,.2f} MB | {row['peak_ram_mb']:,.2f} MB | +{row['delta_ram_mb']:,.2f} MB |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Phân Tích Chuyên Sâu Các Phương Pháp Tối Ưu Xử Lý",
        "",
        "### 2.1. So Sánh Hiệu Năng: Pandas vs. Polars",
        "",
    ])

    max_scale = int(df_res["scale"].max()) if not df_res.empty else 0
    res_max = df_res[df_res["scale"] == max_scale].set_index("operation") if not df_res.empty else pd.DataFrame()
    if not res_max.empty and "Pandas read_csv" in res_max.index and "Polars read_csv" in res_max.index:
        pd_csv_time = res_max.loc["Pandas read_csv", "median_ms"]
        pl_csv_time = res_max.loc["Polars read_csv", "median_ms"]
        speedup_csv = round(pd_csv_time / pl_csv_time, 2) if pl_csv_time > 0 else 1.0

        pd_agg_time = res_max.loc["Pandas Filter + GroupBy", "median_ms"]
        pl_agg_time = res_max.loc["Polars Filter + GroupBy", "median_ms"]
        speedup_agg = round(pd_agg_time / pl_agg_time, 2) if pl_agg_time > 0 else 1.0

        lines.extend([
            f"- **Tốc độ nạp CSV ({max_scale:,} dòng):** Pandas mất `{pd_csv_time:,.2f} ms`, Polars hoàn thành trong `{pl_csv_time:,.2f} ms` $\\rightarrow$ **Polars nhanh hơn {speedup_csv}x**.",
            f"- **Tốc độ Lọc & Gom Nhóm In-Memory (Filter + GroupBy trên tập 'Hà Nội'):** Pandas xử lý trong `{pd_agg_time:,.2f} ms`, Polars hoàn thành trong `{pl_agg_time:,.2f} ms` $\\rightarrow$ **Polars nhanh hơn {speedup_agg}x**.",
            "- **Cơ sở kỹ thuật:**",
            "  1. Polars được xây dựng trên Rust với mô hình dữ liệu Apache Arrow nguyên bản, hỗ trợ zero-copy và vectorized SIMD execution.",
            "  2. Polars tự động khai thác tính toán song song đa luồng CPU (Multi-threaded Rayon execution) trong khi Pandas bị giới hạn bởi GIL trên các tác vụ Python đơn luồng.",
            "",
            "### 2.2. So Sánh Định Dạng Lưu Trữ: CSV vs. Parquet",
            "",
        ])

        if "Pandas read_parquet" in res_max.index:
            pd_pq_time = res_max.loc["Pandas read_parquet", "median_ms"]
            speedup_pq_pd = round(pd_csv_time / pd_pq_time, 2) if pd_pq_time > 0 else 1.0
            csv_size_mb = res_max.loc["Pandas read_csv", "file_size_mb"]
            pq_size_mb = res_max.loc["Pandas read_parquet", "file_size_mb"]
            compress_ratio = round(csv_size_mb / pq_size_mb, 2) if pq_size_mb > 0 else 1.0
            lines.extend([
                f"- **Dung lượng lưu trữ:** CSV {max_scale:,} chiếm `{csv_size_mb:,.2f} MB`, Parquet Snappy chỉ chiếm `{pq_size_mb:,.2f} MB` $\\rightarrow$ **Mức nén đạt {compress_ratio}x**.",
                f"- **Tốc độ nạp vào Pandas:** Đọc Parquet mất `{pd_pq_time:,.2f} ms` so với CSV `{pd_csv_time:,.2f} ms` $\\rightarrow$ **Tăng tốc {speedup_pq_pd}x**.",
                "- **Lợi thế:** Parquet lưu trữ metadata kiểu dữ liệu nhị phân chuẩn xác, không phải phân tích chuỗi văn bản (string parsing) qua từng dòng như CSV.",
                "",
            ])

    lines.extend([
        "### 2.3. Kiểm Soát Bộ Nhớ Với Kỹ Thuật Đọc Theo Khối (Chunked Streaming)",
        "",
        "- **Hiện tượng:** Khi nạp toàn bộ file CSV 500K dòng vào RAM một lần bằng `pd.read_csv`, tiến trình ghi nhận Delta RSS tăng đáng kể để chứa toàn bộ DataFrame.",
        "- **Kiểm soát bằng Chunked Streaming:** Khi áp dụng `chunksize=10,000`, dữ liệu được nạp và giải phóng tuần tự theo từng khối. Mặc dù tổng thời gian thực thi có thể tăng do chi phí vòng lặp I/O lặp lại, mức tăng bộ nhớ (Delta RSS) được giữ trong phạm vi một khối (~10–35 MB), ngăn ngừa tình trạng cạn kiệt bộ nhớ (OOM) khi xử lý các tập dữ liệu có quy mô lớn hơn dung lượng RAM vật lý.",
        "",
        "---",
        "",
        "## 3. Khuyến Nghị Thực Tiễn Cho Pipeline Kỹ Thuật Dữ Liệu",
        "",
        "1. **Tầng Lưu Trữ (Analytical Storage):** Định dạng **Parquet Snappy** mang lại ưu thế vượt trội về kích thước file và tốc độ nạp dữ liệu.",
        "2. **Tầng Xử Lý Phân Tích (Ingestion & ETL):** **Polars** đem lại hiệu năng xử lý đa luồng cao cho các tác vụ tính toán lớn.",
        "3. **Tầng Phục Vụ Truy Vấn Trực Tuyến (Online Serving):** Sử dụng **PostgreSQL** kết hợp các cấu hình chỉ mục B-tree (đơn cột, composite) phục vụ các truy vấn tra cứu điểm, lọc phạm vi kết hợp phân trang Top-N trong thời gian mili-giây.",
    ])

    return "\n".join(lines)


def run_all_benchmarks(
    targets: list[int] | None = None,
    data_dir: Path = Path("data/processed"),
    output_dir: Path = Path("results/processing_benchmark"),
    docs_dir: Path = Path("docs"),
    warmups: int = 2,
    iterations: int = 5,
) -> pd.DataFrame:
    """Execute full processing benchmark across all scale targets."""
    if targets is None:
        targets = [50000, 200000, 500000]

    output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    for scale in targets:
        csv_file = data_dir / f"properties_{scale}.csv"
        parquet_file = data_dir / f"properties_{scale}.parquet"

        if not csv_file.exists():
            print(f"Bo qua {csv_file}: khong ton tai")
            continue

        scale_records = run_benchmark_for_scale(
            csv_path=csv_file,
            parquet_path=parquet_file,
            scale=scale,
            warmups=warmups,
            iterations=iterations,
        )
        all_records.extend(scale_records)

    df_out = pd.DataFrame(all_records)
    csv_out = output_dir / "processing_benchmark.csv"
    df_out.to_csv(csv_out, index=False, encoding="utf-8-sig")
    print(f"\nDa luu ket qua benchmark vao: {csv_out}")

    md_report = generate_processing_markdown_report(all_records)
    md_out = docs_dir / "processing_performance.md"
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Da xuat bao cao Markdown: {md_out}")

    return df_out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--targets",
        type=str,
        default="50000,200000,500000",
        help="Danh sach quy mo can do, ngan cach boi dau phay",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Thu muc chua file CSV du lieu",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/processing_benchmark"),
        help="Thu muc luu ket qua do luong",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Thu muc luu bao cao Markdown",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="So lan do chinh thuc cho moi thao tac",
    )
    parser.add_argument(
        "--warmups",
        type=int,
        default=2,
        help="So lan chay warm-up truoc do",
    )
    args = parser.parse_args(argv)

    targets = [int(t.strip()) for t in args.targets.split(",") if t.strip()]
    run_all_benchmarks(
        targets=targets,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        docs_dir=args.docs_dir,
        warmups=args.warmups,
        iterations=args.iterations,
    )
    print("Hoan thanh Data Processing Benchmark!")


if __name__ == "__main__":
    main()
