"""Build a portable, explicitly historical handoff from immutable archived plans."""
import csv
import hashlib
import json
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path
from scripts.benchmark_runner import compute_statistics, extract_plan_metrics

ROOT = Path(__file__).resolve().parents[1]

def build(output):
    output.mkdir(parents=True, exist_ok=True)
    for directory in ('tables','figures','evidence','dashboard'):
        (output/directory).mkdir(exist_ok=True)
    source = ROOT/'results/benchmark/benchmark_raw_plans.zip'
    trusted = json.loads((ROOT/'report/benchmark_manifest.json').read_text(encoding='utf-8'))['plans']
    summary = json.loads((ROOT/'results/benchmark/benchmark_summary.json').read_text(encoding='utf-8'))
    groups = defaultdict(list)
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        for name in names:
            base = Path(name).name
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != trusted[base]['sha256']:
                raise ValueError('SHA mismatch: '+base)
            data = json.loads(payload)
            if not isinstance(data,list) or len(data)!=1 or 'Execution Time' not in data[0] or 'Planning Time' not in data[0]:
                raise ValueError('Invalid plan: '+base)
            groups[base.rsplit('_run',1)[0]].append((base,data))
    rows=[]
    for old in summary['flat_results']:
        key=f"{old['scale']}_{old['config_id']}"
        plans=groups[key]
        if {n for n,_ in plans}!={f'{key}_run{i:02d}.json' for i in range(1,21)}:
            raise ValueError('Invalid run matrix: '+key)
        stats=compute_statistics([p[0]['Execution Time'] for _,p in plans])
        if stats['median']!=old['execution_time_median_ms']:
            raise ValueError('Median mismatch: '+key)
        row={'scale':old['scale'],'query':old['query_id'],'configuration':old['config_id'],
             'runs':len(plans),'median_ms':stats['median'],'iqr_ms':stats['iqr'],'min_ms':stats['min'],'max_ms':stats['max'],
             'index_bytes_historical':old['index_bytes'],'status':'HISTORICAL'}
        metrics=extract_plan_metrics(plans[0][1])
        row['scan']=','.join(metrics['all_scan_types'])
        row['representative_plan']=plans[0][0]
        (output/'evidence'/plans[0][0]).write_text(json.dumps(plans[0][1],indent=2),encoding='utf-8')
        rows.append(row)
    if len(groups)!=30 or len(rows)!=30: raise ValueError('Invalid matrix')
    lookup={(r['scale'],r['configuration']):r for r in rows}
    for row in rows:
        base='Q3_A' if row['query']=='Q3' else row['query']+'_baseline'
        row['speedup']=lookup[row['scale'],base]['median_ms']/row['median_ms']
    def table(name, records):
        fields=list(records[0])
        with (output/'tables'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
        md='Status: HISTORICAL. Source: evidence/benchmark_raw_plans.zip. Time: ms; storage: bytes. Speedup = baseline median / configuration median. IQR = median upper half - median lower half. Index size comes from historical summary, not EXPLAIN.\n\n'
        md+='| '+' | '.join(fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'
        md+='\n'.join('| '+' | '.join(str(r[k]) for k in fields)+' |' for r in records)
        (output/'tables'/f'{name}.md').write_text(md,encoding='utf-8')
    for name in ('benchmark_summary','execution_statistics','query_comparison','scaling_analysis','index_analysis'):
        table(name,rows)
    table('q3_factorial_analysis',[{'scale':scale,'comparison':a+'/'+b,'speedup':lookup[scale,a]['median_ms']/lookup[scale,b]['median_ms']} for scale in (50000,200000,500000) for a,b in [('Q3_A','Q3_B'),('Q3_C','Q3_D'),('Q3_A','Q3_C'),('Q3_B','Q3_D')]])
    shutil.copy2(source,output/'evidence'/source.name)
    if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256((output/'evidence'/source.name).read_bytes()).digest(): raise ValueError('Copy mismatch')
    shutil.copy2(ROOT/'results/benchmark/environment_info.json',output/'evidence/environment_historical.json')
    limitations=['Historical evidence only; no new PostgreSQL execution','Dataset revision not proven','Historical hardware metadata inconsistent','Database immutability and equivalence not proven','Warm-up execution not independently proven']
    (output/'README.md').write_text('# TV2 — PARTIAL\n\nHistorical artifacts only. Open tables/*.md for verified recalculated timings.\n\n'+'\n'.join('- '+x for x in limitations),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure_specs = [
        ('FIG01','Median Execution Time theo c?u h?nh','median_ms','Th?i gian (ms)'),
        ('FIG02','Speedup so v?i baseline','speedup','Speedup (l?n)'),
        ('FIG03','Th?i gian theo quy m? d? li?u','median_ms','Th?i gian (ms)'),
        ('FIG04','Q3: Query Rewriting v? Index','median_ms','Th?i gian (ms)'),
        ('FIG05','Q4: tr??ng h?p ??i ch?ng','median_ms','Th?i gian (ms)'),
        ('FIG07','Dung l??ng index ? metadata l?ch s?','index_bytes_historical','Dung l??ng (byte)')]
    for name,title,metric,ylabel in figure_specs:
        fig,ax=plt.subplots(figsize=(12,6))
        configs=sorted({r['configuration'] for r in rows if (name!='FIG04' or r['query']=='Q3') and (name!='FIG05' or r['query']=='Q4')})
        for config in configs:
            selected=sorted([r for r in rows if r['configuration']==config],key=lambda r:r['scale'])
            ax.plot([r['scale'] for r in selected],[r[metric] for r in selected],marker='o',label=config)
        ax.set(title=title+' (HISTORICAL)',xlabel='S? b?n ghi',ylabel=ylabel,ylim=(0,None))
        ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout()
        fig.savefig(output/'figures'/f'{name}.png',dpi=300)
        fig.savefig(output/'figures'/f'{name}.svg');plt.close(fig)
    (output/'figures/README.md').write_text('Ngu?n: tables/benchmark_summary.csv, raw ZIP. FIG01/03/04/05: median 20 Execution Time; FIG02: median baseline / median c?u h?nh; FIG07: index_bytes t? summary l?ch s?, ch?a x?c minh catalog. FIG06 v? FIG08 ch?a t?o. Ch?a ki?m tra tr?c quan ?nh.',encoding='utf-8')
    from scripts.handoff_assets import complete_assets
    complete_assets(output, rows, groups)
    artifacts=[]
    for p in sorted(output.rglob('*')):
        if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt'): artifacts.append({'path':p.relative_to(output).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'HISTORICAL','source_files':[str(source.relative_to(ROOT))]})
    (output/'manifest.json').write_text(json.dumps({'status':'PARTIAL','valid_official_plans':600,'limitations':limitations,'artifacts':artifacts},indent=2),encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text('\n'.join(f"{a['sha256']}  {a['path']}" for a in artifacts),encoding='utf-8')

if __name__=='__main__':
    build(ROOT/'deliverables/tv2')
