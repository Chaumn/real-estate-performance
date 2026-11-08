from scripts.benchmark_tables import analytical_tables
from scripts.benchmark_runner import compute_statistics


def test_distinct_tables_and_measured_formulas():
    rows=[]; groups={}
    for scale, factor in [(50000,1),(200000,3)]:
        for config, elapsed in [('Q1_baseline',8),('Q1_indexed',2)]:
            rows.append(dict(scale=scale,configuration=config,query='Q1',median_ms=elapsed*factor,
                index_bytes_historical=0 if config.endswith('baseline') else 100,
                scan='Seq Scan'))
            groups[f'{scale}_{config}']=[('fixture',[{'Execution Time':elapsed*factor,'Planning Time':.5,'Plan':{'Node Type':'Seq Scan'}}])]
    tables=analytical_tables(rows,groups,compute_statistics)
    assert len({tuple(records[0]) for records in tables.values()})==4
    comparison=tables['query_comparison'][0]
    assert comparison['speedup']==4
    assert comparison['reduction_ms']==6
    assert comparison['reduction_percent']==75
    assert tables['execution_statistics'][0]['planning_median_ms']==.5
    assert tables['scaling_analysis'][2]['row_multiplier']==4
    assert tables['scaling_analysis'][2]['latency_multiplier']==3
