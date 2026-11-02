import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
RAW_PLANS_DIR = ROOT / "results" / "benchmark" / "raw"
MANIFEST_PATH = ROOT / "results" / "benchmark" / "raw_manifest.json"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

print("=== CHECKING DATASETS ===")
datasets_info = {}
for scale in [50000, 200000, 500000]:
    csv_file = DATA_DIR / f"properties_{scale}.csv"
    parquet_file = DATA_DIR / f"properties_{scale}.parquet"
    
    assert csv_file.exists(), f"Missing {csv_file}"
    csv_size = csv_file.stat().st_size
    csv_hash = sha256_file(csv_file)
    
    # Read rows and columns
    df = pd.read_csv(csv_file)
    num_rows, num_cols = df.shape
    assert num_rows == scale, f"Expected {scale} rows, got {num_rows}"
    assert num_cols == 9, f"Expected 9 cols, got {num_cols}"
    
    pq_size = parquet_file.stat().st_size if parquet_file.exists() else None
    pq_hash = sha256_file(parquet_file) if parquet_file.exists() else None
    
    datasets_info[str(scale)] = {
        "scale": scale,
        "csv_filename": csv_file.name,
        "csv_size_bytes": csv_size,
        "csv_sha256": csv_hash,
        "parquet_filename": parquet_file.name if parquet_file.exists() else None,
        "parquet_size_bytes": pq_size,
        "parquet_sha256": pq_hash,
        "row_count": num_rows,
        "column_count": num_cols,
        "columns": list(df.columns),
        "id_min": int(df["id"].min()),
        "id_max": int(df["id"].max()),
        "first_5_ids": list(map(int, df["id"].head(5))),
        "last_5_ids": list(map(int, df["id"].tail(5))),
    }
    print(f"[{scale}] CSV: {csv_size:,} bytes | SHA-256: {csv_hash[:16]}... | Rows: {num_rows:,} | Cols: {num_cols}")

# Check subset nesting
df_50k = pd.read_csv(DATA_DIR / "properties_50000.csv")
df_200k = pd.read_csv(DATA_DIR / "properties_200000.csv")
df_500k = pd.read_csv(DATA_DIR / "properties_500000.csv")

# Verify that 50K is exactly prefix of 200K, and 200K prefix of 500K
is_50k_subset_200k = df_50k.equals(df_200k.iloc[:50000])
is_200k_subset_500k = df_200k.equals(df_500k.iloc[:200000])
print(f"Subset nesting D_50K == D_200K[:50000]: {is_50k_subset_200k}")
print(f"Subset nesting D_200K == D_500K[:200000]: {is_200k_subset_500k}")

dataset_manifest = {
    "title": "Vietnam Real Estate Performance Benchmark Datasets",
    "upstream_source": {
        "repository": "https://huggingface.co/datasets/Phuscca/vietnam-real-estates",
        "split": "train",
        "streaming": True,
        "revision": None,
        "seed": 42,
        "buffer_size": 10000,
        "batch_size": 2000,
        "license": "Apache-2.0 / CC-BY-4.0"
    },
    "storage_policy": {
        "local_directory": "data/processed/",
        "git_status": "gitignored via .gitignore (due to size > 140 MB)",
        "reproducibility": "Deterministic generation via `python scripts/build_large_dataset.py`"
    },
    "nesting_property": "D_50K subset D_200K subset D_500K (exact row-level prefix match)",
    "datasets": datasets_info
}

manifest_out = ROOT / "report" / "dataset_manifest.json"
manifest_out.write_text(json.dumps(dataset_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved dataset manifest: {manifest_out}")

print("\n=== CHECKING 600 EXECUTION PLANS ===")
plan_files = list(RAW_PLANS_DIR.glob("*.json"))
print(f"Total raw plan JSON files: {len(plan_files)}")
assert len(plan_files) == 600, f"Expected 600 plans, found {len(plan_files)}"

# Load raw manifest if exists
if MANIFEST_PATH.exists():
    raw_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(f"Existing raw manifest entries: {len(raw_manifest)}")
else:
    raw_manifest = {}

# Verify every plan parses and check SHA-256
corrupted_files = []
manifest_mismatches = []
plans_summary = {}

for p in plan_files:
    content = p.read_bytes()
    calc_hash = hashlib.sha256(content).hexdigest()
    try:
        plan_json = json.loads(content.decode("utf-8"))
    except Exception as e:
        corrupted_files.append((p.name, str(e)))
        continue
    
    if p.name in raw_manifest:
        if raw_manifest[p.name] != calc_hash:
            manifest_mismatches.append(p.name)
    
    plans_summary[p.name] = {
        "sha256": calc_hash,
        "size_bytes": len(content),
    }

print(f"Corrupted JSON files: {len(corrupted_files)}")
print(f"Manifest SHA-256 mismatches: {len(manifest_mismatches)}")
assert len(corrupted_files) == 0, f"Corrupted files: {corrupted_files}"

# Check Q2 Sort node: baseline must have Sort, indexed must not
q2_base = json.loads((RAW_PLANS_DIR / "500000_Q2_baseline_run01.json").read_text(encoding="utf-8"))
q2_idx = json.loads((RAW_PLANS_DIR / "500000_Q2_indexed_run01.json").read_text(encoding="utf-8"))

def has_node_type(plan_node, node_type):
    if plan_node.get("Node Type") == node_type:
        return True
    for child in plan_node.get("Plans", []):
        if has_node_type(child, node_type):
            return True
    return False

q2_base_has_sort = has_node_type(q2_base[0]["Plan"], "Sort")
q2_idx_has_sort = has_node_type(q2_idx[0]["Plan"], "Sort")
print(f"Q2 baseline has Sort: {q2_base_has_sort} (Expected: True)")
print(f"Q2 indexed has Sort: {q2_idx_has_sort} (Expected: False)")
assert q2_base_has_sort is True
assert q2_idx_has_sort is False

benchmark_manifest = {
    "title": "PostgreSQL 18.3 Execution Plans Audit Manifest",
    "total_plans": len(plans_summary),
    "scales": [50000, 200000, 500000],
    "configurations": ["Q1_baseline", "Q1_indexed", "Q2_baseline", "Q2_indexed", "Q3_A", "Q3_B", "Q3_C", "Q3_D", "Q4_baseline", "Q4_indexed"],
    "runs_per_config": 20,
    "warmups_discarded": 3,
    "hardware_environment": {
        "engine": "PostgreSQL 18.3 x86_64-pc-windows-msvc",
        "cpu": "Intel Core i7-11800H @ 2.30 GHz (8 cores, 16 threads)",
        "ram": "16 GB DDR4-3200",
        "storage": "NVMe SSD PCIe 3.0 (KIOXIA 512GB)"
    },
    "verification_checks": {
        "all_600_valid_json": True,
        "q2_baseline_has_sort": True,
        "q2_indexed_sort_eliminated": True,
        "all_sha256_match_manifest": len(manifest_mismatches) == 0
    },
    "plans": plans_summary
}

bench_manifest_out = ROOT / "report" / "benchmark_manifest.json"
bench_manifest_out.write_text(json.dumps(benchmark_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved benchmark manifest: {bench_manifest_out}")

