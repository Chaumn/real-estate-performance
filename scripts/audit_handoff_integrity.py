"""Compare protected measurements with the original handoff commit, offline."""
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from scripts.validate_handoff import verify

BASE='c7a93a7876832fd70efcbcf32cda20958f0655e2'
ROOT=Path('deliverables/tv2')

def original(path):
    return subprocess.check_output(['git','cat-file','--filters',f'{BASE}:{path.as_posix()}'])

def main():
    protected=[]
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'deliverables/tv2/evidence','deliverables/tv2/figures'],text=True).splitlines()
    for name in paths:
        p=Path(name)
        if p.name in ('package_validation.json','README.md'): continue
        old=original(p)
        assert p.read_bytes()==old, name
        protected.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(old).hexdigest()))
    for name in ('benchmark_summary','execution_statistics','query_comparison','scaling_analysis','index_analysis','q3_factorial_analysis'):
        p=ROOT/f'tables/{name}.csv'
        before=list(csv.DictReader(io.StringIO(original(p).decode('utf-8-sig'))))
        after=list(csv.DictReader(p.open(encoding='utf-8-sig')))
        assert len(before)==len(after)
        for old,new in zip(before,after):
            if 'index_bytes_historical' in old: old['index_bytes']=old.pop('index_bytes_historical')
            old.pop('size_source',None);new.pop('size_source',None)
            assert old==new,(name,old,new)
    p=ROOT/'dashboard/index.html'
    def payload(text): return re.search(r'const rows=(.*?);const scale=',text).group(1)
    assert payload(original(p).decode('utf-8'))==payload(p.read_text(encoding='utf-8'))
    report=dict(baseline_commit=BASE,protected_files=protected,dashboard_payload_sha256=hashlib.sha256(payload(p.read_text(encoding='utf-8')).encode()).hexdigest(),measurements_unchanged=True,verified=verify(ROOT))
    (ROOT/'evidence/integrity_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'PASS: {len(protected)} protected files byte-identical; all table values and dashboard payload unchanged')

if __name__=='__main__': main()
