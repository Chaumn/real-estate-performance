"""Finalize checksums and verify portable package links and ZIP bytes."""
import csv
import hashlib
import json
import platform
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def finalize(root=Path('deliverables/tv2')):
    suites = ET.parse(root/'evidence/offline_tests.xml').getroot()
    cases = suites.findall('.//testcase')
    failed = sum(c.find('failure') is not None for c in cases)
    errors = sum(c.find('error') is not None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    record = dict(passed=len(cases)-failed-errors-skipped, failed=failed, errors=errors, skipped=skipped,
                  scope='offline; live module excluded', live_status='NOT_RUN', python=platform.python_version(),
                  commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  command='python -B -m pytest -q -rs -p no:cacheprovider --ignore=tests/test_live_postgresql_e2e.py --junitxml=deliverables/tv2/evidence/offline_tests.xml', source='evidence/offline_tests.xml')
    with (root/'tables/test_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=record);writer.writeheader();writer.writerow(record)
    (root/'tables/test_summary.md').write_text('\n'.join(f'- {k}: {v}' for k,v in record.items()),encoding='utf-8')
    rows=list(csv.DictReader((root/'tables/benchmark_summary.csv').open(encoding='utf-8-sig')))
    assert len(rows)==30 and len({(r['scale'],r['configuration']) for r in rows})==30
    html=root/'dashboard/index.html'
    for link in re.findall(r'(?:href|src)="([^"]+)"',html.read_text(encoding='utf-8')):
        if '${' not in link: assert (html.parent/link).is_file(),link
    for row in rows: assert (root/'evidence'/row['representative_plan']).is_file()
    report={'table_rows':len(rows),'static_links':'PASS','representative_links':'PASS','visual_review':'Contact sheet reviewed; Vietnamese labels visible, no apparent clipping','browser_smoke':'NOT_RUN: Playwright CLI unavailable locally','postgresql':'BLOCKED: connection timeout on 127.0.0.1:5433','benchmark_acceptance':'NOT_ACCEPTED','tests':record}
    (root/'evidence/package_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    artifacts=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt'):
            sources=['evidence/offline_tests.xml'] if 'test_summary' in p.name else ['evidence/build_report.json'] if 'FIG08' in p.name else ['evidence/benchmark_raw_plans.zip','tables/benchmark_summary.csv']
            artifacts.append(dict(path=p.relative_to(root).as_posix(),type=p.suffix,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_files=sources,status='HISTORICAL' if 'test' not in p.name else 'OFFLINE_ONLY'))
    (root/'manifest.json').write_text(json.dumps({'status':'PARTIAL','artifacts':artifacts,'limitations':report},ensure_ascii=False,indent=2),encoding='utf-8')
    files=[p for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt']
    (root/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix() for p in files),encoding='utf-8')
    target=root.parent/'tv2.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(root.parent))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in z.namelist(): assert z.read(name)==(root.parent/name).read_bytes()
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':finalize()
