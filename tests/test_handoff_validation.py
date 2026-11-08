import json
import shutil
from pathlib import Path
import pytest
from scripts.validate_handoff import verify, provenance
from scripts.benchmark_tables import analytical_tables
from scripts.benchmark_runner import compute_statistics

ROOT=Path('deliverables/tv2')

def test_packaged_arithmetic():
    assert verify(ROOT)['mismatches']==0

@pytest.mark.parametrize('damage',['missing','size','fingerprint'])
def test_missing_or_changed_catalog_fails(tmp_path,damage):
    root=tmp_path/'tv2'
    shutil.copytree(ROOT,root)
    p=root/'evidence/50000_validation.json'
    if damage=='missing': p.unlink()
    else:
        data=json.loads(p.read_text())
        if damage=='size': data['configurations']['Q1_baseline']['catalog']['index_bytes']=1
        else: data['after']['content_sha256']='incorrect'
        p.write_text(json.dumps(data))
    with pytest.raises((AssertionError,FileNotFoundError)): verify(root)

def test_provenance_categories():
    assert provenance(Path('environment_historical.json'),'live')[0]=='HISTORICAL_REFERENCE'
    assert provenance(Path('environment_info.json'),'live')[0]=='LIVE_POSTGRESQL_EXPERIMENT'
    assert provenance(Path('FIG08.png'),'live')[0]=='DATASET_QUALITY_BUILD_REPORT'
    assert provenance(Path('regression_current.xml'),'live')[0]=='FULL_REGRESSION_INCLUDING_LIVE_TESTS'
    assert provenance(Path('environment_info.json'),'historical')[0]=='HISTORICAL_REFERENCE'

@pytest.mark.parametrize('mode,status',[('live','LIVE_MEASURED'),('historical','HISTORICAL')])
def test_table_mode(mode,status):
    row=dict(scale=50000,configuration='Q1_baseline',query='Q1',median_ms=1,index_bytes=0,scan='Seq Scan')
    groups={'50000_Q1_baseline':[('fixture',[{'Execution Time':1,'Planning Time':0,'Plan':{}}])]}
    result=analytical_tables([row],groups,compute_statistics,mode)
    assert result['index_analysis'][0]['status']==status
    assert ('validation.json' in result['index_analysis'][0]['size_source'])==(mode=='live')

@pytest.mark.parametrize('mode',['historical','live'])
def test_package_generation_provenance(tmp_path, monkeypatch, mode):
    import zipfile
    from scripts import package_benchmark, handoff_assets
    monkeypatch.setattr(handoff_assets,'complete_assets',lambda *args: None)
    source=None
    if mode=='live':
        source=tmp_path/'experiment'
        shutil.copytree(ROOT/'evidence',source)
        with zipfile.ZipFile(source/'benchmark_raw_plans.zip') as z:
            z.extractall(source/'raw')
    output=tmp_path/'package'
    package_benchmark.build(output,source)
    import csv
    rows=list(csv.DictReader((output/'tables/benchmark_summary.csv').open(encoding='utf-8-sig')))
    assert len(rows)==30
    assert {r['status'] for r in rows}==({'LIVE_MEASURED'} if mode=='live' else {'HISTORICAL'})
    assert 'index_bytes' in rows[0] and 'index_bytes_historical' not in rows[0]
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='NOT_VALIDATED'
    artifact=next(a for a in manifest['artifacts'] if a['path']=='evidence/environment_historical.json')
    assert artifact['status']=='HISTORICAL_REFERENCE'
    with pytest.raises(ValueError,match='empty output'): package_benchmark.build(output,source)
