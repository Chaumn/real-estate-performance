"""Offline evidence verification; never connects to PostgreSQL or infers browser QA."""
import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from scripts.benchmark_runner import compute_statistics
from scripts.benchmark_tables import analytical_tables


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def provenance(path, mode):
    name = path.name
    if name in ('environment_historical.json', 'prior_validation.json', 'offline_tests.xml'):
        return 'HISTORICAL_REFERENCE', ['evidence/'+name]
    if name == 'build_report.json' or name.startswith('FIG08'):
        return 'DATASET_QUALITY_BUILD_REPORT', ['evidence/build_report.json']
    if name == 'regression_current.xml' or name.startswith('test_summary'):
        return 'FULL_REGRESSION_INCLUDING_LIVE_TESTS', ['evidence/regression_current.xml', 'evidence/prior_validation.json']
    if name in ('package_validation.json', 'offline_revision.xml', 'packaging_revision.xml', 'integrity_check.json'):
        return 'OFFLINE_VERIFICATION', ['evidence/benchmark_raw_plans.zip', 'evidence/offline_revision.xml']
    if path.suffix == '.md' and path.parent.name != 'tables':
        return 'DOCUMENTATION', ['evidence/package_validation.json']
    if mode == 'live' and (name.startswith(('benchmark_summary','index_analysis','FIG07'))):
        return 'LIVE_POSTGRESQL_EXPERIMENT', ['evidence/benchmark_raw_plans.zip'] + [f'evidence/{scale}_validation.json' for scale in (50000,200000,500000)]
    return ('LIVE_POSTGRESQL_EXPERIMENT' if mode == 'live' else 'HISTORICAL_REFERENCE'), ['evidence/experiment.json', 'evidence/benchmark_raw_plans.zip'] if mode == 'live' else ['evidence/benchmark_raw_plans.zip']


def verify(root):
    rows=list(csv.DictReader((root/'tables/benchmark_summary.csv').open(encoding='utf-8-sig')))
    assert len(rows)==30 and len({(r['scale'],r['configuration']) for r in rows})==30
    meta=read_json(root/'evidence/experiment.json')
    assert meta['status']=='COMPLETED' and meta['official_runs']==20 and meta['warmups']==3
    assert read_json(root/'evidence/source_status.json')['experiment_id']==meta['experiment_id']==read_json(root/'evidence/acceptance_checks.json')['experiment_id']
    assert read_json(root/'evidence/live_import.json')['rollback']=='PASSED'
    groups=defaultdict(list)
    with zipfile.ZipFile(root/'evidence/benchmark_raw_plans.zip') as archive:
        assert len(archive.namelist()) == len(set(archive.namelist())) == 600
        for name in archive.namelist():
            groups[Path(name).name.rsplit('_run',1)[0]].append((Path(name).name,json.loads(archive.read(name))))
    converted=[]
    for row in rows:
        scale=int(row['scale']); config=row['configuration']; key=f'{scale}_{config}'
        plans=groups[key]
        assert {n for n,_ in plans}=={f'{key}_run{i:02d}.json' for i in range(1,21)}
        stats=compute_statistics([p[0]['Execution Time'] for _,p in plans])
        for field in ('median','iqr','min','max'): assert float(row[field+'_ms'])==stats[field], (key,field)
        validation=read_json(root/f'evidence/{scale}_validation.json')
        assert validation['csv']['content_sha256']==validation['before']['content_sha256']==validation['after']['content_sha256']
        entry=validation['configurations'][config]
        assert entry['equivalence']=='PASSED'
        assert all(i['indisvalid'] for i in entry['catalog']['active_indexes'])
        assert int(row['index_bytes'])==entry['catalog']['index_bytes']
        for n in range(1,4):
            warm=read_json(root/f'evidence/{key}_warmup{n:02d}.json')
            assert 'Execution Time' in warm[0]
        assert read_json(root/'evidence'/row['representative_plan'])==dict(plans)[row['representative_plan']]
        converted.append(dict(row,scale=scale,median_ms=float(row['median_ms']),index_bytes=int(row['index_bytes'])))
    lookup={(r['scale'],r['configuration']):r for r in converted}
    for row in converted:
        base='Q3_A' if row['query']=='Q3' else row['query']+'_baseline'
        assert float(row['speedup'])==lookup[row['scale'],base]['median_ms']/row['median_ms']
    expected=analytical_tables(converted,groups,compute_statistics,'live')
    expected['q3_factorial_analysis']=[dict(scale=s,comparison=a+'/'+b,speedup=lookup[s,a]['median_ms']/lookup[s,b]['median_ms']) for s in (50000,200000,500000) for a,b in [('Q3_A','Q3_B'),('Q3_C','Q3_D'),('Q3_A','Q3_C'),('Q3_B','Q3_D')]]
    for name, records in expected.items():
        actual=list(csv.DictReader((root/f'tables/{name}.csv').open(encoding='utf-8-sig')))
        assert len(actual)==len(records)
        for got,want in zip(actual,records):
            for key,value in want.items():
                assert (float(got[key])==value if isinstance(value,(int,float)) else got[key]==str(value)), (name,key,got[key],value)
    html=(root/'dashboard/index.html').read_text(encoding='utf-8')
    assert 'EXPERIMENT_ACCEPTED' not in html
    payload=json.loads(re.search(r'const rows=(.*?);const scale=',html).group(1))
    for got,want in zip(payload,converted):
        for key in ('scale','configuration','median_ms','iqr_ms','speedup','min_ms','max_ms','runs'):
            assert str(got[key])==str(want[key]) or float(got[key])==float(want[key])
    for got,want in zip(payload,converted):
        assert got.get('index_bytes',got.get('index_bytes_historical'))==want['index_bytes']
    assert len(payload)==30
    for link in re.findall(r'(?:href|src)="([^"]+)"',html):
        if '${' not in link: assert (root/'dashboard'/link).is_file(),link
    for i in range(1,9):
        for ext in ('png','svg'): assert (root/f'figures/FIG{i:02d}.{ext}').is_file()
    return {'execution_statistics':30,'query_comparison':18,'scaling_analysis':30,'q3_factorial_analysis':12,'catalog_configurations':30,'official_plans':600,'warmups':90,'mismatches':0}


