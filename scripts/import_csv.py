"""Import a prepared CSV into public.properties using transactional COPY."""

import argparse
import csv
from io import TextIOWrapper
import os
from pathlib import Path
import sys
from time import perf_counter

from dotenv import dotenv_values
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COLUMNS = [
    "id", "name", "property_type_name", "province_name", "district_name",
    "ward_name", "price", "area", "published_at",
]
NULL_COLUMNS = ["price", "district_name", "ward_name"]
PG_SETTINGS = {
    "PGHOST": "host",
    "PGPORT": "port",
    "PGDATABASE": "dbname",
    "PGUSER": "user",
    "PGPASSWORD": "password",
}
COPY_SQL = """
    COPY public.properties (
        id, name, property_type_name, province_name, district_name,
        ward_name, price, area, published_at
    ) FROM STDIN WITH (
        FORMAT CSV, HEADER TRUE, ENCODING 'UTF8', NULL '',
        FORCE_NULL (price, district_name, ward_name)
    )
"""
SCHEMA_SQL = """
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'properties'
    ORDER BY ordinal_position
"""
STATS_SQL = """
    SELECT COUNT(*), COUNT(DISTINCT id), MIN(id), MAX(id),
           COUNT(*) FILTER (WHERE price IS NULL),
           COUNT(*) FILTER (WHERE district_name IS NULL),
           COUNT(*) FILTER (WHERE ward_name IS NULL)
    FROM public.properties
"""


class ImportValidationError(ValueError):
    """A safe, user-facing validation message without connection secrets."""


def load_connection_settings(env_path=None):
    """Load only the five PG settings; process environment takes precedence."""
    path = PROJECT_ROOT / ".env" if env_path is None else Path(env_path)
    values = dotenv_values(path, interpolate=False)
    settings = {}
    missing = []
    for variable, parameter in PG_SETTINGS.items():
        value = os.environ.get(variable, values.get(variable))
        if value is None or (variable != "PGPASSWORD" and not value.strip()):
            missing.append(variable)
        else:
            settings[parameter] = value
    if missing:
        raise ImportValidationError("Thieu cau hinh .env: " + ", ".join(missing))
    try:
        port = int(settings["port"])
    except ValueError:
        raise ImportValidationError("PGPORT phai la so nguyen tu 1 den 65535") from None
    if not 1 <= port <= 65535:
        raise ImportValidationError("PGPORT phai la so nguyen tu 1 den 65535")
    settings["port"] = port
    return settings


def inspect_csv(stream):
    """Scan a binary file without retaining rows or altering the source.

    Empty fields in the three nullable columns, including quoted empties, are
    treated as NULL. COPY FORCE_NULL uses the same convention. Literal strings
    such as 'NULL' are not rewritten. PostgreSQL validates field types and table
    constraints during COPY.
    """
    text = TextIOWrapper(stream, encoding="utf-8-sig", newline="")
    rows = 0
    null_counts = dict.fromkeys(NULL_COLUMNS, 0)
    try:
        reader = csv.reader(text, strict=True)
        if next(reader, None) != COLUMNS:
            raise ImportValidationError(
                "Header CSV phai dung 9 cot, dung thu tu: " + ",".join(COLUMNS)
            )
        indices = {column: COLUMNS.index(column) for column in NULL_COLUMNS}
        for row in reader:
            rows += 1
            if len(row) != len(COLUMNS):
                raise ImportValidationError(f"Ban ghi CSV thu {rows} khong co dung 9 cot")
            for column, index in indices.items():
                null_counts[column] += int(row[index] == "")
        if rows == 0:
            raise ImportValidationError("CSV khong co ban ghi du lieu; tu choi import")
    except (UnicodeError, csv.Error) as exc:
        raise ImportValidationError("CSV sai cu phap hoac khong phai UTF-8") from exc
    finally:
        # Keep the same file descriptor open for the subsequent COPY pass.
        text.detach()
    return {"rows": rows, "null_counts": null_counts}


def file_version(stream):
    info = os.fstat(stream.fileno())
    return info.st_size, info.st_mtime_ns


def validate_database_stats(database_stats, expected):
    count, distinct_ids, minimum_id, maximum_id, *nulls = database_stats
    if count != expected["rows"]:
        raise ImportValidationError(
            f"So dong khong khop: CSV={expected['rows']}, database={count}"
        )
    if distinct_ids != count or minimum_id != 1 or maximum_id != count:
        raise ImportValidationError("ID trong database phai du tu 1 den N, khong trung")
    actual_nulls = dict(zip(NULL_COLUMNS, nulls))
    if actual_nulls != expected["null_counts"]:
        raise ImportValidationError(
            f"So luong NULL khong khop: CSV={expected['null_counts']}, database={actual_nulls}"
        )
    return {"rows": count, "min_id": minimum_id, "max_id": maximum_id,
            "null_counts": actual_nulls}


