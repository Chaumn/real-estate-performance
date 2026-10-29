import csv
from io import StringIO
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from scripts import build_large_dataset as builder


@pytest.fixture
def records():
    row = {
        "name": '  Bán nhà, "đẹp"\nHà Nội  ',
        "property_type_name": " Nhà riêng ",
        "province_name": " Hà Nội ",
        "district_name": " Ba Đình ",
        "ward_name": " Điện Biên ",
        "price": 2_000_000_000,
        "area": 50,
        "published_at": "2026-01-02T03:04:05",
        "unused": "Do not export",
    }
    return [
        {**row, "price": None, "district_name": None,
         "published_at": "2026-01-02T03:04:05.123456"},
        {**row, "name": " "},
        {**row, "price": 0, "ward_name": None},
        {**row, "area": float("inf")},
        dict(row),
        {**row, "price": -1, "district_name": None},
        {**row, "published_at": "bad"},
        {**row, "name": None, "area": 0, "published_at": "bad"},
        {**row, "price": "1e30", "area": "1e20"},
        dict(row), dict(row), dict(row),
    ]


@pytest.fixture
def paths(tmp_path):
    return {"output_dir": tmp_path / "processed", "report_dir": tmp_path / "results"}


def csv_rows(path):
    return list(csv.reader(StringIO(path.read_text(encoding="utf-8-sig"))))


@pytest.mark.parametrize(
    "length,batch_size,expected",
    [(0, 2, []), (1, 2, [[0]]), (5, 2, [[0, 1], [2, 3], [4]]),
     (4, 2, [[0, 1], [2, 3]]), (3, 1, [[0], [1], [2]])],
)
def test_iter_batches(length, batch_size, expected):
    assert list(builder.iter_batches(iter(range(length)), batch_size)) == expected


def test_batch_iterator_is_lazy_and_rejects_zero_size():
    consumed = []

    def source():
        for number in range(10):
            consumed.append(number)
            yield number

    batches = builder.iter_batches(source(), 3)
    assert consumed == []
    assert next(batches) == [0, 1, 2]
    assert consumed == [0, 1, 2]
    with pytest.raises(ValueError, match="batch_size"):
        next(builder.iter_batches([], 0))


def test_nested_outputs_single_pass_shared_cleaner_and_report(records, paths, monkeypatch):
    consumed = []
    batch_lengths = []
    real_cleaner = builder.clean_dataframe

    class SinglePass:
        def __init__(self):
            self.iterations = 0

        def __iter__(self):
            self.iterations += 1
            assert self.iterations == 1
            for record in records:
                consumed.append(record)
                yield record
            pytest.fail("Builder read beyond the final necessary batch")

    def tracked_cleaner(df):
        batch_lengths.append(len(df))
        return real_cleaner(df)

    monkeypatch.setattr(builder, "clean_dataframe", tracked_cleaner)
    report = builder.build_datasets(
        SinglePass(), targets=[7, 2, 5, 2], batch_size=3,
        seed=123, shuffle_buffer=100, revision="test-commit", **paths,
    )

    assert len(consumed) == 12
    assert batch_lengths == [3, 3, 3, 3]
    outputs = {}
    for target in [2, 5, 7]:
        path = paths["output_dir"] / f"properties_{target}.csv"
        outputs[target] = csv_rows(path)
        assert outputs[target][0] == [
            "id", "name", "property_type_name", "province_name", "district_name",
            "ward_name", "price", "area", "published_at",
        ]
        assert len(outputs[target]) == target + 1
        assert [int(row[0]) for row in outputs[target][1:]] == list(range(1, target + 1))
        assert report["outputs"][str(target)]["rows"] == target
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        assert path.read_bytes().count(b"\xef\xbb\xbf") == 1
    assert outputs[2] == outputs[7][:3]
    assert outputs[5] == outputs[7][:6]
    assert (paths["output_dir"] / "properties_7.csv").read_bytes().startswith(
        (paths["output_dir"] / "properties_5.csv").read_bytes()
    )
    assert outputs[7][1][1] == 'Bán nhà, "đẹp"\nHà Nội'
    assert outputs[7][1][4] == ""  # Missing district.
    assert outputs[7][1][6] == ""  # Missing price.
    assert outputs[7][2][5] == ""  # Missing ward.
    assert outputs[7][2][6] == ""  # Zero price stays as a NULL row.
    assert outputs[7][1][-1] == "2026-01-02 03:04:05.123456"
    assert outputs[7][2][-1] == "2026-01-02 03:04:05.000000"
    assert report["status"] == "completed"
    assert report["source"] == builder.DATASET_NAME
    assert report["split"] == "train"
    assert report["streaming"] is True
    assert report["revision"] == "test-commit"
    assert report["seed"] == 123
    assert report["batch_size"] == 3
    assert report["shuffle_buffer"] == 100
    assert report["targets"] == [2, 5, 7]
    assert report["source_rows_read"] == 12
    assert report["invalid_rows"] == 4
    assert report["invalid_by_reason"] == {
        "invalid_required": 2, "invalid_area": 2, "invalid_date": 2,
    }
    assert report["invalid_price_values"] == 2
    assert report["valid_rows_seen"] == 8
    assert report["valid_rows_not_exported"] == 1
    assert report["exported_rows"] == 7
    assert report["total_csv_rows_written"] == 14
    expected_nulls = dict.fromkeys(builder.OUTPUT_COLUMNS, 0)
    expected_nulls.update(price=3, district_name=2, ward_name=1)
    assert report["null_counts"] == expected_nulls
    assert report["outputs"]["2"]["null_counts"]["price"] == 2
    assert report["elapsed_seconds"] >= 0
    saved_report = json.loads((paths["report_dir"] / "build_report_7.json").read_text())
    assert saved_report == report
    assert not list(paths["output_dir"].glob("*.part"))
    assert not list(paths["report_dir"].glob("*.part"))


