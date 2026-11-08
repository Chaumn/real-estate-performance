import json
import pytest
from scripts.benchmark_runner import extract_plan_metrics
from scripts.verify_benchmark_evidence import audit_raw_evidence


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf')])
def test_invalid_timing_rejected(value):
    with pytest.raises(ValueError):
        extract_plan_metrics([{'Plan': {}, 'Planning Time': 1, 'Execution Time': value}])


def test_missing_timing_rejected():
    with pytest.raises(KeyError):
        extract_plan_metrics([{'Plan': {}, 'Planning Time': 1}])


def test_verifier_rejects_invalid_identity_and_missing_runs(tmp_path):
    raw = tmp_path/'raw'; raw.mkdir()
    (raw/'50000_Q1_baseline_run99.json').write_text('[]')
    result = audit_raw_evidence(raw, tmp_path/'manifest.json')
    assert result['status'] == 'INVALID'
    assert result['errors']


def test_verifier_rejects_corrupt_json(tmp_path):
    raw = tmp_path/'raw'; raw.mkdir()
    (raw/'50000_Q1_baseline_run01.json').write_text('{')
    result = audit_raw_evidence(raw, tmp_path/'manifest.json')
    assert any('run01' in error for error in result['errors'])
