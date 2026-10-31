"""Offline tests: all connections are fakes, including transaction boundaries."""

from contextlib import contextmanager
import csv
from io import StringIO

import pytest

from scripts import import_csv as importer


SETTINGS = {
    "host": "unit-host", "port": 5432, "dbname": "unit-db",
    "user": "unit-user", "password": "unit-secret",
}


@pytest.fixture(autouse=True)
def isolate_database_and_environment(monkeypatch):
    def forbidden_connection(*args, **kwargs):
        pytest.fail("Unit tests must never connect to a real PostgreSQL database")

    monkeypatch.setattr(importer.psycopg, "connect", forbidden_connection)
    for variable in importer.PG_SETTINGS:
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture
def rows():
    return [
        [1, 'Bán nhà, "đẹp"\nHà Nội', "Nhà", "Hà Nội", None, "Điện Biên",
         None, 50, "2025-07-06 11:36:56.502000"],
        [2, "Đất Đà Nẵng", "Đất", "Đà Nẵng", "NULL", None,
         1234567890, 63.5, "2025-07-07 12:00:00.000000"],
    ]


def write_csv(tmp_path, rows, *, header=None, bom=True):
    path = tmp_path / "properties.csv"
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(importer.COLUMNS if header is None else header)
        writer.writerows(rows)
    return path


class FakeDatabase:
    def __init__(self, previous=None):
        self.rows = list(previous or [])
        self.events = []
        self.blocks = []
        self.options = None
        self.schema = list(importer.COLUMNS)
        self.stats_override = None
        self.fail_copy = None
        self.on_commit = None
        self.copy_sql = None

    def connect(self, **kwargs):
        self.options = kwargs
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    @contextmanager
    def transaction(self):
        database = self.database
        previous = list(database.rows)
        database.events.append("BEGIN")
        try:
            yield
            if database.on_commit:
                database.on_commit()
        except BaseException:
            database.rows = previous
            database.events.append("ROLLBACK")
            raise
        else:
            database.events.append("COMMIT")

    def cursor(self):
        return FakeCursor(self.database)


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, statement):
        database = self.database
        normalized = " ".join(statement.split())
        if normalized.startswith("LOCK TABLE"):
            database.events.append("LOCK")
        elif "information_schema.columns" in normalized:
            self.result = [(column,) for column in database.schema]
        elif normalized.startswith("SELECT EXISTS"):
            self.result = (bool(database.rows),)
        elif normalized.startswith("TRUNCATE"):
            database.events.append("TRUNCATE")
            database.rows = []
        elif normalized.startswith("SELECT COUNT(*)"):
            database.events.append("VALIDATE")
            ids = [row["id"] for row in database.rows]
            self.result = database.stats_override or (
                len(ids), len(set(ids)), min(ids, default=None), max(ids, default=None),
                *[sum(row[column] is None for row in database.rows) for column in importer.NULL_COLUMNS],
            )
        else:
            pytest.fail("Unexpected SQL in unit test")

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result

    def copy(self, statement):
        self.database.copy_sql = statement
        return FakeCopy(self.database)


class FakeCopy:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.database.events.append("COPY")
        return self

    def write(self, block):
        assert isinstance(block, bytes)
        self.database.blocks.append(block)
        if self.database.fail_copy == "write":
            raise RuntimeError("simulated COPY write failure")

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            return False
        if self.database.fail_copy == "finish":
            raise RuntimeError("simulated COPY server failure")
        text = b"".join(self.database.blocks).decode("utf-8")
        reader = csv.reader(StringIO(text))
        assert next(reader) == importer.COLUMNS
        for values in reader:
            row = dict(zip(importer.COLUMNS, values))
            row["id"] = int(row["id"])
            # Match the declared COPY FORCE_NULL convention for these columns.
            for column in importer.NULL_COLUMNS:
                if row[column] == "":
                    row[column] = None
            self.database.rows.append(row)
        return False