@pytest.mark.parametrize("batch_size", [1, 2, 4, 20])
def test_continuous_ids_and_prefixes_across_batch_boundaries(records, paths, batch_size):
    report = builder.build_datasets(
        iter(records), targets=[2, 5, 7], batch_size=batch_size, **paths,
    )

    large = pd.read_csv(paths["output_dir"] / "properties_7.csv")
    assert large["id"].tolist() == list(range(1, 8))
    for target in [2, 5]:
        small = pd.read_csv(paths["output_dir"] / f"properties_{target}.csv")
        pd.testing.assert_frame_equal(small, large.iloc[:target], check_dtype=False)
    assert report["source_rows_read"] == report["invalid_rows"] + report["valid_rows_seen"]


def test_empty_cleaned_batch_and_short_final_batch(records, paths):
    rows = [records[1], records[3], records[0], records[2], records[4]]

    report = builder.build_datasets(iter(rows), targets=[3], batch_size=2, **paths)

    assert report["source_rows_read"] == 5
    assert report["invalid_rows"] == 2
    output = pd.read_csv(paths["output_dir"] / "properties_3.csv")
    assert output["id"].tolist() == [1, 2, 3]


@pytest.mark.parametrize("source_kind", ["empty", "invalid", "too_short", "network_error"])
def test_failure_never_publishes_partial_results(records, paths, source_kind):
    def source():
        if source_kind == "empty":
            return
        if source_kind == "invalid":
            yield records[1]
            yield records[3]
            return
        yield records[0]
        yield records[2]  # The small target completes, but must remain temporary.
        if source_kind == "network_error":
            raise RuntimeError("connection lost")

    with pytest.raises((ValueError, RuntimeError), match="Khong du|connection lost"):
        builder.build_datasets(source(), targets=[2, 5], batch_size=2, **paths)

    assert list(paths["output_dir"].iterdir()) == []
    assert list(paths["report_dir"].iterdir()) == []


