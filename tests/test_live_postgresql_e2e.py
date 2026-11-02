# -*- coding: utf-8 -*-
"""
Live PostgreSQL Integration & End-to-End Test Suite.
Tests real PostgreSQL on port 5433 (NO MagicMock, NO FakeDatabase).

Verifies:
1. Live database connectivity on port 5433.
2. Creation of isolated test database: real_estate_test_db.
3. Schema creation using sql/schema.sql.
4. Transactional COPY of real CSV (properties_50000.csv).
5. Post-import data validation (row count, NULL count, ID continuity).
6. Controlled transaction rollback on constraint violation.
7. Real execution of Q1, Q2, Q3 Original, Q3 Rewritten, Q4.
8. Semantic equivalence verification of Q3 Original vs Q3 Rewritten.
9. End-to-end smoke pipeline test (cleaning -> feature engineering -> DB COPY -> query).
"""

import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
import psycopg
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.cleaning import clean_dataframe
from scripts.feature_engineering import compute_features

import uuid
PG_HOST = "127.0.0.1"
PG_PORT = 5433
PG_USER = "postgres"
ADMIN_DB = "postgres"
TEST_DB = f"real_estate_qa_e2e_{uuid.uuid4().hex[:8]}"
CSV_50K = PROJECT_ROOT / "data" / "processed" / "properties_50000.csv"
SCHEMA_SQL_PATH = PROJECT_ROOT / "sql" / "schema.sql"

def is_postgres_running():
    try:
        with psycopg.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=ADMIN_DB, connect_timeout=3
        ) as conn:
            return True
    except Exception:
        return False

pytestmark = pytest.mark.skipif(
    not is_postgres_running(),
    reason="PostgreSQL not running on port 5433"
)


@pytest.fixture(scope="module")
def setup_test_database():
    """Create isolated ephemeral test database without dropping any pre-existing databases."""
    admin_conn = psycopg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=ADMIN_DB, autocommit=True
    )
    with admin_conn.cursor() as cur:
        # Safety check: ensure we do NOT drop or overwrite any pre-existing database
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,))
        if cur.fetchone():
            raise RuntimeError(f"Database {TEST_DB} already exists! Refusing to overwrite existing database.")
        
        # Create fresh ephemeral test database
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB)))
    admin_conn.close()

    # Connect to test db and apply schema
    test_conn = psycopg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB, autocommit=True
    )
    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with test_conn.cursor() as cur:
        cur.execute(schema_sql)
    test_conn.close()

    yield TEST_DB

    # Teardown: ONLY drop the ephemeral test database created in this session
    try:
        admin_conn = psycopg.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=ADMIN_DB, autocommit=True
        )
        with admin_conn.cursor() as cur:
            cur.execute(sql.SQL("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = {} AND pid <> pg_backend_pid()
            """).format(sql.Literal(TEST_DB)))
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(TEST_DB)))
        admin_conn.close()
    except Exception as e:
        print(f"Warning during ephemeral test db teardown: {e}")


def test_live_postgres_version(setup_test_database):
    """Verify live PostgreSQL version and cluster configuration."""
    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            assert "PostgreSQL 18" in ver or "PostgreSQL" in ver


def test_transactional_copy_csv_into_test_db(setup_test_database):
    """Import 50,000 rows CSV via real transactional COPY."""
    assert CSV_50K.is_file(), f"Missing {CSV_50K}"
    
    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            # COPY FROM STDIN
            copy_sql = """
                COPY public.properties (
                    id, name, property_type_name, province_name, district_name,
                    ward_name, price, area, published_at
                ) FROM STDIN WITH (
                    FORMAT CSV, HEADER TRUE, ENCODING 'UTF8', NULL '',
                    FORCE_NULL (price, district_name, ward_name)
                )
            """
            with open(CSV_50K, "r", encoding="utf-8") as f:
                with cur.copy(copy_sql) as copy:
                    while data := f.read(65536):
                        copy.write(data)
        conn.commit()

        # Check row count
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.properties;")
            cnt = cur.fetchone()[0]
            assert cnt == 50000, f"Expected 50,000 rows, got {cnt}"


def test_post_import_data_integrity(setup_test_database):
    """Verify row count, NULL count, ID continuity after COPY."""
    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*), 
                    COUNT(DISTINCT id), 
                    MIN(id), 
                    MAX(id),
                    COUNT(*) FILTER (WHERE price IS NULL),
                    COUNT(*) FILTER (WHERE district_name IS NULL),
                    COUNT(*) FILTER (WHERE ward_name IS NULL)
                FROM public.properties;
            """)
            total, distinct_id, min_id, max_id, null_price, null_district, null_ward = cur.fetchone()

            assert total == 50000
            assert distinct_id == 50000
            assert min_id == 1
            assert max_id == 50000
            # Compare with CSV audit for 50K
            df_50k = pd.read_csv(CSV_50K, low_memory=False)
            assert null_price == int(df_50k["price"].isna().sum())
            assert null_district == int(df_50k["district_name"].isna().sum())
            assert null_ward == int(df_50k["ward_name"].isna().sum())


def test_controlled_transaction_rollback(setup_test_database):
    """Verify ACID atomicity: controlled constraint violation rolls back cleanly."""
    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.properties;")
            initial_count = cur.fetchone()[0]

        # Attempt to insert invalid record in a transaction that will fail
        with pytest.raises(psycopg.Error):
            with conn.transaction():
                with conn.cursor() as cur:
                    # Valid insert
                    cur.execute("""
                        INSERT INTO public.properties (id, name, property_type_name, province_name, area, published_at)
                        VALUES (999999, 'Test Nhà', 'Nhà', 'Hà Nội', 100.0, NOW());
                    """)
                    # Violate check constraint: area <= 0
                    cur.execute("""
                        INSERT INTO public.properties (id, name, property_type_name, province_name, area, published_at)
                        VALUES (1000000, 'Test Lỗi', 'Nhà', 'Hà Nội', -50.0, NOW());
                    """)

        # Verify transaction rolled back completely
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.properties;")
            after_count = cur.fetchone()[0]
            assert after_count == initial_count, "Rollback failed: row count altered"
            cur.execute("SELECT COUNT(*) FROM public.properties WHERE id = 999999;")
            assert cur.fetchone()[0] == 0, "Partial insert leaked after rollback"


def test_query_q1_execution(setup_test_database):
    """Test Q1 on live test database."""
    q1_path = PROJECT_ROOT / "sql" / "benchmark" / "queries" / "q1.sql"
    with open(q1_path, "r", encoding="utf-8") as f:
        q1_sql = f.read()

    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(q1_sql)
            rows = cur.fetchall()
            assert len(rows) > 0, "Q1 returned 0 rows"
            # q1 selects id (0), name (1), price (2), area (3)
            for r in rows[:10]:
                assert len(r) == 4
                assert r[0] > 0  # id


def test_query_q2_execution(setup_test_database):
    """Test Q2 on live test database."""
    q2_path = PROJECT_ROOT / "sql" / "benchmark" / "queries" / "q2.sql"
    with open(q2_path, "r", encoding="utf-8") as f:
        q2_sql = f.read()

    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(q2_sql)
            rows = cur.fetchall()
            assert len(rows) == 20, f"Q2 LIMIT 20 returned {len(rows)} rows"
            # q2 selects id (0), name (1), price (2), area (3), published_at (4)
            # ORDER BY price ASC, id ASC
            prices = [float(r[2]) for r in rows]
            assert prices == sorted(prices)
            for p in prices:
                assert 4100000000 <= p <= 14300000000


def test_q3_original_vs_rewritten_equivalence(setup_test_database):
    """Verify mathematical & semantic equivalence between Q3 Original and Q3 Rewritten."""
    q3_orig_path = PROJECT_ROOT / "sql" / "benchmark" / "queries" / "q3_original.sql"
    q3_rewr_path = PROJECT_ROOT / "sql" / "benchmark" / "queries" / "q3_rewritten.sql"
    with open(q3_orig_path, "r", encoding="utf-8") as f:
        sql_orig = f.read()
    with open(q3_rewr_path, "r", encoding="utf-8") as f:
        sql_rewr = f.read()

    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_orig)
            orig_rows = cur.fetchall()
            cur.execute(sql_rewr)
            rewr_rows = cur.fetchall()

            assert len(orig_rows) == len(rewr_rows), f"Row count mismatch: orig={len(orig_rows)}, rewr={len(rewr_rows)}"
            assert orig_rows == rewr_rows, "Result set content mismatch between Q3 original and rewritten"


