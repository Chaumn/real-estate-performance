import json
import pandas as pd

with open('results/build_report_500000.json', 'r', encoding='utf-8') as f:
    br = json.load(f)

with open('results/quality/data_quality_report_500000.json', 'r', encoding='utf-8') as f:
    dq = json.load(f)

df_proc = pd.read_csv('results/processing_benchmark/processing_benchmark.csv')
df_bench = pd.read_csv('results/benchmark/benchmark_results.csv')

with open('scripts/reference_summary.txt', 'w', encoding='utf-8') as out:
    def p(*args):
        out.write(" ".join(str(a) for a in args) + "\n")

    p("=== 1. BUILD REPORT ===")
    for k in ['source_rows_read', 'invalid_rows', 'invalid_by_reason', 'valid_rows_seen', 'valid_rows_not_exported', 'exported_rows', 'null_counts']:
        p(k, ":", br.get(k))

    p("\n=== 2. DATA QUALITY SUMMARY ===")
    p("File size MB:", dq['file_size_mb'])
    for col, v in dq['column_summary'].items():
        p(f"{col}: missing={v['missing_count']} ({v['missing_pct']}%), unique={v['unique_count']}")

    p("\n=== 3. NUMERIC STATS ===")
    for col, v in dq['numeric_stats'].items():
        p(f"{col}: min={v['min']}, max={v['max']}, mean={v['mean']:.2f}, median={v['median']:.2f}, std={v['std']:.2f}, iqr={v['iqr']:.2f}")

    p("\n=== 4. PROVINCES ===")
    for prov, v in list(dq['categorical_distributions']['top_provinces'].items())[:15]:
        p(f"{prov}: {v['count']} ({v['pct']}%)")

    p("\n=== 5. PROPERTY TYPES ===")
    for pt, v in dq['categorical_distributions']['property_type_distribution'].items():
        p(f"{pt}: {v['count']} ({v['pct']}%)")

    p("\n=== 6. DUPLICATES ===")
    d = dq['duplicate_analysis']
    p(f"exact_duplicates_excl_id: {d.get('exact_duplicates_excl_id')}, suspected_duplicates: {d.get('suspected_duplicates')} ({d.get('suspected_duplicate_pct')}%)")

    p("\n=== 7. BENCHMARK SUMMARY (SCALES & CONFIGS) ===")
    for scale in [50000, 200000, 500000]:
        p(f"--- Scale {scale} ---")
        sub = df_bench[df_bench['scale'] == scale]
        for _, r in sub.iterrows():
            p(f"  {r['config_id']:12} | {r['dominant_scan_type']:16} | idx={str(r['indexes_used']):28} | size={r['index_size_mb']:5.2f}MB | med={r['execution_time_median_ms']:7.3f}ms | iqr={r['execution_time_iqr_ms']:6.3f}ms | hits={r['shared_hit_blocks_median']:7.0f} | reads={r['shared_read_blocks_median']:3.0f} | speedup={r['speedup']:6.2f}x")