def test_csv_write_failure_cleans_up(records, paths, monkeypatch):
    original_to_csv = pd.DataFrame.to_csv
    calls = 0

    def fail_on_second_write(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk full")
        return original_to_csv(self, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail_on_second_write)
    with pytest.raises(OSError, match="disk full"):
        builder.build_datasets(iter(records), targets=[2, 5], batch_size=3, **paths)

    assert list(paths["output_dir"].iterdir()) == []
    assert list(paths["report_dir"].iterdir()) == []


def test_publication_failure_rolls_back_completed_csvs(records, paths, monkeypatch):
    original_replace = Path.replace

    def fail_report_replace(self, target):
        if Path(target).suffix == ".json":
            raise OSError("cannot publish report")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_report_replace)
    with pytest.raises(OSError, match="cannot publish report"):
        builder.build_datasets(iter(records), targets=[2, 5], batch_size=3, **paths)

    assert list(paths["output_dir"].iterdir()) == []
    assert list(paths["report_dir"].iterdir()) == []


@pytest.mark.parametrize("existing", ["csv", "report"])
def test_existing_results_are_preserved_without_consuming_stream(records, paths, existing):
    if existing == "csv":
        path = paths["output_dir"] / "properties_2.csv"
    else:
        path = paths["report_dir"] / "build_report_5.json"
    path.parent.mkdir(parents=True)
    path.write_text("previous result", encoding="utf-8")

    def source():
        pytest.fail("Existing outputs should be checked before consuming data")
        yield records[0]

    with pytest.raises(FileExistsError, match="khong ghi de"):
        builder.build_datasets(source(), targets=[2, 5], **paths)

    assert path.read_text(encoding="utf-8") == "previous result"
    assert not list(path.parent.glob("*.part"))


@pytest.mark.parametrize("revision", [None, "abc123"])
def test_source_uses_streaming_and_shuffle_without_network(monkeypatch, revision):
    calls = []
    shuffled_rows = iter([])

    def shuffle(**kwargs):
        calls.append(("shuffle", kwargs))
        return shuffled_rows

    def fake_load_dataset(name, **kwargs):
        calls.append((name, kwargs))
        return SimpleNamespace(shuffle=shuffle)

    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(load_dataset=fake_load_dataset))
    result = builder.load_source(seed=17, shuffle_buffer=23, revision=revision)

    expected_options = {"split": "train", "streaming": True}
    if revision is not None:
        expected_options["revision"] = revision
    assert calls == [
        (builder.DATASET_NAME, expected_options),
        ("shuffle", {"seed": 17, "buffer_size": 23}),
    ]
    assert result is shuffled_rows


@pytest.mark.parametrize("targets", [[], [0], [-1], [1.5]])
def test_invalid_targets_fail_before_writing(paths, targets):
    with pytest.raises(ValueError, match="targets"):
        builder.build_datasets([], targets=targets, **paths)
    assert not paths["output_dir"].exists()


@pytest.mark.parametrize("arguments", [
    ["--targets", "0,2"], ["--targets", "2,"], ["--targets", "abc"],
    ["--batch-size", "0"], ["--shuffle-buffer", "-1"], ["--seed", "-1"],
    ["--progress-interval", "0"], ["--progress-interval", "-1"],
    ["--progress-interval", "nan"], ["--progress-interval", "inf"],
])
def test_cli_rejects_invalid_options(arguments):
    with pytest.raises(SystemExit) as error:
        builder.main(arguments)
    assert error.value.code == 2


def test_cli_forwards_all_options_and_uses_one_source(records, paths, monkeypatch, capsys):
    source_calls = []
    real_build = builder.build_datasets

    def fake_source(**kwargs):
        source_calls.append(kwargs)
        return iter(records)

    def local_build(rows, **kwargs):
        return real_build(rows, **kwargs, **paths)

    monkeypatch.setattr(builder, "load_source", fake_source)
    monkeypatch.setattr(builder, "build_datasets", local_build)
    builder.main([
        "--targets", "5,2", "--seed", "17", "--batch-size", "3",
        "--shuffle-buffer", "23", "--revision", "abc123", "--progress-interval", "2.5",
    ])

    assert source_calls == [{"seed": 17, "shuffle_buffer": 23, "revision": "abc123"}]
    report = json.loads((paths["report_dir"] / "build_report_5.json").read_text())
    assert report["targets"] == [2, 5]
    assert report["batch_size"] == 3
    assert "5 dong hop le" in capsys.readouterr().out