def write_inventory(root, report, mode):
    artifacts=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt'):
            status,sources=provenance(p,mode)
            artifacts.append(dict(path=p.relative_to(root).as_posix(),sha256=digest(p),status=status,source_files=sources))
    (root/'manifest.json').write_text(json.dumps(dict(status=report['benchmark_acceptance'],delivery_status=report['delivery_status'],artifacts=artifacts,validation=report),ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'SHA256SUMS.txt').write_text('\n'.join(digest(p)+'  '+p.relative_to(root).as_posix() for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')


def finalize(root=Path('deliverables/tv2')):
    counts=verify(root) # Fail closed before publishing an acceptance record.
    prior=read_json(root/'evidence/prior_validation.json')
    cases=ET.parse(root/'evidence/regression_current.xml').getroot().findall('.//testcase')
    failed=sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
    skipped=sum(c.find('skipped') is not None for c in cases)
    assert failed==0 and len(cases)-skipped==prior['tests']['passed'] and skipped==prior['tests']['skipped']
    live=[c for c in cases if 'live_postgresql' in c.get('classname','')]
    assert live and all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in live)
    current=ET.parse(root/'evidence/offline_revision.xml').getroot().findall('.//testcase')
    assert current and all(c.find('failure') is None and c.find('error') is None for c in current)
    current_tests=dict(passed=sum(c.find('skipped') is None for c in current),skipped=sum(c.find('skipped') is not None for c in current),failed=0,scope='offline revision working tree based on c7a93a7; live module excluded',source='evidence/offline_revision.xml')
    report=dict(verified=counts,benchmark_acceptance='EXPERIMENT_EVIDENCE_VERIFIED_OFFLINE',delivery_status='PACKAGE_INTEGRITY_VERIFIED',
        postgresql='NOT_RUN_CURRENT; archived experiment evidence verified offline',
        browser_smoke='PRIOR_REPORTED_PASS: DOM rendering only; not independently rerun',
        cdp_interaction='NOT_VERIFIED; no reproducible interaction evidence',
        visual_review='PRIOR_REPORTED_PASS: contact sheet and Vietnamese labels only; no new visual review',
        tests=prior['tests'],current_tests=current_tests,handoff_baseline='c7a93a7',
        limitations=['No current database connection or benchmark execution','Prior regression attribution remains c51b2c2','Historical collation C differs from experiment English_United States.1252; environment equivalence unproven'])
    (root/'evidence/package_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    write_inventory(root,report,'live')
    target=root.parent/'tv2.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(root.parent))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in z.namelist(): assert z.read(name)==(root.parent/name).read_bytes()
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': finalize()