def import_csv(
    file_path, *, replace=False, settings=None, connect=None,
    chunk_size=1024 * 1024, progress_interval=5.0,
):
    """Inspect CSV, COPY bounded byte blocks, validate, then commit once.

    The connection uses autocommit only to avoid an implicit outer transaction.
    Every database operation is inside an explicit connection.transaction().
    Unit tests inject a fake connection factory and never contact PostgreSQL.
    """
    if chunk_size <= 0 or progress_interval <= 0:
        raise ValueError("chunk_size va progress_interval phai > 0")
    path = Path(file_path)
    if not path.is_file():
        raise ImportValidationError("Khong tim thay file CSV: " + str(path))
    started = perf_counter()
    print(f"Kiem tra CSV: {path}", flush=True)
    with path.open("rb") as source:
        version = file_version(source)
        expected = inspect_csv(source)
        if file_version(source) != version:
            raise ImportValidationError("CSV da thay doi trong khi kiem tra")
        print(f"CSV hop le: {expected['rows']} ban ghi; NULL={expected['null_counts']}",
              flush=True)
        if settings is None:
            settings = load_connection_settings()
        if connect is None:
            connect = psycopg.connect
        print("Bat dau ket noi PostgreSQL...", flush=True)
        with connect(**settings, autocommit=True, client_encoding="UTF8", connect_timeout=10) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    # Serialize importers and prevent concurrent writers from
                    # invalidating the empty-table check and final statistics.
                    cursor.execute("LOCK TABLE public.properties IN SHARE ROW EXCLUSIVE MODE")
                    cursor.execute(SCHEMA_SQL)
                    if [row[0] for row in cursor.fetchall()] != COLUMNS:
                        raise ImportValidationError("Schema public.properties khong dung 9 cot da thong nhat")
                    cursor.execute("SELECT EXISTS (SELECT 1 FROM public.properties)")
                    populated = cursor.fetchone()[0]
                    if populated and not replace:
                        raise ImportValidationError(
                            "Bang public.properties da co du lieu. Chi dung --replace khi muon thay the toan bo."
                        )
                    if replace:
                        print("TRUNCATE public.properties trong transaction...", flush=True)
                        cursor.execute("TRUNCATE TABLE public.properties")

                    source.seek(0)
                    if source.read(3) != b"\xef\xbb\xbf":
                        source.seek(0)
                    total_bytes = version[0] - source.tell()
                    sent = 0
                    last_progress = perf_counter()
                    print(f"Bat dau COPY: {expected['rows']} ban ghi, {total_bytes} bytes...", flush=True)
                    with cursor.copy(COPY_SQL) as copy:
                        while block := source.read(chunk_size):
                            copy.write(block)
                            sent += len(block)
                            now = perf_counter()
                            if now - last_progress >= progress_interval or sent == total_bytes:
                                print(
                                    f"COPY da gui={sent}/{total_bytes} bytes; "
                                    f"thoi gian={now - started:.1f}s; chua COMMIT",
                                    flush=True,
                                )
                                last_progress = now

                    if file_version(source) != version or sent != total_bytes:
                        raise ImportValidationError("CSV da thay doi trong khi COPY")
                    cursor.execute(STATS_SQL)
                    result = validate_database_stats(cursor.fetchone(), expected)
                    print(
                        f"Kiem tra truoc COMMIT: rows={result['rows']}; "
                        f"ID={result['min_id']}..{result['max_id']}, khong thieu/trung; "
                        f"NULL={result['null_counts']}; thoi gian={perf_counter() - started:.1f}s",
                        flush=True,
                    )
            # The explicit transaction has committed successfully here.
    result["elapsed_seconds"] = perf_counter() - started
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="Prepared CSV to import")
    parser.add_argument("--replace", action="store_true", help="Replace all public.properties rows transactionally")
    args = parser.parse_args(argv)
    try:
        result = import_csv(args.file, replace=args.replace)
    except ImportValidationError as exc:
        parser.exit(1, f"Loi kiem tra: {exc}. Khong commit; transaction dang mo duoc rollback.\n")
    except KeyboardInterrupt:
        parser.exit(130, "Da dung import; transaction dang mo duoc rollback.\n")
    except Exception as exc:
        # Do not print raw driver errors, kwargs, DSNs or tracebacks: they may
        # contain connection secrets or values from the imported data.
        parser.exit(
            1, f"Loi import ({type(exc).__name__}). Transaction chua commit se duoc rollback. "
            "Kiem tra ket noi, quyen truy cap, schema va du lieu CSV.\n",
        )
    print(
        f"COMMIT thanh cong: {result['rows']} ban ghi; NULL={result['null_counts']}; "
        f"tong thoi gian={result['elapsed_seconds']:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