def test_cli_reports_source_errors(monkeypatch, capsys):
    def fail_load(**kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(builder, "load_source", fail_load)
    with pytest.raises(SystemExit) as error:
        builder.main(["--targets", "2"])
    assert error.value.code == 1
    assert "Loi xay dung dataset: offline" in capsys.readouterr().err


def test_cli_defaults_without_network(monkeypatch):
    calls = {}
    rows = iter([])

    def fake_source(**kwargs):
        calls["source"] = kwargs
        return rows

    def fake_build(source, **kwargs):
        assert source is rows
        calls["build"] = kwargs
        return {
            "source_rows_read": 500000, "invalid_rows": 0,
            "exported_rows": 500000, "outputs": {},
        }

    monkeypatch.setattr(builder, "load_source", fake_source)
    monkeypatch.setattr(builder, "build_datasets", fake_build)
    builder.main([])

    assert calls["source"] == {"seed": 42, "shuffle_buffer": 10000, "revision": None}
    assert calls["build"] == {
        "targets": [50000, 200000, 500000], "batch_size": 2000,
        "seed": 42, "shuffle_buffer": 10000, "revision": None,
        "progress_interval": 10.0,
    }


def test_ctrl_c_cleans_staged_csvs_and_exits_clearly(records, paths, monkeypatch, capsys):
    real_build = builder.build_datasets

    def source():
        yield records[0]
        yield records[2]
        raise KeyboardInterrupt

    def local_build(rows, **kwargs):
        return real_build(rows, **kwargs, **paths)

    monkeypatch.setattr(builder, "load_source", lambda **kwargs: source())
    monkeypatch.setattr(builder, "build_datasets", local_build)
    with pytest.raises(SystemExit) as error:
        builder.main(["--targets", "2,5", "--batch-size", "2"])

    assert error.value.code == 130
    assert "Da dung" in capsys.readouterr().err
    assert list(paths["output_dir"].iterdir()) == []
    assert list(paths["report_dir"].iterdir()) == []


def test_connection_message_precedes_hugging_face_initialization(monkeypatch, capsys):
    def fake_load_dataset(*args, **kwargs):
        message = capsys.readouterr().out
        assert "Bat dau ket noi Hugging Face" in message
        assert builder.DATASET_NAME in message
        return SimpleNamespace(shuffle=lambda **kwargs: iter([]))

    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(load_dataset=fake_load_dataset))
    builder.load_source(seed=42, shuffle_buffer=10000)


def test_progress_is_flushed_throttled_and_includes_invalid_batches(
    records, paths, monkeypatch, capsys
):
    clock = [0.0]
    print_options = []
    real_print = print

    def tracked_print(*args, **kwargs):
        print_options.append(kwargs)
        real_print(*args, **kwargs)

    def source():
        initial = capsys.readouterr().out
        assert "Bat dau doc stream Hugging Face" in initial
        assert "Shuffle buffer=10000" in initial
        assert "truoc khi batch dau tien" in initial
        assert "da doc=0; hop le=0; bi loai=0; da xuat=0/3" in initial
        # Only complete batches trigger updates. The last update is forced.
        for elapsed, record in [
            (6, records[1]), (7, records[0]), (8, records[3]),
            (12, records[2]), (13, records[4]),
        ]:
            clock[0] = elapsed
            yield record

    monkeypatch.setattr(builder, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(builder, "print", tracked_print, raising=False)
    builder.build_datasets(source(), targets=[3], batch_size=1, progress_interval=5, **paths)

    progress = [line for line in capsys.readouterr().out.splitlines() if line.startswith("Tien do:")]
    assert progress == [
        "Tien do: da doc=1; hop le=0; bi loai=1; da xuat=0/3; thoi gian=6.0s",
        "Tien do: da doc=4; hop le=2; bi loai=2; da xuat=2/3; thoi gian=12.0s",
        "Tien do: da doc=5; hop le=3; bi loai=2; da xuat=3/3; thoi gian=13.0s",
    ]
    assert all(options.get("flush") is True for options in print_options)


def test_progress_interval_does_not_change_csv_data(records, paths, tmp_path):
    builder.build_datasets(iter(records), targets=[2, 5, 7], batch_size=3, **paths)
    other_dir = tmp_path / "other_processed"
    builder.build_datasets(
        iter(records), targets=[2, 5, 7], batch_size=3, progress_interval=0.001,
        output_dir=other_dir, report_dir=tmp_path / "other_results",
    )

    for target in [2, 5, 7]:
        filename = f"properties_{target}.csv"
        assert (paths["output_dir"] / filename).read_bytes() == (other_dir / filename).read_bytes()


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt])
def test_stream_error_survives_permission_error_and_other_parts_are_cleaned(
    records, paths, monkeypatch, capsys, exception_type
):
    original_error = exception_type("original stream failure")
    original_unlink = Path.unlink
    attempts = []
    blocked_paths = []

    def source():
        yield records[0]
        yield records[2]
        raise original_error

    def deny_first_part(self, *args, **kwargs):
        if self.suffix == ".part":
            attempts.append(self)
            if not blocked_paths:
                blocked_paths.append(self)
                error = PermissionError(13, "Access is denied", str(self))
                error.winerror = 5
                raise error
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", deny_first_part)
    with pytest.raises(exception_type) as error:
        builder.build_datasets(source(), targets=[1, 2, 4], batch_size=1, **paths)

    assert error.value is original_error
    assert len(attempts) == 3
    assert len(set(attempts)) == 3
    assert list(paths["output_dir"].iterdir()) == blocked_paths
    assert list(paths["report_dir"].iterdir()) == []
    warning = capsys.readouterr().err
    assert "Canh bao cleanup" in warning
    assert str(blocked_paths[0]) in warning
    assert "Access is denied" in warning
    # Release the simulated lock so pytest can remove its own temporary tree.
    original_unlink(blocked_paths[0])


