"""Automated PostgreSQL Benchmark Runner for Real Estate Performance.

Executes a 3 scales x 10 configurations benchmark matrix:
- Scales: 50,000 | 200,000 | 500,000 rows
- 10 Configurations: Q1 (base/idx), Q2 (base/idx), Q3 (A/B/C/D), Q4 (base/idx)
- 3 warm-up runs (discarded) + 20 official runs per configuration
- Captures EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
- Extracts Planning Time, Execution Time, Buffers, Scan Types, Index Name, Index Size
- Computes Median Execution Time, Min, Max, P95, StdDev, IQR, Speedup
- Verifies query result equivalence between baseline and optimized forms
- Records full environment information (PostgreSQL, OS, Python, hardware)
"""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import psycopg
from psycopg.rows import dict_row

if __package__:
    from .import_csv import load_connection_settings, import_csv
else:
    from import_csv import load_connection_settings, import_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_BENCHMARK_DIR = PROJECT_ROOT / "sql" / "benchmark"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "benchmark"

# 10 configurations across 4 benchmark queries
CONFIGURATIONS = [
    {
        "config_id": "Q1_baseline",
        "query_id": "Q1",
        "description": "Single-column search by province (No supplemental index)",
        "query_file": "q1.sql",
        "index_file": None,
        "supplemental_index": None,
        "baseline_for": "Q1",
        "is_baseline": True,
    },
    {
        "config_id": "Q1_indexed",
        "query_id": "Q1",
        "description": "Single-column search by province (B-tree on province_name)",
        "query_file": "q1.sql",
        "index_file": "q1_province_name.sql",
        "supplemental_index": "idx_properties_province_name",
        "baseline_for": "Q1",
        "is_baseline": False,
    },
    {
        "config_id": "Q2_baseline",
        "query_id": "Q2",
        "description": "Multi-column filter + range + ORDER BY + LIMIT (No supplemental index)",
        "query_file": "q2.sql",
        "index_file": None,
        "supplemental_index": None,
        "baseline_for": "Q2",
        "is_baseline": True,
    },
    {
        "config_id": "Q2_indexed",
        "query_id": "Q2",
        "description": "Multi-column filter + range + ORDER BY + LIMIT (Composite B-tree)",
        "query_file": "q2.sql",
        "index_file": "q2_location_price.sql",
        "supplemental_index": "idx_properties_location_price",
        "baseline_for": "Q2",
        "is_baseline": False,
    },
    {
        "config_id": "Q3_A",
        "query_id": "Q3",
        "description": "Query Rewriting: A. Original Query (published_at::date = DATE), No Index",
        "query_file": "q3_original.sql",
        "index_file": None,
        "supplemental_index": None,
        "baseline_for": "Q3",
        "is_baseline": True,
    },
    {
        "config_id": "Q3_B",
        "query_id": "Q3",
        "description": "Query Rewriting: B. Rewritten Query (published_at >= AND <), No Index",
        "query_file": "q3_rewritten.sql",
        "index_file": None,
        "supplemental_index": None,
        "baseline_for": "Q3",
        "is_baseline": False,
    },
    {
        "config_id": "Q3_C",
        "query_id": "Q3",
        "description": "Query Rewriting: C. Original Query, With Index on published_at",
        "query_file": "q3_original.sql",
        "index_file": "q3_published_at.sql",
        "supplemental_index": "idx_properties_published_at",
        "baseline_for": "Q3",
        "is_baseline": False,
    },
    {
        "config_id": "Q3_D",
        "query_id": "Q3",
        "description": "Query Rewriting: D. Rewritten Query, With Index on published_at",
        "query_file": "q3_rewritten.sql",
        "index_file": "q3_published_at.sql",
        "supplemental_index": "idx_properties_published_at",
        "baseline_for": "Q3",
        "is_baseline": False,
    },
    {
        "config_id": "Q4_baseline",
        "query_id": "Q4",
        "description": "Aggregation Control: GROUP BY + AVG + COUNT (No supplemental index)",
        "query_file": "q4.sql",
        "index_file": None,
        "supplemental_index": None,
        "baseline_for": "Q4",
        "is_baseline": True,
    },
    {
        "config_id": "Q4_indexed",
        "query_id": "Q4",
        "description": "Aggregation Control: GROUP BY + AVG + COUNT (B-tree on property_type_name)",
        "query_file": "q4.sql",
        "index_file": "q4_property_type.sql",
        "supplemental_index": "idx_properties_property_type",
        "baseline_for": "Q4",
        "is_baseline": False,
    },
]

