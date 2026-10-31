"""Offline guards against changing the accepted queries or index isolation.

These checks compare tokens in this fixed set of SQL assets. They are not a
general PostgreSQL parser and do not assert an execution plan or performance.
"""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "sql/benchmark"
TOKEN = re.compile(r"'(?:''|[^'])*'|::|>=|<=|<>|!=|\w+|[^\s]", re.UNICODE)
CREATE_INDEX = re.compile(
    r"CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+)\s+"
    r"ON\s+public\.properties\s+(?:USING\s+(?P<method>\w+)\s*)?"
    r"\((?P<columns>[^)]*)\)\s*;",
    re.IGNORECASE,
)

INDEX_CASES = [
    ("q1_province_name.sql", "idx_properties_province_name",
     ("province_name",), "q1_single_column_index.sql"),
    ("q2_location_price.sql", "idx_properties_location_price",
     ("province_name", "district_name", "price", "id"), "q2_composite_index.sql"),
    ("q3_published_at.sql", "idx_properties_published_at",
     ("published_at",), "q3_query_rewriting.sql"),
    ("q4_property_type.sql", "idx_properties_property_type",
     ("property_type_name",), "q4_aggregation_control.sql"),
]
QUERY_CASES = [
    ("q1.sql", "q1_single_column_index.sql", True),
    ("q2.sql", "q2_composite_index.sql", True),
    ("q3_original.sql", "q3_query_rewriting.sql", True),
    ("q3_rewritten.sql", "q3_query_rewriting.sql", False),
    ("q4.sql", "q4_aggregation_control.sql", True),
]


def read_sql(path):
    # These assets have line comments and no "--" inside their literals.
    return re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8-sig")).strip()


def tokens(sql):
    # Preserve the exact case, accents and values of string/date literals.
    return tuple(token if token.startswith("'") else token.casefold()
                 for token in TOKEN.findall(sql))


def accepted_selects(path):
    return [
        tokens(statement)
        for statement in re.findall(r"\bSELECT\b.*?;", read_sql(path), re.IGNORECASE | re.DOTALL)
    ]


@pytest.mark.parametrize("filename,original_file,in_baseline", QUERY_CASES)
def test_pure_select_matches_accepted_queries(filename, original_file, in_baseline):
    query = tokens(read_sql(BENCHMARK / "queries" / filename))
    assert query[0] == "select"
    assert query[-1] == ";"
    assert query.count(";") == 1
    assert query in accepted_selects(ROOT / "sql/optimizations" / original_file)
    if in_baseline:
        assert query in accepted_selects(ROOT / "sql/baseline_queries.sql")


@pytest.mark.parametrize("filename,index_name,columns,original_file", INDEX_CASES)
def test_index_is_single_accepted_btree_without_other_commands(
    filename, index_name, columns, original_file
):
    statement = read_sql(BENCHMARK / "indexes" / filename)
    match = CREATE_INDEX.fullmatch(statement)
    assert match is not None
    assert match["name"] == index_name
    assert match["method"].casefold() == "btree"
    assert tuple(part.strip() for part in match["columns"].split(",")) == columns

    accepted = list(CREATE_INDEX.finditer(read_sql(ROOT / "sql/optimizations" / original_file)))
    assert len(accepted) == 1
    assert accepted[0]["name"] == index_name
    assert (accepted[0]["method"] or "btree").casefold() == match["method"].casefold()
    assert tuple(part.strip() for part in accepted[0]["columns"].split(",")) == columns


def test_reset_drops_exactly_four_named_indexes_without_cascade_or_primary_key():
    statements = read_sql(BENCHMARK / "reset_indexes.sql").split(";")
    assert not statements[-1].strip()
    actual = [tokens(statement) for statement in statements[:-1]]
    expected = [
        ("drop", "index", "if", "exists", "public", ".", index_name)
        for _, index_name, _, _ in INDEX_CASES
    ]
    assert len(actual) == 4
    assert set(actual) == set(expected)


def test_only_requested_query_and_index_files_are_present():
    assert {path.name for path in (BENCHMARK / "queries").glob("*.sql")} == {
        filename for filename, _, _ in QUERY_CASES
    }
    assert {path.name for path in (BENCHMARK / "indexes").glob("*.sql")} == {
        filename for filename, _, _, _ in INDEX_CASES
    }
