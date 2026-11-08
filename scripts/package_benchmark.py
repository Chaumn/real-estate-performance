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

def build(output, experiment=None):
    output.mkdir(parents=True, exist_ok=True)
    for directory in ('tables','figures','evidence','dashboard'):
        (output/directory).mkdir(exist_ok=True)
    source = ROOT/'results/benchmark/benchmark_raw_plans.zip'
    trusted = json.loads((ROOT/'report/benchmark_manifest.json').read_text(encoding='utf-8'))['plans']
    source_dir = ROOT/'results/benchmark'
    if experiment:
        source_dir = Path(experiment).resolve()
        meta = json.loads((source_dir/'experiment.json').read_text())
        if meta['status']!='COMPLETED' or meta['official_runs']!=20 or meta['warmups']!=3:
            raise ValueError('Experiment is incomplete')
        source = source_dir/'benchmark_raw_plans.zip'
        if not source.exists():
            with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED) as archive:
                for path in sorted((source_dir/'raw').glob('*.json')): archive.write(path,path.name)
        trusted = {p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (source_dir/'raw').glob('*.json')}
        for path in source_dir.glob('*.json'): shutil.copy2(path,output/'evidence'/path.name)
    summary = json.loads((source_dir/'benchmark_summary.json').read_text(encoding='utf-8'))
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
    table('benchmark_summary', rows)
    from scripts.benchmark_tables import analytical_tables
    for name, records in analytical_tables(rows, groups, compute_statistics).items():
        table(name, records)
    table('q3_factorial_analysis',[{'scale':scale,'comparison':a+'/'+b,'speedup':lookup[scale,a]['median_ms']/lookup[scale,b]['median_ms']} for scale in (50000,200000,500000) for a,b in [('Q3_A','Q3_B'),('Q3_C','Q3_D'),('Q3_A','Q3_C'),('Q3_B','Q3_D')]])
    shutil.copy2(source,output/'evidence'/source.name)
    if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256((output/'evidence'/source.name).read_bytes()).digest(): raise ValueError('Copy mismatch')
    shutil.copy2(ROOT/'results/benchmark/environment_info.json',output/'evidence/environment_historical.json')
    limitations=['Historical evidence only; no new PostgreSQL execution','Dataset revision not proven','Historical hardware metadata inconsistent','Database immutability and equivalence not proven','Warm-up execution not independently proven']
    (output/'README.md').write_text('# TV2 — PARTIAL\n\nHistorical artifacts only. Open tables/*.md for verified recalculated timings.\n\n'+'\n'.join('- '+x for x in limitations),encoding='utf-8')
    from scripts.handoff_assets import complete_assets
    complete_assets(output, rows, groups, 'LIVE_MEASURED' if experiment else 'HISTORICAL')
    if experiment:
        status='LIVE_MEASURED — nghiệm thu provenance còn giới hạn'
        # Presentation assets must clearly distinguish this experiment from history.
        for path in list((output/'tables').glob('*'))+[output/'dashboard/index.html',output/'chapter5_handoff.md',output/'README.md']:
            content=path.read_text(encoding='utf-8-sig').replace('HISTORICAL','LIVE_MEASURED')
            path.write_text(content,encoding='utf-8')
        (output/'evidence/source_status.json').write_text(json.dumps({'experiment_id':meta['experiment_id'],'status':'LIVE_MEASURED','source_revision':'UNPROVEN','official_plans':600,'warmups':90},indent=2),encoding='utf-8')
        env=summary['environment']
        narrative = '# Chương 5 — thí nghiệm mới LIVE_MEASURED\n\n'
        narrative += '## 5.1 Môi trường thực nghiệm\n\n'+json.dumps(env,ensure_ascii=False,indent=2)+'\n\n'
        narrative += '## 5.2 Vận hành hệ thống\n\nExperiment `'+meta['experiment_id']+'`: 3 quy mô, 10 cấu hình, 3 warm-up và 20 lượt chính thức. Importer production, kiểm tra rollback 50K và fingerprint được lưu trong evidence. Database real_estate_db độc lập; khóa SHARE trong mỗi quy mô chặn writer khác. Settings session đo và catalog/equivalence từng cấu hình có trong evidence.\n\n'
        narrative += '## 5.3 Kết quả Q1–Q4\n\n'
        for row in rows:
            narrative += f"- {row['scale']} / {row['configuration']}: median {row['median_ms']} ms, IQR {row['iqr_ms']} ms, speedup {row['speedup']:.3f}.\n"
        narrative += '\n## 5.4 Khả năng mở rộng\n\nXem [scaling_analysis](tables/scaling_analysis.md) và [FIG03](figures/FIG03.png). Tỷ lệ latency được tính so với 50K; ba tập là prefix nên không phải các mẫu độc lập.\n\n'
        narrative += '## 5.5 Giải thích kết quả\n\nXem [Q3 factorial](tables/q3_factorial_analysis.md): A/B và C/D tách rewriting; A/C và B/D tách index. [FIG06](figures/FIG06.png) đếm node scan thực sự, không đếm truy vấn. Q4 là đối chứng, không giả định index luôn nhanh hơn. [index_analysis](tables/index_analysis.md) ghi index usage và dung lượng.\n\n'
        narrative += '## 5.6 Hạn chế thực nghiệm\n\nRevision upstream chưa chứng minh; SHA CSV chỉ khóa đầu vào hiện tại. Thí nghiệm warm-cache, không cold-cache; EXPLAIN có overhead. Chưa kiểm soát toàn bộ tải nền, autovacuum và nhiễu hệ điều hành; IQR và min/max phải đi kèm median. Không trộn với 600 plan lịch sử. Chưa nghiệm thu browser/visual QA mới; không khẳng định tính tổng quát ngoài máy và workload này.\n'
        (output/'chapter5_handoff.md').write_text(narrative,encoding='utf-8')
    artifacts=[]
    for p in sorted(output.rglob('*')):
        if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt'): artifacts.append({'path':p.relative_to(output).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'HISTORICAL','source_files':[str(source.relative_to(ROOT))]})
    (output/'manifest.json').write_text(json.dumps({'status':'PARTIAL','valid_official_plans':600,'limitations':limitations,'artifacts':artifacts},indent=2),encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text('\n'.join(f"{a['sha256']}  {a['path']}" for a in artifacts),encoding='utf-8')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',type=Path)
    args=parser.parse_args()
    build(ROOT/'deliverables/tv2',args.experiment)