def test_cli_reports_stream_error_separately_from_cleanup_warning(
    records, paths, monkeypatch, capsys
):
    real_build = builder.build_datasets
    original_unlink = Path.unlink
    blocked_paths = []

    def source():
        yield records[0]
        raise RuntimeError("connection lost during stream")

    def deny_first_part(self, *args, **kwargs):
        if self.suffix == ".part" and not blocked_paths:
            blocked_paths.append(self)
            raise PermissionError(13, "Access is denied", str(self))
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(builder, "load_source", lambda **kwargs: source())
    monkeypatch.setattr(builder, "build_datasets", lambda rows, **kwargs: real_build(rows, **kwargs, **paths))
    monkeypatch.setattr(Path, "unlink", deny_first_part)
    with pytest.raises(SystemExit) as error:
        builder.main(["--targets", "1,3", "--batch-size", "1"])

    assert error.value.code == 1
    stderr = capsys.readouterr().err
    assert "Loi xay dung dataset: connection lost during stream" in stderr
    assert "Canh bao cleanup" in stderr
    assert str(blocked_paths[0]) in stderr
    assert list(paths["output_dir"].glob("*.csv")) == []
    assert list(paths["report_dir"].iterdir()) == []
    original_unlink(blocked_paths[0])


def test_rollback_cleanup_failure_does_not_stop_other_cleanup(
    records, paths, monkeypatch, capsys
):
    original_replace = Path.replace
    original_unlink = Path.unlink
    blocked_path = paths["output_dir"] / "properties_2.csv"
    deleted_paths = []
    original_error = OSError("cannot publish report")

    def fail_report_replace(self, target):
        if Path(target).suffix == ".json":
            raise original_error
        return original_replace(self, target)

    def deny_rollback_delete(self, *args, **kwargs):
        if self == blocked_path:
            raise PermissionError(13, "Access is denied", str(self))
        deleted_paths.append(self)
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "replace", fail_report_replace)
    monkeypatch.setattr(Path, "unlink", deny_rollback_delete)
    with pytest.raises(OSError) as error:
        builder.build_datasets(iter(records), targets=[1, 2], batch_size=3, **paths)

    assert error.value is original_error
    assert paths["output_dir"] / "properties_1.csv" in deleted_paths
    assert list(paths["output_dir"].iterdir()) == [blocked_path]
    assert list(paths["report_dir"].iterdir()) == []
    assert str(blocked_path) in capsys.readouterr().err
    original_unlink(blocked_path)
