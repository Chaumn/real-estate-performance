"""Distinct analytical projections of measured benchmark records."""


def analytical_tables(rows, groups, statistics):
    lookup = {(r['scale'], r['configuration']): r for r in rows}
    execution, comparisons, scaling, indexes = [], [], [], []
    for row in rows:
        scale, config = row['scale'], row['configuration']
        identity = dict(scale=scale, configuration=config, status='HISTORICAL')
        plans = groups[f'{scale}_{config}']
        stats = dict(identity)
        for field, prefix in [('Execution Time', 'execution'), ('Planning Time', 'planning')]:
            for metric, value in statistics([p[0][field] for _, p in plans]).items():
                stats[f'{prefix}_{metric}_ms'] = value
        execution.append(stats)
        baseline = 'Q3_A' if row['query']=='Q3' else row['query']+'_baseline'
        base = lookup[scale, baseline]['median_ms']
        if config != baseline:
            comparisons.append(dict(identity, baseline=baseline, baseline_ms=base,
                configuration_ms=row['median_ms'], reduction_ms=base-row['median_ms'],
                reduction_percent=(base-row['median_ms'])/base*100 if base else None,
                speedup=base/row['median_ms'] if row['median_ms'] else None))
        first = min(r['scale'] for r in rows if r['configuration']==config)
        initial = lookup[first,config]['median_ms']
        scaling.append(dict(identity, reference_scale=first, row_multiplier=scale/first,
            median_ms=row['median_ms'], latency_multiplier=row['median_ms']/initial if initial else None))
        used = set()
        def visit(node):
            if 'Index Name' in node: used.add(node['Index Name'])
            for child in node.get('Plans',[]): visit(child)
        for _,plan in plans: visit(plan[0]['Plan'])
        indexes.append(dict(identity, index_bytes=row['index_bytes_historical'],
            bytes_per_row=row['index_bytes_historical']/scale, scan_types=row['scan'],
            indexes_used=','.join(sorted(used)), size_source='historical summary; not EXPLAIN'))
    return {'execution_statistics':execution,'query_comparison':comparisons,
            'scaling_analysis':scaling,'index_analysis':indexes}
