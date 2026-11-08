"""Content and catalog validation outside timed query execution."""
import csv
import hashlib
import json
from datetime import datetime
from decimal import Decimal

from scripts.import_csv import COLUMNS


def canonical(row):
    values = list(row)
    values[0] = int(values[0])
    for index in (4, 5, 6):
        if values[index] == '': values[index] = None
    if values[6] is not None: values[6] = str(Decimal(str(values[6])).normalize())
    values[7] = float(values[7])
    values[8] = str(datetime.fromisoformat(str(values[8])))
    return json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n'


def fingerprint(rows):
    digest = hashlib.sha256(); count = 0
    for row in rows:
        digest.update(canonical(row)); count += 1
    return {'rows':count, 'content_sha256':digest.hexdigest()}


def csv_fingerprint(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.reader(stream)
        if next(reader)!=COLUMNS: raise ValueError('CSV schema mismatch')
        result=fingerprint(reader)
    result['csv_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def database_fingerprint(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT '+','.join(COLUMNS)+' FROM public.properties ORDER BY id')
        return fingerprint(iter(cur))


def result_digest(conn, query, ordered=False):
    with conn.cursor() as cur:
        cur.execute(query); rows=cur.fetchall()
    values=[json.dumps(row,default=str,ensure_ascii=False) for row in rows]
    if not ordered: values.sort()
    return hashlib.sha256('\n'.join(values).encode()).hexdigest()


def validate_catalog(indexes, supplemental):
    expected={'idx_properties_province_name':'(province_name)',
              'idx_properties_location_price':'(province_name, district_name, price, id)',
              'idx_properties_published_at':'(published_at)',
              'idx_properties_property_type':'(property_type_name)'}
    primary=[i for i in indexes if i['indisprimary']]
    if len(primary)!=1 or not primary[0]['indisvalid'] or '(id)' not in primary[0]['index_definition']:
        raise ValueError('Invalid primary key catalog')
    others=[i for i in indexes if not i['indisprimary']]
    if len(others)!=(1 if supplemental else 0): raise ValueError('Unexpected index count')
    for index in others:
        definition=index['index_definition']
        if not index['indisvalid'] or index['index_name']!=supplemental or 'USING btree '+expected[supplemental] not in definition:
            raise ValueError('Invalid supplemental index definition')