INDEX_INSPECTION_SQL = """
    SELECT
        indexrelid::regclass::text AS index_name,
        indisprimary,
        indisvalid,
        pg_get_indexdef(indexrelid) AS index_definition,
        pg_relation_size(indexrelid) AS index_bytes
    FROM pg_index
    WHERE indrelid = 'public.properties'::regclass
    ORDER BY indexrelid::regclass::text;
"""

SETTINGS_INSPECTION_SQL = """
    SELECT name, setting, unit, source
    FROM pg_settings
    WHERE name IN (
        'shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem',
        'random_page_cost', 'seq_page_cost', 'effective_io_concurrency',
        'max_parallel_workers', 'max_parallel_workers_per_gather',
        'jit', 'default_statistics_target', 'track_io_timing',
        'enable_seqscan', 'enable_indexscan', 'enable_indexonlyscan', 'enable_bitmapscan'
    )
    ORDER BY name;
"""


def read_sql_file(relative_path: Path) -> str:
    """Read a clean SQL file stripping UTF-8 BOM."""
    path = SQL_BENCHMARK_DIR / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Khong tim thay file SQL: {path}")
    return path.read_text(encoding="utf-8-sig").strip()


def extract_plan_nodes(plan_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recursively collect all execution plan nodes."""
    nodes = [plan_dict]
    if "Plans" in plan_dict:
        for child in plan_dict["Plans"]:
            nodes.extend(extract_plan_nodes(child))
    return nodes


def extract_plan_metrics(explain_json: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) structure.
    
    Extracts Planning Time, Execution Time, buffer statistics,
    and identifies all scan operations and indexes used.
    """
    if not explain_json or not isinstance(explain_json, list):
        raise ValueError("EXPLAIN JSON phai la danh sach chua it nhat mot phan tu")
    
    root = explain_json[0]
    planning_time = float(root["Planning Time"])
    execution_time = float(root["Execution Time"])
    if not all(math.isfinite(v) and v >= 0 for v in (planning_time, execution_time)):
        raise ValueError("Invalid EXPLAIN timing")
    plan_root = root.get("Plan", {})

    all_nodes = extract_plan_nodes(plan_root)

    # Detect scan operations
    scan_types = []
    indexes_used = []
    for node in all_nodes:
        node_type = node.get("Node Type", "")
        if "Scan" in node_type:
            scan_types.append(node_type)
        if "Index Name" in node:
            indexes_used.append(node["Index Name"])

    # Determine primary scan type (prioritize index scans or bitmap scans if present)
    primary_scan = "Seq Scan"
    if any(s in ("Index Scan", "Index Only Scan") for s in scan_types):
        primary_scan = next(s for s in scan_types if s in ("Index Scan", "Index Only Scan"))
    elif any("Bitmap" in s for s in scan_types):
        primary_scan = "Bitmap Scan"
    elif scan_types:
        primary_scan = scan_types[0]

    # Buffer counters from root node (PostgreSQL aggregates buffer counts up the tree)
    shared_hit = int(plan_root.get("Shared Hit Blocks", 0))
    shared_read = int(plan_root.get("Shared Read Blocks", 0))
    shared_dirtied = int(plan_root.get("Shared Dirtied Blocks", 0))
    shared_written = int(plan_root.get("Shared Written Blocks", 0))
    temp_read = int(plan_root.get("Temp Read Blocks", 0))
    temp_written = int(plan_root.get("Temp Written Blocks", 0))

    return {
        "planning_time_ms": planning_time,
        "execution_time_ms": execution_time,
        "total_time_ms": planning_time + execution_time,
        "primary_scan_type": primary_scan,
        "all_scan_types": list(dict.fromkeys(scan_types)),
        "indexes_used": list(dict.fromkeys(indexes_used)),
        "actual_rows": plan_root.get("Actual Rows", 0),
        "actual_loops": plan_root.get("Actual Loops", 1),
        "shared_hit_blocks": shared_hit,
        "shared_read_blocks": shared_read,
        "shared_dirtied_blocks": shared_dirtied,
        "shared_written_blocks": shared_written,
        "temp_read_blocks": temp_read,
        "temp_written_blocks": temp_written,
    }


def compute_statistics(values: List[float]) -> Dict[str, float]:
    """Compute robust descriptive statistics: median, min, max, mean, stddev, IQR."""
    if not values:
        return {"median": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "iqr": 0.0, "p95": 0.0}
    s = sorted(values)
    n = len(s)
    med = statistics.median(s)
    mean_val = statistics.mean(s)
    min_val = s[0]
    max_val = s[-1]
    std_val = statistics.stdev(s) if n > 1 else 0.0

    # Quartiles and IQR
    if n >= 4:
        mid = n // 2
        q1 = statistics.median(s[:mid])
        q3 = statistics.median(s[mid:] if n % 2 == 0 else s[mid + 1:])
        iqr = q3 - q1
    else:
        iqr = max_val - min_val

    # 95th percentile
    p95_idx = min(int(math.ceil(0.95 * n)) - 1, n - 1)
    p95_val = s[p95_idx]

    return {
        "median": round(med, 4),
        "mean": round(mean_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "std": round(std_val, 4),
        "iqr": round(iqr, 4),
        "p95": round(p95_val, 4),
    }


class BenchmarkRunner:
    """Manages index isolation, query execution, and metric extraction."""

    def __init__(self, connection_settings: Optional[Dict[str, Any]] = None):
        self.settings = connection_settings or load_connection_settings()
        self.reset_sql = read_sql_file(Path("reset_indexes.sql"))

    def get_connection(self) -> psycopg.Connection:
        """Establish a dedicated autocommit connection for benchmarking."""
        conn = psycopg.connect(
            **self.settings,
            autocommit=True,
            client_encoding="UTF8",
            connect_timeout=10,
        )
        return conn

    def inspect_environment(self) -> Dict[str, Any]:
        """Gather database, hardware, and runtime environment specifications."""
        with self.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT version(), current_database(), current_user;")
                ver_info = cur.fetchone()

                cur.execute("SHOW server_version_num;")
                server_version_num = cur.fetchone()["server_version_num"]

                cur.execute("SHOW client_encoding;")
                client_encoding = cur.fetchone()["client_encoding"]

                cur.execute("SHOW TimeZone;")
                timezone = cur.fetchone()["TimeZone"]

                cur.execute(
                    "SELECT datcollate, datctype FROM pg_database WHERE datname = current_database();"
                )
                collate_info = cur.fetchone()

                cur.execute(SETTINGS_INSPECTION_SQL)
                pg_settings = {row["name"]: {"setting": row["setting"], "unit": row["unit"], "source": row["source"]} for row in cur.fetchall()}

        # Machine info
        uname = platform.uname()
        env_meta = {
            "timestamp": datetime.datetime.now().isoformat(),
            "os": f"{uname.system} {uname.release} (build {uname.version})",
            "machine": uname.machine,
            "processor": uname.processor,
            "cpu_logical_cores": os.cpu_count(),
            "python_version": sys.version,
            "psycopg_version": psycopg.__version__,
            "postgresql_version": ver_info["version"] if ver_info else "unknown",
            "server_version_num": server_version_num,
            "database": ver_info["current_database"] if ver_info else "unknown",
            "user": ver_info["current_user"] if ver_info else "unknown",
            "client_encoding": client_encoding,
            "timezone": timezone,
            "collation": collate_info,
            "pg_settings": pg_settings,
        }
        return env_meta

    def reset_indexes(self, conn: psycopg.Connection) -> None:
        """Drop all four supplemental indexes without touching PK or table data."""
        with conn.cursor() as cur:
            cur.execute(self.reset_sql)

    def prepare_configuration(
        self, conn: psycopg.Connection, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up index environment, run ANALYZE, and inspect index catalog."""
        # 1. Always reset supplemental indexes first
        self.reset_indexes(conn)

        # 2. Create index if required by configuration
        index_bytes = 0
        supplemental_index_name = config.get("supplemental_index")
        index_file = config.get("index_file")
        if index_file:
            index_sql = read_sql_file(Path("indexes") / index_file)
            with conn.cursor() as cur:
                cur.execute(index_sql)

        # 3. Update optimizer statistics
        with conn.cursor() as cur:
            cur.execute("ANALYZE public.properties;")

        # 4. Verify catalog state
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(INDEX_INSPECTION_SQL)
            indexes = cur.fetchall()

        # Check index isolation: only primary key + at most the expected supplemental index
        from scripts.benchmark_validation import validate_catalog
        validate_catalog(indexes, supplemental_index_name)
        index_names = [idx["index_name"] for idx in indexes]
        for idx in indexes:
            if idx["indisprimary"]:
                continue
            if idx["index_name"] == supplemental_index_name:
                index_bytes = idx["index_bytes"]
            else:
                raise RuntimeError(
                    f"Phat hien Index ngoai le khong mong muon: {idx['index_name']} trong cau hinh {config['config_id']}"
                )

        if supplemental_index_name and supplemental_index_name not in index_names:
            raise RuntimeError(
                f"Index {supplemental_index_name} chua duoc tao thanh cong cho {config['config_id']}"
            )

        return {
            "supplemental_index_name": supplemental_index_name,
            "index_bytes": index_bytes,
            "active_indexes": indexes,
        }

    def verify_query_equivalence(self, conn: psycopg.Connection, query_id: str) -> None:
        """Assert identical result sets between query variations."""
        with conn.cursor() as cur:
            if query_id == "Q3":
                # Rigorous bi-directional EXCEPT ALL check
                q3_diff_sql = """
                    WITH original AS (
                        SELECT id, name, published_at
                        FROM public.properties
                        WHERE published_at::date = DATE '2025-10-15'
                    ), rewritten AS (
                        SELECT id, name, published_at
                        FROM public.properties
                        WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
                          AND published_at < TIMESTAMP '2025-10-16 00:00:00'
                    )
                    SELECT COUNT(*) AS differing_rows
                    FROM (
                        (SELECT * FROM original EXCEPT ALL SELECT * FROM rewritten)
                        UNION ALL
                        (SELECT * FROM rewritten EXCEPT ALL SELECT * FROM original)
                    ) AS differences;
                """
                cur.execute(q3_diff_sql)
                diff_count = cur.fetchone()[0]
                if diff_count != 0:
                    raise AssertionError(
                        f"Q3 Equivalence Check that bai: {diff_count} dong khac biet giua Original va Rewritten!"
                    )

    def execute_explain_analyze(
        self, conn: psycopg.Connection, query_sql: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) and return parsed metrics."""
        explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)\n{query_sql}"
        with conn.cursor() as cur:
            cur.execute(explain_sql)
            raw_result = cur.fetchone()[0]
        
        metrics = extract_plan_metrics(raw_result)
        return raw_result, metrics

    def run_benchmark(
        self,
        scales: List[int],
        configs_to_run: Optional[List[str]] = None,
        warmup_runs: int = 3,
        official_runs: int = 20,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        check_equivalence: bool = True,
        auto_import: bool = False,
        dedicated_database: bool = False,
    ) -> Dict[str, Any]:
        """Execute the full benchmark suite across scales and configurations."""
        if auto_import and (not dedicated_database or self.settings.get('dbname') != 'real_estate_db'):
            raise ValueError('Auto-import requires explicit dedicated real_estate_db authorization')
        from scripts.benchmark_validation import csv_fingerprint, database_fingerprint, result_digest
        experiment_id = uuid.uuid4().hex
        output_dir = output_dir / experiment_id
        raw_output_dir = output_dir / "raw"
        raw_output_dir.mkdir(parents=True, exist_ok=False)
        (output_dir / "experiment.json").write_text(json.dumps({"experiment_id": experiment_id, "status": "STARTED", "warmups": warmup_runs, "official_runs": official_runs}), encoding="utf-8")

        env_info = self.inspect_environment()
        env_file = output_dir / "environment_info.json"
        env_file.write_text(json.dumps(env_info, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[*] Da ghi thong so moi truong: {env_file}", flush=True)

        selected_configs = [
            c for c in CONFIGURATIONS
            if configs_to_run is None or c["config_id"] in configs_to_run
        ]

        all_results = []
        summary_by_scale: Dict[int, Dict[str, Any]] = {scale: {} for scale in scales}

        total_steps = len(scales) * len(selected_configs)
        step = 0

        with self.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as session_cursor:
                session_cursor.execute(SETTINGS_INSPECTION_SQL)
                session_settings = session_cursor.fetchall()
            (output_dir/'session_settings.json').write_text(json.dumps({'experiment_id':experiment_id,'settings':session_settings},default=str,indent=2),encoding='utf-8')
            for scale in scales:
                # 1. Verify table row count matches current scale
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*), MIN(id), MAX(id) FROM public.properties;")
                    row_count, min_id, max_id = cur.fetchone()

                if row_count != scale:
                    if auto_import:
                        csv_path = PROJECT_ROOT / "data" / "processed" / f"properties_{scale}.csv"
                        if not csv_path.is_file():
                            raise FileNotFoundError(f"Khong tim thay CSV de auto-import: {csv_path}")
                        print(f"[*] Tu dong nap du lieu quy mo {scale:,} tu {csv_path}...", flush=True)
                        import_csv(csv_path, replace=True, settings=self.settings)
                        with conn.cursor() as cur:
                            cur.execute("SELECT COUNT(*), MIN(id), MAX(id) FROM public.properties;")
                            row_count, min_id, max_id = cur.fetchone()
                    else:
                        raise RuntimeError(
                            f"Quy mo du lieu khong khop: yeu cau {scale}, nhung DB hien co {row_count}. "
                            f"Hay chay import_csv --file data/processed/properties_{scale}.csv --replace truoc, "
                            f"hoac them co --auto-import vao runner!"
                        )

                print(f"\n=======================================================", flush=True)
                print(f"[*] KIEM TRA DATASET QUY MO: {scale:,} BAN GHI", flush=True)
                print(f"[*] Hien tai tren DB: {row_count:,} dong (ID: {min_id}..{max_id})", flush=True)
                print(f"=======================================================", flush=True)

                # Verify Q3 equivalence once per scale
                if check_equivalence:
                    print(f"[*] Kiem tra tinh tuong duong Q3 (Original vs Rewritten)...", flush=True)
                    self.verify_query_equivalence(conn, "Q3")
                    print(f"[+] Q3 Equivalence Check PASSED: 0 dong sai khac.", flush=True)

                scale_medians: Dict[str, float] = {}
                # Hold a table lock for the complete scale: concurrent writers
                # must not alter rows between equivalence checks and timings.
                conn.execute('BEGIN')
                conn.execute('LOCK TABLE public.properties IN SHARE MODE')
                csv_path = PROJECT_ROOT / 'data' / 'processed' / f'properties_{scale}.csv'
                expected = csv_fingerprint(csv_path)
                before = database_fingerprint(conn)
                if before != {k:expected[k] for k in before}:
                    raise ValueError('Database content differs from CSV')
                evidence = {'csv':expected,'before':before,'configurations':{}}
                references = {}
                self.reset_indexes(conn)
                for query_id, filename in [('Q1','q1.sql'),('Q2','q2.sql'),('Q3','q3_original.sql'),('Q4','q4.sql')]:
                    references[query_id] = result_digest(conn, read_sql_file(Path('queries')/filename), query_id=='Q2')

                for config in selected_configs:
                    step += 1
                    cid = config["config_id"]
                    qid = config["query_id"]
                    print(f"\n[{step}/{total_steps}] Cau hinh: {cid} (Dataset: {scale:,} dong)", flush=True)
                    print(f"    Mo ta: {config['description']}", flush=True)

                    # Setup isolated index and analyze
                    prep_info = self.prepare_configuration(conn, config)
                    query_sql = read_sql_file(Path("queries") / config["query_file"])
                    if database_fingerprint(conn) != before:
                        raise ValueError('Data changed before configuration')
                    if result_digest(conn, query_sql, qid=='Q2') != references[qid]:
                        raise ValueError('Query result equivalence failed')
                    if qid == 'Q3': self.verify_query_equivalence(conn, 'Q3')
                    evidence['configurations'][cid] = {'catalog':prep_info,'equivalence':'PASSED'}
                    index_bytes = prep_info["index_bytes"]
                    index_size_mb = round(index_bytes / (1024 * 1024), 2)
                    print(f"    Index dung luong: {index_size_mb} MB ({index_bytes:,} bytes)", flush=True)

                    # 2. Warm-up runs (discarded)
                    print(f"    Warm-up {warmup_runs} lan...", end="", flush=True)
                    for w in range(warmup_runs):
                        warmup, _ = self.execute_explain_analyze(conn, query_sql)
                        warmup_path = output_dir / f"{scale}_{cid}_warmup{w+1:02d}.json"
                        with warmup_path.open('x', encoding='utf-8') as warmup_file:
                            json.dump(warmup, warmup_file)
                    print(" xong.", flush=True)

                    # 3. Official runs
                    print(f"    Chay {official_runs} lan do chinh thuc...", flush=True)
                    run_exec_times = []
                    run_plan_times = []
                    run_shared_hits = []
                    run_shared_reads = []
                    run_scan_types = []
                    run_indexes_used = []

                    for r in range(1, official_runs + 1):
                        raw_json, metrics = self.execute_explain_analyze(conn, query_sql)
                        
                        # Save raw EXPLAIN JSON
                        raw_filename = f"{scale}_{cid}_run{r:02d}.json"
                        raw_filepath = raw_output_dir / raw_filename
                        with raw_filepath.open('x', encoding='utf-8') as raw_file:
                            json.dump(raw_json, raw_file, indent=2)

                        run_exec_times.append(metrics["execution_time_ms"])
                        run_plan_times.append(metrics["planning_time_ms"])
                        run_shared_hits.append(metrics["shared_hit_blocks"])
                        run_shared_reads.append(metrics["shared_read_blocks"])
                        run_scan_types.append(metrics["primary_scan_type"])
                        run_indexes_used.extend(metrics["indexes_used"])

                    # 4. Compute statistics
                    exec_stats = compute_statistics(run_exec_times)
                    plan_stats = compute_statistics(run_plan_times)
                    hit_median = round(statistics.median(run_shared_hits), 1)
                    read_median = round(statistics.median(run_shared_reads), 1)
                    dominant_scan = max(set(run_scan_types), key=run_scan_types.count)
                    unique_indexes = list(dict.fromkeys(run_indexes_used))

                    scale_medians[cid] = exec_stats["median"]

                    # Speedup relative to the query's baseline
                    baseline_cid = f"{qid}_baseline" if qid != "Q3" else "Q3_A"
                    baseline_median = scale_medians.get(baseline_cid)
                    speedup = round(baseline_median / exec_stats["median"], 2) if baseline_median is not None and exec_stats["median"] > 0 else None

                    print(f"    -> Median Execution: {exec_stats['median']} ms (IQR: {exec_stats['iqr']} ms, min: {exec_stats['min']}, max: {exec_stats['max']})")
                    print(f"    -> Primary Scan: {dominant_scan} | Speedup: {speedup}x | Shared Hit: {hit_median} blk | Read: {read_median} blk")

                    result_record = {
                        "scale": scale,
                        "query_id": qid,
                        "config_id": cid,
                        "description": config["description"],
                        "query_file": config["query_file"],
                        "supplemental_index": config.get("supplemental_index"),
                        "index_bytes": index_bytes,
                        "index_size_mb": index_size_mb,
                        "dominant_scan_type": dominant_scan,
                        "indexes_used": ",".join(unique_indexes),
                        "official_runs": official_runs,
                        "execution_time_median_ms": exec_stats["median"],
                        "execution_time_mean_ms": exec_stats["mean"],
                        "execution_time_min_ms": exec_stats["min"],
                        "execution_time_max_ms": exec_stats["max"],
                        "execution_time_std_ms": exec_stats["std"],
                        "execution_time_iqr_ms": exec_stats["iqr"],
                        "execution_time_p95_ms": exec_stats["p95"],
                        "planning_time_median_ms": plan_stats["median"],
                        "planning_time_mean_ms": plan_stats["mean"],
                        "shared_hit_blocks_median": hit_median,
                        "shared_read_blocks_median": read_median,
                        "speedup": speedup,
                        "raw_execution_times": run_exec_times,
                    }
                    all_results.append(result_record)
                    summary_by_scale[scale][cid] = result_record

                evidence['after'] = database_fingerprint(conn)
                if evidence['after'] != before: raise ValueError('Data changed during scale')
                (output_dir/f'{scale}_validation.json').write_text(json.dumps(evidence,default=str,indent=2),encoding='utf-8')
                conn.execute('COMMIT')

        # Final cleanup: reset supplemental indexes
        with self.get_connection() as conn:
            self.reset_indexes(conn)

        # 5. Export summary files
        self.export_results(all_results, summary_by_scale, env_info, output_dir)
        (output_dir/'experiment.json').write_text(json.dumps({'experiment_id':experiment_id,'status':'COMPLETED','warmups':warmup_runs,'official_runs':official_runs,'scales':scales,'configurations':[c['config_id'] for c in selected_configs]},indent=2),encoding='utf-8')
        return {
            "results": all_results,
            "summary_by_scale": summary_by_scale,
            "environment": env_info,
        }

    def export_results(
        self,
        results: List[Dict[str, Any]],
        summary_by_scale: Dict[int, Dict[str, Any]],
        env_info: Dict[str, Any],
        output_dir: Path,
    ) -> None:
        """Write summary CSV and hierarchical JSON."""
        # Export CSV
        csv_path = output_dir / "benchmark_results.csv"
        csv_headers = [
            "scale", "query_id", "config_id", "dominant_scan_type", "indexes_used",
            "index_size_mb", "execution_time_median_ms", "execution_time_iqr_ms",
            "execution_time_min_ms", "execution_time_max_ms", "planning_time_median_ms",
            "shared_hit_blocks_median", "shared_read_blocks_median", "speedup",
        ]
        import csv
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"\n[+] Da xuat CSV ket qua: {csv_path}", flush=True)

        # Export Full JSON
        json_path = output_dir / "benchmark_summary.json"
        summary_data = {
            "metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "scales": list(summary_by_scale.keys()),
                "total_records": len(results),
            },
            "environment": env_info,
            "summary_by_scale": summary_by_scale,
            "flat_results": results,
        }
        json_path.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] Da xuat JSON tong hop: {json_path}", flush=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dedicated-database', action='store_true', help='Confirm real_estate_db is dedicated and may be replaced by auto-import')
    parser.add_argument(
        "--scales",
        default="50000,200000,500000",
        help="Comma-separated dataset scales to benchmark (default: 50000,200000,500000)",
    )
    parser.add_argument(
        "--configs",
        default=None,
        help="Comma-separated configuration IDs to run (default: all 10 configurations)",
    )
    parser.add_argument(
        "--warmups",
        type=int,
        default=3,
        help="Number of warm-up iterations to discard (default: 3)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=20,
        help="Number of official benchmark iterations (default: 20)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save benchmark results and raw plans",
    )
    parser.add_argument(
        "--skip-equivalence",
        action="store_true",
        help="Skip bi-directional equivalence verification query",
    )
    parser.add_argument(
        "--auto-import",
        action="store_true",
        help="Automatically import dataset CSV if database row count does not match the target scale",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check connection, settings, schema and catalog without running queries",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    scales = [int(s.strip()) for s in args.scales.split(",") if s.strip()]
    configs = [c.strip() for c in args.configs.split(",")] if args.configs else None

    runner = BenchmarkRunner()

    if args.check_only:
        print("[*] Kiem tra ket noi va thong so moi truong...", flush=True)
        env = runner.inspect_environment()
        print(f"[+] Ket noi thanh cong toi PostgreSQL {env['postgresql_version']}")
        print(f"[+] Database: {env['database']} | User: {env['user']}")
        print(f"[+] Shared Buffers: {env['pg_settings'].get('shared_buffers', {}).get('setting')}")
        return

    print("==========================================================", flush=True)
    print("      AUTOMATED POSTGRESQL BENCHMARK RUNNER               ", flush=True)
    print("==========================================================", flush=True)
    print(f"Scales: {scales}")
    print(f"Configs: {configs or 'All 10 configurations'}")
    print(f"Warm-ups: {args.warmups} | Official Runs: {args.runs}")
    print(f"Output: {args.output_dir}")
    print(f"Auto-import: {args.auto_import}")

    runner.run_benchmark(
        scales=scales,
        configs_to_run=configs,
        warmup_runs=args.warmups,
        official_runs=args.runs,
        output_dir=args.output_dir,
        check_equivalence=not args.skip_equivalence,
        auto_import=args.auto_import,
        dedicated_database=args.dedicated_database,
    )


if __name__ == "__main__":
    main()
