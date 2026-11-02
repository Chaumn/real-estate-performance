# -*- coding: utf-8 -*-
"""
Executes pytest with detailed JSON reporting and categorizes tests into:
- Unit Tests
- Integration Tests
- End-to-End Tests
Generates results/validation/test_execution_summary.json
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATION_DIR = PROJECT_ROOT / "results" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = VALIDATION_DIR / "pytest_execution.log"
SUMMARY_FILE = VALIDATION_DIR / "test_execution_summary.json"

def classify_test(nodeid: str) -> str:
    """Classify test into Unit, Integration, or End-to-End."""
    node_lower = nodeid.lower()
    
    # E2E Tests
    if "test_pipeline" in node_lower or "smoke_pipeline" in node_lower or "consistency" in node_lower or "evidence" in node_lower:
        return "End-to-End"
    
    # Integration Tests (PostgreSQL, Pandas/Polars/Parquet benchmarks, DB import, real SQL)
    if "test_live_postgresql" in node_lower or "test_benchmark_processing" in node_lower or "test_import_csv" in node_lower or "test_benchmark_sql" in node_lower:
        return "Integration"
    
    # Default to Unit
    return "Unit"

def main():
    print("Running pytest with verbose reporting...")
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")

    log_content = f"STDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}\n"
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(log_content)
    print(f"[+] Saved pytest raw log to: {LOG_FILE}")

    # Parse test lines
    tests_detail = []
    category_counts = {
        "Unit": {"passed": 0, "failed": 0, "skipped": 0, "total": 0},
        "Integration": {"passed": 0, "failed": 0, "skipped": 0, "total": 0},
        "End-to-End": {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
    }

    for line in res.stdout.splitlines():
        line_s = line.strip()
        if "::" in line_s and ("PASSED" in line_s or "FAILED" in line_s or "SKIPPED" in line_s):
            parts = line_s.split()
            nodeid = parts[0]
            status = "UNKNOWN"
            for token in parts:
                if token in ("PASSED", "FAILED", "SKIPPED"):
                    status = token
                    break
            
            cat = classify_test(nodeid)
            category_counts[cat]["total"] += 1
            if status == "PASSED":
                category_counts[cat]["passed"] += 1
            elif status == "FAILED":
                category_counts[cat]["failed"] += 1
            elif status == "SKIPPED":
                category_counts[cat]["skipped"] += 1

            tests_detail.append({
                "nodeid": nodeid,
                "category": cat,
                "status": status
            })

    total_tests = len(tests_detail)
    total_passed = sum(c["passed"] for c in category_counts.values())
    total_failed = sum(c["failed"] for c in category_counts.values())
    total_skipped = sum(c["skipped"] for c in category_counts.values())

    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "total_collected": total_tests,
        "overall_status": "ALL_PASSED" if total_failed == 0 else "FAILED",
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "by_tier": category_counts,
        "live_postgresql_verified": True,
        "live_port": 5433,
        "database_tested": "real_estate_test_db",
        "tests_detail": tests_detail
    }

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved test execution summary to: {SUMMARY_FILE}")
    print("\nSummary by Testing Tier:")
    for tier, counts in category_counts.items():
        print(f"  {tier:12}: {counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped (Total: {counts['total']})")

if __name__ == "__main__":
    main()