@pytest.mark.parametrize("bom", [True, False])
def test_copy_streams_bounded_blocks_preserves_utf8_and_nulls(tmp_path, rows, capsys, bom):
    path = write_csv(tmp_path, rows, bom=bom)
    original = path.read_bytes()
    database = FakeDatabase()

    def before_commit():
        message = capsys.readouterr().out
        assert "Kiem tra truoc COMMIT: rows=2" in message
        assert "ID=1..2" in message
        assert "unit-secret" not in message
        assert database.events[-1] == "VALIDATE"

    database.on_commit = before_commit
    result = importer.import_csv(path, settings=SETTINGS, connect=database.connect, chunk_size=7)

    assert result["rows"] == 2
    assert result["null_counts"] == {"price": 1, "district_name": 1, "ward_name": 1}
    assert result["elapsed_seconds"] >= 0
    assert database.rows[0]["name"] == rows[0][1]
    assert database.rows[1]["district_name"] == "NULL"
    assert database.rows[0]["price"] is None
    assert database.rows[1]["ward_name"] is None
    assert len(database.blocks) > 1
    assert max(map(len, database.blocks)) <= 7
    assert b"".join(database.blocks) == original.removeprefix(b"\xef\xbb\xbf")
    assert path.read_bytes() == original
    sql = " ".join(database.copy_sql.split())
    assert "FROM STDIN" in sql
    assert "FORMAT CSV, HEADER TRUE" in sql
    assert "ENCODING 'UTF8'" in sql
    assert database.options["autocommit"] is True
    assert database.options["client_encoding"] == "UTF8"
    assert database.events == ["BEGIN", "LOCK", "COPY", "VALIDATE", "COMMIT"]


def test_missing_file_is_rejected_before_connecting(tmp_path):
    with pytest.raises(importer.ImportValidationError, match="Khong tim thay"):
        importer.import_csv(tmp_path / "missing.csv")


@pytest.mark.parametrize("header", [
    importer.COLUMNS[:-1],
    [*importer.COLUMNS, "unexpected"],
    [importer.COLUMNS[1], importer.COLUMNS[0], *importer.COLUMNS[2:]],
    ["ID", *importer.COLUMNS[1:]],
    ["id"] * 9,
])
def test_wrong_schema_rejected_before_connecting(tmp_path, rows, header):
    path = write_csv(tmp_path, rows, header=header)
    with pytest.raises(importer.ImportValidationError, match="Header CSV"):
        importer.import_csv(path)


@pytest.mark.parametrize("bad_row", [[1] * 8, [1] * 10, []])
def test_wrong_record_width_rejected_before_connecting(tmp_path, bad_row):
    path = write_csv(tmp_path, [bad_row])
    with pytest.raises(importer.ImportValidationError, match="Ban ghi CSV thu 1"):
        importer.import_csv(path, replace=True)


@pytest.mark.parametrize("content", [b"", b"\xff", b'id,name\n1,"unterminated'])
def test_unreadable_or_malformed_csv_rejected(tmp_path, content):
    path = tmp_path / "invalid.csv"
    path.write_bytes(content)
    with pytest.raises(importer.ImportValidationError):
        importer.import_csv(path)


def test_header_only_csv_cannot_empty_a_table(tmp_path):
    path = write_csv(tmp_path, [])
    with pytest.raises(importer.ImportValidationError, match="khong co ban ghi"):
        importer.import_csv(path, replace=True)


def test_existing_data_is_refused_by_default(tmp_path, rows):
    path = write_csv(tmp_path, rows)
    previous = [{"id": 99, "name": "previous data"}]
    database = FakeDatabase(previous)
    with pytest.raises(importer.ImportValidationError, match="da co du lieu"):
        importer.import_csv(path, settings=SETTINGS, connect=database.connect)
    assert database.rows == previous
    assert database.events == ["BEGIN", "LOCK", "ROLLBACK"]


def test_replace_truncates_copies_and_validates_in_one_transaction(tmp_path, rows):
    path = write_csv(tmp_path, rows)
    database = FakeDatabase([{"id": 99}])
    importer.import_csv(path, replace=True, settings=SETTINGS, connect=database.connect)
    assert [row["id"] for row in database.rows] == [1, 2]
    assert database.events == ["BEGIN", "LOCK", "TRUNCATE", "COPY", "VALIDATE", "COMMIT"]


@pytest.mark.parametrize("phase", ["write", "finish"])
def test_copy_failure_rolls_back_previous_data(tmp_path, rows, phase):
    path = write_csv(tmp_path, rows)
    previous = [{"id": 99, "name": "previous data"}]
    database = FakeDatabase(previous)
    database.fail_copy = phase
    with pytest.raises(RuntimeError, match="simulated COPY"):
        importer.import_csv(path, replace=True, settings=SETTINGS, connect=database.connect)
    assert database.rows == previous
    assert database.events == ["BEGIN", "LOCK", "TRUNCATE", "COPY", "ROLLBACK"]


