"""Automated Benchmark Result Analysis and Scientific Visualization Module.

Reads benchmark summary CSV/JSON and automatically generates:
1. Markdown summary comparison tables across all 3 scales.
2. Speedup and Execution Time charts (matplotlib).
3. Detailed architectural breakdown for Q1, Q2, Q3 (A/B/C/D), and Q4.
4. Scan type transition and Buffer I/O analysis.
5. Index storage overhead and scalability evaluation.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_CSV = PROJECT_ROOT / "results" / "benchmark" / "benchmark_results.csv"
DEFAULT_INPUT_JSON = PROJECT_ROOT / "results" / "benchmark" / "benchmark_summary.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "benchmark" / "analysis"


def load_benchmark_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Load and parse benchmark CSV records."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Khong tim thay file ket qua: {csv_path}")
    records = []
    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "scale": int(row["scale"]),
                "query_id": row["query_id"],
                "config_id": row["config_id"],
                "dominant_scan_type": row.get("dominant_scan_type", ""),
                "indexes_used": row.get("indexes_used", ""),
                "index_size_mb": float(row.get("index_size_mb", 0.0) or 0.0),
                "execution_time_median_ms": float(row["execution_time_median_ms"]),
                "execution_time_iqr_ms": float(row.get("execution_time_iqr_ms", 0.0) or 0.0),
                "execution_time_min_ms": float(row.get("execution_time_min_ms", 0.0) or 0.0),
                "execution_time_max_ms": float(row.get("execution_time_max_ms", 0.0) or 0.0),
                "planning_time_median_ms": float(row.get("planning_time_median_ms", 0.0) or 0.0),
                "shared_hit_blocks_median": float(row.get("shared_hit_blocks_median", 0.0) or 0.0),
                "shared_read_blocks_median": float(row.get("shared_read_blocks_median", 0.0) or 0.0),
                "speedup": float(row.get("speedup", 1.0) or 1.0),
            })
    return records


def generate_markdown_report(records: List[Dict[str, Any]], output_path: Path) -> str:
    """Generate comprehensive scientific analysis in GitHub-flavored Markdown."""
    scales = sorted(set(r["scale"] for r in records))
    configs_by_scale: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for r in records:
        configs_by_scale.setdefault(r["scale"], {})[r["config_id"]] = r

    lines = [
        "# Báo Cáo Phân Tích Thực Nghiệm Tối Ưu Hiệu Năng PostgreSQL",
        "",
        "## 1. Tổng quan thí nghiệm",
        "",
        "- **Hệ quản trị CSDL:** PostgreSQL 18.3 (x86_64-windows)",
        f"- **Quy mô dữ liệu kiểm thử:** {', '.join(f'{s:,}' for s in scales)} bản ghi",
        "- **Chính sách đo lường:** Warm-up 3 lần + 20 lần đo tuần tự, lấy **Median Execution Time** làm chỉ số trọng tâm.",
        "- **Số cấu hình kiểm thử:** 10 cấu hình độc lập (Q1: 2, Q2: 2, Q3: 4, Q4: 2).",
        "",
        "---",
        "",
        "## 2. Bảng kết quả tổng hợp chi tiết",
        "",
        "| Scale | Config ID | Query | Scan Type | Index Used | Index (MB) | Median Exec (ms) | IQR (ms) | Speedup | Shared Hit Blk |",
        "| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for scale in scales:
        scale_records = [r for r in records if r["scale"] == scale]
        for r in scale_records:
            lines.append(
                f"| {r['scale']:,} | `{r['config_id']}` | {r['query_id']} | "
                f"{r['dominant_scan_type']} | {r['indexes_used'] or 'None'} | "
                f"{r['index_size_mb']:.2f} | {r['execution_time_median_ms']:.3f} | "
                f"{r['execution_time_iqr_ms']:.3f} | **{r['speedup']:.2f}x** | "
                f"{r['shared_hit_blocks_median']:.0f} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Phân tích chi tiết từng bài toán tối ưu",
        "",
        "### 3.1. Q1 — Single-column Index (Tìm theo tỉnh/thành phố)",
        "",
        "- **Truy vấn:** Lọc các bất động sản tại `'Hải Phòng'`.",
        "- **Cơ chế:**",
        "  - *Baseline:* Thực hiện `Seq Scan` toàn bộ bảng `public.properties`. Chi phí và thời gian thực thi tăng tuyến tính theo số lượng bản ghi.",
        "  - *Indexed (`idx_properties_province_name`):* PostgreSQL chuyển sang `Bitmap Heap Scan` hoặc `Index Scan`. Chỉ cần đọc các block chứa con trỏ hàng tương ứng.",
        "- **Đánh giá hiệu năng:**",
    ])

    for scale in scales:
        base = configs_by_scale.get(scale, {}).get("Q1_baseline")
        opt = configs_by_scale.get(scale, {}).get("Q1_indexed")
        if base and opt:
            lines.append(
                f"  - **{scale:,} dòng:** Baseline `{base['execution_time_median_ms']:.2f} ms` -> Indexed `{opt['execution_time_median_ms']:.2f} ms` "
                f"(Speedup: **{opt['speedup']:.2f}x**, Dung lượng Index: `{opt['index_size_mb']:.2f} MB`)."
            )

    lines.extend([
        "",
        "### 3.2. Q2 — Composite Index (Bộ lọc kết hợp vị trí, khoảng giá, sắp xếp và LIMIT)",
        "",
        "- **Truy vấn:** Tìm 20 BĐS giá thấp nhất tại Hà Nội, Cầu Giấy trong khoảng 4.1 tỷ - 14.3 tỷ.",
        "- **Cơ chế:**",
        "  - *Baseline:* Phải quét toàn bộ bảng (`Seq Scan`), lọc các dòng thỏa mãn, sau đó sắp xếp trong bộ nhớ (`Sort` top-N heapsort) rồi lấy 20 dòng đầu.",
        "  - *Indexed (`idx_properties_location_price`):* Index bao phủ thứ tự `(province_name, district_name, price, id)`. Planner sử dụng `Index Scan` duyệt trực tiếp cây B-tree theo đúng thứ tự sắp xếp và **dừng ngay khi đủ 20 dòng (early exit)**.",
        "- **Đánh giá hiệu năng:** Tốc độ tăng vượt bậc (thường đạt hàng chục đến hàng trăm lần) do triệt tiêu hoàn toàn chi phí quét bảng và chi phí sắp xếp.",
    ])

    for scale in scales:
        base = configs_by_scale.get(scale, {}).get("Q2_baseline")
        opt = configs_by_scale.get(scale, {}).get("Q2_indexed")
        if base and opt:
            lines.append(
                f"  - **{scale:,} dòng:** Baseline `{base['execution_time_median_ms']:.2f} ms` -> Indexed `{opt['execution_time_median_ms']:.2f} ms` "
                f"(Speedup: **{opt['speedup']:.2f}x**)."
            )

    lines.extend([
        "",
        "### 3.3. Q3 — Tác động độc lập của Query Rewriting và Indexing (Sargability)",
        "",
        "- **Thực nghiệm 4 cấu hình:**",
        "  - **A (Original, No Index):** `WHERE published_at::date = DATE '2025-10-15'` -> `Seq Scan`.",
        "  - **B (Rewritten, No Index):** `WHERE published_at >= TIMESTAMP '...' AND published_at < TIMESTAMP '...'` -> `Seq Scan`. Viết lại query khi không có Index không làm giảm thời gian quét bảng đáng kể.",
        "  - **C (Original, With Index):** Giữ nguyên hàm ép kiểu `::date`. Dù có Index `idx_properties_published_at`, B-tree index **KHÔNG THỂ SỬ DỤNG** do biểu thức áp dụng trên cột (non-sargable predicate). Planner buộc phải `Seq Scan`.",
        "  - **D (Rewritten, With Index):** Khoảng thời gian nửa mở giúp biểu thức trở thành sargable predicate. Planner lập tức chuyển sang `Bitmap Index Scan` / `Index Scan`, đem lại tốc độ tối đa.",
        "- **Bảng phân rã hiệu năng Q3:**",
        "",
        "| Scale | A: Orig NoIdx | B: Rewrite NoIdx | C: Orig WithIdx | D: Rewrite WithIdx | Speedup B vs A | Speedup C vs A | Speedup D vs A |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for scale in scales:
        qa = configs_by_scale.get(scale, {}).get("Q3_A")
        qb = configs_by_scale.get(scale, {}).get("Q3_B")
        qc = configs_by_scale.get(scale, {}).get("Q3_C")
        qd = configs_by_scale.get(scale, {}).get("Q3_D")
        if qa and qb and qc and qd:
            sp_b = qa["execution_time_median_ms"] / qb["execution_time_median_ms"] if qb["execution_time_median_ms"] > 0 else 1.0
            sp_c = qa["execution_time_median_ms"] / qc["execution_time_median_ms"] if qc["execution_time_median_ms"] > 0 else 1.0
            sp_d = qa["execution_time_median_ms"] / qd["execution_time_median_ms"] if qd["execution_time_median_ms"] > 0 else 1.0
            lines.append(
                f"| {scale:,} | {qa['execution_time_median_ms']:.2f} ms | {qb['execution_time_median_ms']:.2f} ms | "
                f"{qc['execution_time_median_ms']:.2f} ms | {qd['execution_time_median_ms']:.2f} ms | "
                f"{sp_b:.2f}x | {sp_c:.2f}x | **{sp_d:.2f}x** |"
            )

    lines.extend([
        "",
        "### 3.4. Q4 — Aggregation Control (Trường hợp đối chứng - Index không cải thiện)",
        "",
        "- **Truy vấn:** `GROUP BY property_type_name, COUNT(*), ROUND(AVG(price), 0)`.",
        "- **Cơ chế:**",
        "  - Truy vấn yêu cầu tổng hợp **toàn bộ dữ liệu trong bảng**.",
        "  - Ngay cả khi tạo Index trên `property_type_name`, để tính `AVG(price)`, PostgreSQL vẫn cần truy cập toàn bộ các hàng trong bảng để đọc cột `price`.",
        "  - Việc duyệt qua Index sau đó đọc từng dòng Heap ngẫu nhiên (Random I/O) kém hiệu quả hơn nhiều so với việc quét tuần tự toàn bảng (`Seq Scan`) kết hợp giải thuật gom nhóm băm (`HashAggregate`).",
        "- **Kết luận quan trọng:** Index không phải lúc nào cũng nhanh hơn. Với truy vấn aggregate toàn bảng không có WHERE chọn lọc, Index B-tree đơn cột không mang lại lợi ích và planner thường bỏ qua hoặc nếu dùng sẽ gây suy giảm hiệu năng.",
    ])

    for scale in scales:
        base = configs_by_scale.get(scale, {}).get("Q4_baseline")
        opt = configs_by_scale.get(scale, {}).get("Q4_indexed")
        if base and opt:
            lines.append(
                f"  - **{scale:,} dòng:** Baseline `{base['execution_time_median_ms']:.2f} ms` ({base['dominant_scan_type']}) vs "
                f"Indexed `{opt['execution_time_median_ms']:.2f} ms` ({opt['dominant_scan_type']}) -> Speedup: **{opt['speedup']:.2f}x**."
            )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Phân tích chi phí lưu trữ (Storage Overhead)",
        "",
        "| Index Name | Áp dụng cho | Cột | Dung lượng tại 50K | Dung lượng tại 200K | Dung lượng tại 500K |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |",
    ])

    idx_map = [
        ("idx_properties_province_name", "Q1", "(province_name)"),
        ("idx_properties_location_price", "Q2", "(province_name, district_name, price, id)"),
        ("idx_properties_published_at", "Q3", "(published_at)"),
        ("idx_properties_property_type", "Q4", "(property_type_name)"),
    ]

    for iname, qid, cols in idx_map:
        sizes = []
        for s in scales:
            cfg_name = f"{qid}_indexed" if qid != "Q3" else "Q3_D"
            rec = configs_by_scale.get(s, {}).get(cfg_name)
            sizes.append(f"{rec['index_size_mb']:.2f} MB" if rec else "N/A")
        s50 = sizes[0] if len(sizes) > 0 else "N/A"
        s200 = sizes[1] if len(sizes) > 1 else "N/A"
        s500 = sizes[2] if len(sizes) > 2 else "N/A"
        lines.append(f"| `{iname}` | {qid} | `{cols}` | {s50} | {s200} | {s500} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Kết luận khoa học và khuyến nghị",
        "",
        "1. **Tối ưu B-tree đơn cột (Q1):** Rất hiệu quả cho các trường có tính chọn lọc cao hoặc vừa phải (`province_name`). Giảm số lượng block cần đọc qua bộ đệm.",
        "2. **Tối ưu Composite Index (Q2):** Đạt hiệu quả cao nhất khi kết hợp lọc khoảng và sắp xếp + LIMIT. Cần sắp xếp thứ tự cột trong Index: `(equality_col_1, equality_col_2, range_or_sort_col)` để tận dụng tối đa chỉ mục.",
        "3. **Viết lại truy vấn (Q3):** Index chỉ phát huy tác dụng khi vị từ là sargable. Tránh tuyệt đối việc áp dụng hàm hoặc ép kiểu trực tiếp trên cột được đánh chỉ mục trong mệnh đề `WHERE`.",
        "4. **Kiểm soát tổng hợp (Q4):** Tránh lạm dụng index cho các truy vấn aggregate toàn bảng. Cần cân nhắc Materialized Views hoặc thống kê định kỳ thay vì chỉ mục B-tree thông thường.",
        "",
    ])

    report_text = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    return report_text


def plot_execution_time_by_scale(records: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Plot Execution Time vs Scale for Q1, Q2, Q3, Q4."""
    scales = sorted(set(r["scale"] for r in records))
    queries = ["Q1", "Q2", "Q3", "Q4"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, qid in enumerate(queries):
        ax = axes[idx]
        q_records = [r for r in records if r["query_id"] == qid]

        # Group by config_id
        config_ids = sorted(set(r["config_id"] for r in q_records))
        for cid in config_ids:
            c_recs = sorted([r for r in q_records if r["config_id"] == cid], key=lambda x: x["scale"])
            x_vals = [r["scale"] for r in c_recs]
            y_vals = [r["execution_time_median_ms"] for r in c_recs]
            marker = "o" if "base" in cid.lower() or cid == "Q3_A" else "s"
            linestyle = "--" if "base" in cid.lower() or cid == "Q3_A" else "-"
            ax.plot(x_vals, y_vals, marker=marker, linestyle=linestyle, linewidth=2, label=cid)

        ax.set_title(f"{qid} Execution Time across Scales", fontsize=12, fontweight="bold")
        ax.set_xlabel("Dataset Scale (rows)", fontsize=10)
        ax.set_ylabel("Median Execution Time (ms)", fontsize=10)
        ax.set_xticks(scales)
        ax.set_xticklabels([f"{s:,}" for s in scales])
        ax.grid(True, linestyle=":", alpha=0.6)
        if config_ids:
            ax.legend(fontsize=9)
        # Use log scale if variation is large
        all_y = [r["execution_time_median_ms"] for r in q_records]
        if all_y and max(all_y) / (min(all_y) + 1e-4) > 10:
            ax.set_yscale("log")
            ax.set_ylabel("Median Execution Time (ms, log scale)", fontsize=10)

    plt.tight_layout()
    plot_path = output_dir / "execution_time_by_scale.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    return plot_path


def plot_speedup_comparison(records: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Plot Speedup bar chart for all optimization methods across scales."""
    scales = sorted(set(r["scale"] for r in records))
    
    # We compare: Q1_indexed, Q2_indexed, Q3_B, Q3_C, Q3_D, Q4_indexed
    target_configs = [
        ("Q1_indexed", "Q1 (Single Index)"),
        ("Q2_indexed", "Q2 (Composite Index)"),
        ("Q3_B", "Q3 B (Rewrite Only)"),
        ("Q3_C", "Q3 C (Index Only)"),
        ("Q3_D", "Q3 D (Rewrite + Index)"),
        ("Q4_indexed", "Q4 (Aggregation Control)"),
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(target_configs))
    width = 0.25

    colors = ["#4C72B0", "#55A868", "#C44E52"]

    for i, scale in enumerate(scales):
        speedups = []
        for cid, _ in target_configs:
            match = next((r for r in records if r["scale"] == scale and r["config_id"] == cid), None)
            speedups.append(match["speedup"] if match else 1.0)
        offset = (i - 1) * width
        rects = ax.bar(x + offset, speedups, width, label=f"{scale:,} rows", color=colors[i % len(colors)], edgecolor="black", linewidth=0.5)

    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Baseline (1.0x)")
    ax.set_ylabel("Speedup Factor (Baseline / Optimized)", fontsize=11, fontweight="bold")
    ax.set_title("Speedup Comparison Across Optimization Methods and Scales", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in target_configs], rotation=15, ha="right", fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plot_path = output_dir / "speedup_comparison.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    return plot_path


def plot_storage_overhead(records: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Plot Index Storage Overhead (MB) across scales."""
    scales = sorted(set(r["scale"] for r in records))
    indexes = [
        ("Q1_indexed", "Q1: province_name"),
        ("Q2_indexed", "Q2: location_price"),
        ("Q3_D", "Q3: published_at"),
        ("Q4_indexed", "Q4: property_type"),
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(indexes))
    width = 0.25
    colors = ["#4575b4", "#74add1", "#abd9e9"]

    for i, scale in enumerate(scales):
        sizes = []
        for cid, _ in indexes:
            match = next((r for r in records if r["scale"] == scale and r["config_id"] == cid), None)
            sizes.append(match["index_size_mb"] if match else 0.0)
        offset = (i - 1) * width
        ax.bar(x + offset, sizes, width, label=f"{scale:,} rows", color=colors[i % len(colors)], edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Index Size (MB)", fontsize=11, fontweight="bold")
    ax.set_title("B-tree Index Storage Overhead by Scale", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in indexes], fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plot_path = output_dir / "index_storage_overhead.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    return plot_path


def analyze_all(
    input_csv: Path = DEFAULT_INPUT_CSV,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    generate_plots: bool = True,
) -> Dict[str, Any]:
    """Execute complete analysis pipeline and output artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records = load_benchmark_csv(input_csv)

    print(f"[*] Doc {len(records)} ban ghi tu {input_csv}...", flush=True)

    report_path = output_dir / "benchmark_analysis_report.md"
    generate_markdown_report(records, report_path)
    print(f"[+] Da tao bao cao Markdown: {report_path}", flush=True)

    generated_plots = []
    if generate_plots:
        p1 = plot_execution_time_by_scale(records, output_dir)
        p2 = plot_speedup_comparison(records, output_dir)
        p3 = plot_storage_overhead(records, output_dir)
        generated_plots.extend([p1, p2, p3])
        print(f"[+] Da tao cac bieu do truc quan hoa tai: {output_dir}", flush=True)

    return {
        "report_path": report_path,
        "plots": generated_plots,
        "record_count": len(records),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_CSV, help="Path to benchmark_results.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for reports and charts")
    parser.add_argument("--no-plots", action="store_true", help="Skip generating charts")
    args = parser.parse_args(argv)

    analyze_all(input_csv=args.input, output_dir=args.output_dir, generate_plots=not args.no_plots)


if __name__ == "__main__":
    main()