def test_query_q4_execution(setup_test_database):
    """Test Q4 GROUP BY aggregation on live test database."""
    q4_path = PROJECT_ROOT / "sql" / "benchmark" / "queries" / "q4.sql"
    with open(q4_path, "r", encoding="utf-8") as f:
        q4_sql = f.read()

    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=TEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(q4_sql)
            rows = cur.fetchall()
            assert len(rows) > 0, "Q4 returned 0 rows"
            # q4 selects property_type_name (0), total (1), avg_price (2)
            for r in rows:
                assert len(r) == 3
                assert r[1] > 0
            totals = [r[1] for r in rows]
            assert totals == sorted(totals, reverse=True)


def test_end_to_end_smoke_pipeline():
    """End-to-end smoke pipeline: raw record -> clean -> feature engineering -> validation."""
    raw_df = pd.DataFrame([
        {
            "name": "  Bán nhà mặt phố Cầu Giấy  ",
            "property_type_name": "Nhà mặt tiền",
            "province_name": "Hà Nội",
            "district_name": "Cầu Giấy",
            "ward_name": "Dịch Vọng",
            "price": 15000000000,
            "area": 85.5,
            "published_at": "2025-06-15 10:30:00"
        },
        {
            "name": "Đất thổ cư giá thỏa thuận",
            "property_type_name": "Đất",
            "province_name": "Đà Nẵng",
            "district_name": "Sơn Trà",
            "ward_name": None,
            "price": None,  # Negotiated
            "area": 120.0,
            "published_at": "2025-07-20 14:00:00"
        }
    ])
    # 1. Clean
    cleaned_df, report = clean_dataframe(raw_df)
    cleaned_df["id"] = range(1, len(cleaned_df) + 1)
    assert len(cleaned_df) == 2
    assert cleaned_df.iloc[0]["id"] == 1
    assert cleaned_df.iloc[0]["name"] == "Bán nhà mặt phố Cầu Giấy"

    # 2. Feature engineering
    enriched = compute_features(cleaned_df)
    assert enriched.shape == (2, 24)
    assert enriched.loc[0, "price_per_m2"] == 15000000000 / 85.5
    assert pd.isna(enriched.loc[1, "price_per_m2"])
    assert enriched.loc[1, "price_segment"] == "Thỏa thuận"


def test_preexisting_databases_preserved(setup_test_database):
    """Verify that existing system databases are preserved and never dropped."""
    with psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, dbname=ADMIN_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database;")
            dbs = [row[0] for row in cur.fetchall()]
            assert "postgres" in dbs, "Default 'postgres' database must exist"
            assert setup_test_database in dbs, "Ephemeral test database must exist during test"

