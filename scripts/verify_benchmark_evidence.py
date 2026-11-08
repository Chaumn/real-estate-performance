"""Verification and Provenance Manifest Generator for PostgreSQL Benchmark Raw Evidence.

Validates the existence, completeness, and cryptographic integrity of all 600
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) execution plan files.
"""

from __future__ import annotations

import hashlib
import math
import re
import json
from pathlib import Path
import sys
from typing import Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def compute_sha256(file_path: Path) -> str:
    """Compute hex SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_plan_metrics(raw_json: Any) -> tuple[float | None, float | None, str]:
    """Extract planning time, execution time, and primary scan node from EXPLAIN JSON."""
    try:
        data = raw_json[0] if isinstance(raw_json, list) else raw_json
        plan = data.get("Plan", {})
        planning_time = data.get("Planning Time")
        execution_time = data.get("Execution Time")

        # Determine primary scan node
        scan_type = plan.get("Node Type", "Unknown")
        # If root is Gather, Aggregate, Sort, or Limit, inspect child
        plans = plan.get("Plans", [])
        if scan_type in ("Gather", "Aggregate", "Sort", "Limit") and plans:
            scan_type = f"{scan_type} -> {plans[0].get('Node Type', 'Unknown')}"

        return planning_time, execution_time, scan_type
    except Exception:
        return None, None, "Unknown"


def audit_raw_evidence(
    raw_dir: Path = Path("results/benchmark/raw"),
    manifest_out: Path = Path("results/benchmark/raw_manifest.json"),
) -> dict[str, Any]:
    """Audit all raw explain json files and export cryptographic manifest."""
    if not raw_dir.exists():
        return {
            "status": "MISSING",
            "message": f"Thu muc {raw_dir} khong ton tai",
            "total_files": 0,
            "manifest": [],
        }

    files = sorted(raw_dir.glob("*.json"))
    configs = ['Q1_baseline','Q1_indexed','Q2_baseline','Q2_indexed','Q3_A','Q3_B','Q3_C','Q3_D','Q4_baseline','Q4_indexed']
    expected = {f'{scale}_{config}_run{run:02d}.json' for scale in (50000,200000,500000) for config in configs for run in range(1,21)}
    errors = []
    if {f.name for f in files} != expected:
        errors.append('Run matrix does not match expected scale/configuration/run identities')

    manifest = []
    scales_found = set()
    configs_found = set()

    for fpath in files:
        # Expected naming pattern: {scale}_{config}_run{run:02d}.json
        if not re.fullmatch(r'(50000|200000|500000)_(Q[124]_(baseline|indexed)|Q3_[ABCD])_run(0[1-9]|1[0-9]|20)', fpath.stem):
            errors.append(f'Invalid identity: {fpath.name}')
            continue
        parts = fpath.stem.split("_")
        scale = int(parts[0]) if parts[0].isdigit() else 0
        run_part = parts[-1]
        run_idx = int(run_part.replace("run", "")) if run_part.startswith("run") else 0
        config = "_".join(parts[1:-1])

        scales_found.add(scale)
        configs_found.add(config)

        checksum = compute_sha256(fpath)

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = json.load(f)
            p_time, e_time, scan_node = extract_plan_metrics(content)
            if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0].get('Plan'), dict):
                raise ValueError('Invalid plan structure')
            if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v >= 0 for v in (p_time,e_time)):
                raise ValueError('Missing or invalid timing')
        except Exception as e:
            errors.append(f"{fpath.name}: {e}")
            p_time, e_time, scan_node = None, None, f"Error: {e}"

        manifest.append({
            "filename": fpath.name,
            "scale": scale,
            "config": config,
            "run": run_idx,
            "size_bytes": fpath.stat().st_size,
            "sha256": checksum,
            "planning_time_ms": p_time,
            "execution_time_ms": e_time,
            "primary_scan_type": scan_node,
        })

    summary = {
        "status": "STRUCTURE_VERIFIED" if not errors else "INVALID",
        "errors": errors,
        "limitations": ["Hashes computed, not compared against trusted manifest; filename identities do not prove execution provenance"],
        "total_files": len(files),
        "expected_files": 600,
        "scales_audited": sorted(scales_found),
        "configs_audited": sorted(configs_found),
        "manifest_path": str(manifest_out),
        "entries": manifest,
    }

    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main():
    print("Dang kiem tra toan bo 600 file EXPLAIN JSON tho...", flush=True)
    res = audit_raw_evidence()
    print(f"Ket qua: {res['status']} ({res['total_files']} files hop le)")
    print(f"Cac quy mo: {res['scales_audited']}")
    print(f"Cac cau hinh: {res['configs_audited']}")
    print(f"Manifest: {res['manifest_path']}")


if __name__ == "__main__":
    main()

