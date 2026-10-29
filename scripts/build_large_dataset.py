"""Build nested CSV datasets from one shuffled, bounded-memory stream."""

import argparse
from contextlib import ExitStack
from itertools import islice
import json
import math
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from time import perf_counter

import pandas as pd

if __package__:
    from .cleaning import COLUMNS, clean_dataframe
else:
    from cleaning import COLUMNS, clean_dataframe


DATASET_NAME = "Phuscca/vietnam-real-estates"
OUTPUT_COLUMNS = ["id", *COLUMNS]
DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEFAULT_TARGETS = [50_000, 200_000, 500_000]
DEFAULT_PROGRESS_INTERVAL = 10.0


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Gia tri phai la so nguyen duong")
    return number


def parse_targets(value):
    try:
        targets = [positive_int(part.strip()) for part in value.split(",")]
    except (ValueError, argparse.ArgumentTypeError) as exc:
        raise argparse.ArgumentTypeError(
            "--targets can danh sach so nguyen duong, vi du 50000,200000,500000"
        ) from exc
    return sorted(set(targets))


def positive_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("Khoang thoi gian phai la so huu han > 0")
    return seconds


def cleanup_files(paths):
    """Try every path independently, preserving the exception being handled."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            # Reporting a cleanup problem must not replace the original error,
            # even if stderr is closed or cannot encode a Vietnamese path.
            try:
                print(f"Canh bao cleanup: khong the xoa {path}: {exc}",
                      file=sys.stderr, flush=True)
            except (OSError, UnicodeError):
                pass


def iter_batches(rows, batch_size):
    """Consume an iterable once, keeping at most batch_size records per batch."""
    if batch_size <= 0:
        raise ValueError("batch_size phai > 0")
    iterator = iter(rows)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            return
        yield batch


def load_source(*, seed, shuffle_buffer, revision=None):
    print(f"Bat dau ket noi Hugging Face: {DATASET_NAME}, split=train...", flush=True)
    # Keep offline tests and --help independent of the Hugging Face import.
    from datasets import load_dataset

    options = {"split": "train", "streaming": True}
    if revision is not None:
        options["revision"] = revision
    stream = load_dataset(DATASET_NAME, **options)
    return stream.shuffle(seed=seed, buffer_size=shuffle_buffer)


def build_datasets(
    rows,
    *,
    targets,
    batch_size=2000,
    seed=42,
    shuffle_buffer=10000,
    revision=None,
    output_dir=Path("data/processed"),
    report_dir=Path("results"),
    progress_interval=DEFAULT_PROGRESS_INTERVAL,
):
    """Clean an already shuffled stream once and write each requested prefix.

    Counters describe every source record yielded in the batches we consume.
    The last batch can contain valid rows beyond max(targets); these are counted
    as valid_rows_not_exported. The Hugging Face shuffle buffer can prefetch
    further upstream records, which are not included in source_rows_read.

    Existing results are refused. CSVs are staged beside their final paths,
    closed, then renamed only after all targets are complete. The report is
    published last; ordinary publication failures roll back newly named files.
    """
    targets = sorted(set(targets))
    if not targets or any(type(target) is not int or target <= 0 for target in targets):
        raise ValueError("targets phai chua cac so nguyen duong")
    if batch_size <= 0 or shuffle_buffer <= 0:
        raise ValueError("batch_size va shuffle_buffer phai > 0")
    if not math.isfinite(progress_interval) or progress_interval <= 0:
        raise ValueError("progress_interval phai la so huu han > 0")

    started = perf_counter()
    output_dir, report_dir = Path(output_dir), Path(report_dir)
    max_target = targets[-1]
    output_paths = {
        target: output_dir / f"properties_{target}.csv" for target in targets
    }
    report_path = report_dir / f"build_report_{max_target}.json"
    final_paths = [*output_paths.values(), report_path]
    for path in final_paths:
        if path.exists():
            raise FileExistsError(f"Ket qua da ton tai, khong ghi de: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    counts = {target: 0 for target in targets}
    null_counts = {
        target: dict.fromkeys(OUTPUT_COLUMNS, 0) for target in targets
    }
    source_rows_read = invalid_rows = valid_rows_seen = exported_rows = 0
    invalid_by_reason = dict.fromkeys(
        ["invalid_required", "invalid_area", "invalid_date"], 0
    )
    invalid_price_values = 0
    temporary_paths = []
    published_paths = []
    completed = False
    last_progress = started

    def show_progress(*, force=False):
        nonlocal last_progress
        now = perf_counter()
        if force or now - last_progress >= progress_interval:
            print(
                f"Tien do: da doc={source_rows_read}; hop le={valid_rows_seen}; "
                f"bi loai={invalid_rows}; da xuat={exported_rows}/{max_target}; "
                f"thoi gian={now - started:.1f}s",
                flush=True,
            )
            last_progress = now

    try:
        with ExitStack() as stack:
            handles = {}
            staged_csvs = {}
            for target, path in output_paths.items():
                handle = stack.enter_context(NamedTemporaryFile(
                    mode="w", encoding="utf-8-sig", newline="",
                    dir=path.parent, prefix=f".{path.stem}.",
                    suffix=".csv.part", delete=False,
                ))
                staged_csvs[target] = Path(handle.name)
                temporary_paths.append(Path(handle.name))
                handles[target] = handle

            print(
                f"Bat dau doc stream Hugging Face, batch_size={batch_size}. "
                f"Shuffle buffer={shuffle_buffer} co the can duoc nap truoc khi "
                "batch dau tien xuat hien; dang cho du lieu...",
                flush=True,
            )
            show_progress(force=True)
            for batch in iter_batches(rows, batch_size):
                cleaned, cleaning_report = clean_dataframe(pd.DataFrame.from_records(batch))
                source_rows_read += cleaning_report["original_rows"]
                invalid_rows += cleaning_report["removed_rows"]
                valid_rows_seen += cleaning_report["cleaned_rows"]
                invalid_price_values += cleaning_report["invalid_price"]
                for reason in invalid_by_reason:
                    invalid_by_reason[reason] += cleaning_report[reason]

                cleaned = cleaned.iloc[:max_target - exported_rows].copy()
                if not cleaned.empty:
                    cleaned.insert(
                        0, "id", range(exported_rows + 1, exported_rows + len(cleaned) + 1)
                    )
                    for target in targets:
                        remaining = target - counts[target]
                        if remaining <= 0:
                            continue
                        portion = cleaned.iloc[:remaining]
                        portion.to_csv(
                            handles[target], index=False, header=counts[target] == 0,
                            na_rep="", date_format=DATE_FORMAT, lineterminator="\n",
                        )
                        counts[target] += len(portion)
                        for column, count in portion.isna().sum().items():
                            null_counts[target][column] += int(count)
                    exported_rows += len(cleaned)
                show_progress(force=exported_rows == max_target)
                if exported_rows == max_target:
                    break

            if exported_rows < max_target:
                show_progress(force=True)
                raise ValueError(
                    f"Khong du ban ghi hop le: can {max_target}, chi co {exported_rows}; "
                    f"da doc {source_rows_read}, loai {invalid_rows}. "
                    "Khong xuat ket qua chua hoan thanh."
                )

        report = {
            "status": "completed",
            "source": DATASET_NAME,
            "split": "train",
            "streaming": True,
            "revision": revision,
            "seed": seed,
            "targets": targets,
            "batch_size": batch_size,
            "shuffle_buffer": shuffle_buffer,
            "columns": OUTPUT_COLUMNS,
            "source_rows_read": source_rows_read,
            "invalid_rows": invalid_rows,
            "invalid_by_reason": invalid_by_reason,
            "invalid_price_values": invalid_price_values,
            "valid_rows_seen": valid_rows_seen,
            "valid_rows_not_exported": valid_rows_seen - exported_rows,
            "exported_rows": exported_rows,
            "total_csv_rows_written": sum(counts.values()),
            "null_counts": null_counts[max_target],
            "outputs": {
                str(target): {
                    "path": str(output_paths[target]),
                    "rows": counts[target],
                    "null_counts": null_counts[target],
                }
                for target in targets
            },
            "elapsed_seconds": perf_counter() - started,
        }
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=report_dir,
            prefix=f".{report_path.stem}.", suffix=".json.part", delete=False,
        ) as handle:
            staged_report = Path(handle.name)
            temporary_paths.append(staged_report)
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")

        # Recheck after the potentially long stream run, before publishing.
        for path in final_paths:
            if path.exists():
                raise FileExistsError(f"Ket qua da ton tai, khong ghi de: {path}")
        for target, path in output_paths.items():
            staged_csvs[target].replace(path)
            published_paths.append(path)
        staged_report.replace(report_path)
        published_paths.append(report_path)
        completed = True
        return report
    finally:
        cleanup_paths = [] if completed else list(reversed(published_paths))
        cleanup_files([*cleanup_paths, *temporary_paths])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=parse_targets, default=DEFAULT_TARGETS,
                        help="Comma-separated sizes (default: 50000,200000,500000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=positive_int, default=2000)
    parser.add_argument("--shuffle-buffer", type=positive_int, default=10000)
    parser.add_argument("--revision", help="Optional Hugging Face commit, tag or branch")
    parser.add_argument("--progress-interval", type=positive_seconds,
                        default=DEFAULT_PROGRESS_INTERVAL,
                        help="Seconds between batch progress updates (default: 10)")
    args = parser.parse_args(argv)
    if args.seed < 0:
        parser.error("--seed phai >= 0")

    try:
        rows = load_source(
            seed=args.seed, shuffle_buffer=args.shuffle_buffer, revision=args.revision
        )
        report = build_datasets(
            rows, targets=args.targets, batch_size=args.batch_size,
            seed=args.seed, shuffle_buffer=args.shuffle_buffer, revision=args.revision,
            progress_interval=args.progress_interval,
        )
    except KeyboardInterrupt:
        parser.exit(130, "Da dung. Da thu don file tam; xem canh bao cleanup neu co.\n")
    except Exception as exc:
        parser.exit(1, f"Loi xay dung dataset: {exc}\n")

    print(f"Da doc {report['source_rows_read']} dong; loai {report['invalid_rows']}; "
          f"xuat {report['exported_rows']} dong hop le.", flush=True)
    for output in report["outputs"].values():
        print(f"{output['path']}: {output['rows']} dong", flush=True)
    print(f"Report: results/build_report_{max(args.targets)}.json", flush=True)


if __name__ == "__main__":
    sys.exit(main())
