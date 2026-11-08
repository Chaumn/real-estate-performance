from scripts.benchmark_validation import fingerprint, validate_catalog
import pytest


def test_same_count_changed_content_detected():
    row=[1,'name','type','province',None,None,100,20,'2025-01-01 00:00:00']
    changed=row.copy(); changed[1]='changed'
    assert fingerprint([row])['rows']==fingerprint([changed])['rows']
    assert fingerprint([row])!=fingerprint([changed])


def test_invalid_catalog_rejected():
    with pytest.raises(ValueError): validate_catalog([],None)
    with pytest.raises(ValueError): validate_catalog([{'indisprimary':True,'indisvalid':False,'index_definition':'(id)'}],None)