@pytest.mark.parametrize("stats, message", [
    ((1, 1, 1, 1, 1, 1, 1), "So dong khong khop"),
    ((2, 1, 1, 2, 1, 1, 1), "ID trong database"),
    ((2, 2, 2, 3, 1, 1, 1), "ID trong database"),
    ((2, 2, 1, 3, 1, 1, 1), "ID trong database"),
    ((2, 2, 1, 2, 0, 1, 1), "So luong NULL"),
    ((2, 2, 1, 2, 1, 0, 1), "So luong NULL"),
    ((2, 2, 1, 2, 1, 1, 0), "So luong NULL"),
])
def test_post_copy_validation_failure_rolls_back_previous_data(tmp_path, rows, stats, message):
    path = write_csv(tmp_path, rows)
    previous = [{"id": 99}]
    database = FakeDatabase(previous)
    database.stats_override = stats
    with pytest.raises(importer.ImportValidationError, match=message):
        importer.import_csv(path, replace=True, settings=SETTINGS, connect=database.connect)
    assert database.rows == previous
    assert database.events[-1] == "ROLLBACK"
    assert "COMMIT" not in database.events


def test_database_schema_mismatch_rolls_back_without_truncate(tmp_path, rows):
    path = write_csv(tmp_path, rows)
    database = FakeDatabase([{"id": 99}])
    database.schema = database.schema[:-1]
    with pytest.raises(importer.ImportValidationError, match="Schema public.properties"):
        importer.import_csv(path, replace=True, settings=SETTINGS, connect=database.connect)
    assert database.rows == [{"id": 99}]
    assert database.events == ["BEGIN", "LOCK", "ROLLBACK"]


def test_quoted_empty_nullable_fields_are_null(tmp_path, rows):
    path = write_csv(tmp_path, rows)
    # QUOTE_ALL makes missing cells explicit quoted empty CSV fields.
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
        writer.writerow(importer.COLUMNS)
        writer.writerows(rows)
    database = FakeDatabase()
    result = importer.import_csv(path, settings=SETTINGS, connect=database.connect)
    assert result["null_counts"] == {"price": 1, "district_name": 1, "ward_name": 1}
    assert database.rows[1]["district_name"] == "NULL"


def test_env_configuration_and_environment_override(tmp_path, monkeypatch, capsys):
    path = tmp_path / ".env"
    path.write_text(
        "PGHOST=local-test\nPGPORT=5432\nPGDATABASE=unit-db\n"
        "PGUSER=unit-user\nPGPASSWORD='unit-secret-${literal}'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PGPORT", "5433")
    settings = importer.load_connection_settings(path)
    assert settings == {
        "host": "local-test", "port": 5433, "dbname": "unit-db",
        "user": "unit-user", "password": "unit-secret-${literal}",
    }
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_missing_connection_configuration_lists_keys_only(tmp_path):
    with pytest.raises(importer.ImportValidationError, match="PGHOST.*PGPORT.*PGDATABASE.*PGUSER.*PGPASSWORD"):
        importer.load_connection_settings(tmp_path / ".env")


@pytest.mark.parametrize("port", ["not-a-port", "0", "65536"])
def test_invalid_port_does_not_expose_password(tmp_path, port):
    path = tmp_path / ".env"
    path.write_text(
        f"PGHOST=unit\nPGPORT={port}\nPGDATABASE=unit\nPGUSER=unit\nPGPASSWORD=unit-secret\n",
        encoding="utf-8",
    )
    with pytest.raises(importer.ImportValidationError) as error:
        importer.load_connection_settings(path)
    assert "PGPORT" in str(error.value)
    assert "unit-secret" not in str(error.value)


@pytest.mark.parametrize("replace", [False, True])
def test_cli_forwards_file_and_replace_without_database(monkeypatch, capsys, replace):
    calls = []
    def fake_import(file_path, **kwargs):
        calls.append((str(file_path), kwargs))
        return {"rows": 2, "null_counts": {}, "elapsed_seconds": 0.25}
    monkeypatch.setattr(importer, "import_csv", fake_import)
    arguments = ["--file", "properties.csv", *(["--replace"] if replace else [])]
    importer.main(arguments)
    assert calls == [("properties.csv", {"replace": replace})]
    assert "COMMIT thanh cong: 2 ban ghi" in capsys.readouterr().out


def test_cli_errors_never_print_raw_connection_secrets(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("postgresql://unit-user:unit-secret@unit-host/unit-db")
    monkeypatch.setattr(importer, "import_csv", fail)
    with pytest.raises(SystemExit) as error:
        importer.main(["--file", "properties.csv"])
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "RuntimeError" in captured.err
    assert "unit-secret" not in captured.err + captured.out
    assert "postgresql://" not in captured.err + captured.out
