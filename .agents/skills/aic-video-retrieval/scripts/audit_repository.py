#!/usr/bin/env python3
"""Audit AIC query/notebook inventory and optionally validate a submission ZIP."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

QUERY_RE = re.compile(r"^query-(p\d+)-(\d+)-(kis|qa|trake)\.txt$", re.I)
CSV_RE = re.compile(r"^submission/query-(p\d+)-(\d+)-(kis|qa|trake)\.csv$", re.I)
VIDEO_RE = re.compile(r"^L\d{2}_V\d{3}$", re.I)
EVENT_RE = re.compile(r"(?im)^\s*(?:E|Cảnh\s*)(\d+)(?:\s*[:.)-]|\s+)")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def ok(self, message: str) -> None:
        print(f"[OK] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[WARN] {message}")

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[ERROR] {message}")


def inventory(root: Path, report: Reporter) -> dict[str, dict[int, dict[str, object]]]:
    rounds: dict[str, dict[int, dict[str, object]]] = defaultdict(dict)
    folders = sorted(path for path in root.glob("SOTUYEN*-bo-de-thi") if path.is_dir())
    if not folders:
        report.error("Không tìm thấy SOTUYEN*-bo-de-thi.")
        return {}
    for folder in folders:
        valid_count = 0
        for path in sorted(folder.glob("query-*.txt")):
            match = QUERY_RE.fullmatch(path.name)
            if not match:
                report.warn(f"Tên query không đúng mẫu: {path.relative_to(root)}")
                continue
            valid_count += 1
            round_id, number_text, task = match.groups()
            round_id, number, task = round_id.lower(), int(number_text), task.lower()
            try:
                text = path.read_text(encoding="utf-8-sig").strip()
            except UnicodeError as exc:
                report.error(f"Không đọc được {path.relative_to(root)}: {exc}")
                continue
            if not text:
                report.error(f"Query rỗng: {path.relative_to(root)}")
            if number in rounds[round_id]:
                report.error(f"Trùng query {round_id}-{number}: {path.relative_to(root)}")
                continue
            events = sorted({int(item) for item in EVENT_RE.findall(text)}) if task == "trake" else []
            if task == "trake" and (not events or events != list(range(1, max(events) + 1))):
                report.error(f"TRAKE event không hợp lệ {path.relative_to(root)}: {events}")
            rounds[round_id][number] = {"task": task, "events": len(events), "path": path}
        if not valid_count:
            report.warn(f"Không có query hợp lệ: {folder.relative_to(root)}")
    for round_id, items in sorted(rounds.items(), key=lambda item: int(item[0][1:])):
        ids = sorted(items)
        if ids != list(range(1, max(ids) + 1)):
            report.error(f"{round_id} có ID không liên tục: {ids}")
        counts = Counter(str(item["task"]) for item in items.values())
        report.ok(f"{round_id}: {len(items)} query (kis={counts['kis']}, qa={counts['qa']}, trake={counts['trake']})")
    return dict(rounds)


def audit_notebooks(root: Path, report: Reporter) -> None:
    notebooks = sorted(root.glob("*.ipynb"))
    if not notebooks:
        report.error("Không tìm thấy .ipynb ở root.")
    for path in notebooks:
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            cells = notebook["cells"]
            assert notebook.get("nbformat") == 4 and isinstance(cells, list)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, AssertionError) as exc:
            report.error(f"Notebook JSON không hợp lệ {path.name}: {exc}")
            continue
        code = [cell for cell in cells if cell.get("cell_type") == "code"]
        outputs = sum(bool(cell.get("outputs")) for cell in code)
        report.ok(f"{path.name}: JSON hợp lệ; {len(cells)} cell, {len(code)} code, {outputs} có output")


def audit_links(root: Path, report: Reporter) -> None:
    for name in ("rules.txt", "dataset.txt"):
        path = root / name
        if not path.is_file():
            report.error(f"Thiếu {name}")
            continue
        value = path.read_text(encoding="utf-8-sig").strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            report.error(f"{name} không phải HTTP(S) URL hợp lệ")
        else:
            report.ok(f"{name}: {parsed.netloc}")


def as_nonnegative(value: str, label: str, report: Reporter) -> int | None:
    if not re.fullmatch(r"\d+", value.strip()):
        report.error(f"{label} phải là số nguyên không âm, nhận {value!r}")
        return None
    return int(value)


def audit_submission(path: Path, rounds: dict[str, dict[int, dict[str, object]]], requested: str | None, report: Reporter) -> None:
    if not path.is_file() or not zipfile.is_zipfile(path):
        report.error(f"Submission ZIP không hợp lệ/không tồn tại: {path}")
        return
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            report.error(f"ZIP lỗi CRC: {bad_member}")
            return
        names = [name.replace("\\", "/") for name in archive.namelist() if not name.endswith("/")]
        parsed = [(name, CSV_RE.fullmatch(name)) for name in names]
        found_rounds = {match.group(1).lower() for _, match in parsed if match}
        round_id = requested.lower() if requested else (next(iter(found_rounds)) if len(found_rounds) == 1 else None)
        if not round_id or round_id not in rounds:
            report.error(f"Không suy ra được round local từ ZIP: {sorted(found_rounds)}")
            return
        if found_rounds != {round_id}:
            report.error(f"ZIP chứa round {sorted(found_rounds)}, cần chỉ {round_id}")
        expected = {f"submission/query-{round_id}-{number}-{item['task']}.csv" for number, item in rounds[round_id].items()}
        actual = set(names)
        if expected - actual:
            report.error(f"Thiếu CSV: {sorted(expected - actual)}")
        if actual - expected:
            report.error(f"Có file lạ: {sorted(actual - expected)}")
        for number, item in sorted(rounds[round_id].items()):
            name = f"submission/query-{round_id}-{number}-{item['task']}.csv"
            if name not in actual:
                continue
            try:
                rows = list(csv.reader(io.StringIO(archive.read(name).decode("utf-8-sig"))))
            except UnicodeError as exc:
                report.error(f"{name} không phải UTF-8: {exc}")
                continue
            if not 1 <= len(rows) <= 100:
                report.error(f"{name} cần 1..100 dòng, có {len(rows)}")
                continue
            task, events = str(item["task"]), int(item["events"])
            width = 2 if task == "kis" else 3 if task == "qa" else events + 1
            for index, row in enumerate(rows, 1):
                label = f"{name} dòng {index}"
                if len(row) != width:
                    report.error(f"{label} cần {width} cột, có {len(row)}")
                    continue
                if not VIDEO_RE.fullmatch(row[0].strip()):
                    report.error(f"{label} có video_id không hợp lệ {row[0]!r}")
                frame_cells = row[1:2] if task in {"kis", "qa"} else row[1:]
                frames = [as_nonnegative(value, f"{label} cột frame", report) for value in frame_cells]
                if task == "qa" and not row[2].strip():
                    report.error(f"{label} có answer rỗng")
                if task == "trake" and all(value is not None for value in frames):
                    values = [int(value) for value in frames]
                    if any(right <= left for left, right in zip(values, values[1:])):
                        report.error(f"{label} có frame TRAKE không tăng: {values}")
            if len({tuple(row) for row in rows}) != len(rows):
                report.warn(f"{name} có dòng trùng, lãng phí quota")
        if not report.errors:
            report.ok(f"{path.name}: cấu trúc, CSV và CRC hợp lệ")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--submission", type=Path)
    parser.add_argument("--round", dest="round_id")
    args = parser.parse_args()
    root = args.root.resolve()
    report = Reporter()
    print(f"AIC workspace: {root}")
    rounds = inventory(root, report)
    audit_notebooks(root, report)
    audit_links(root, report)
    if args.submission:
        audit_submission(args.submission.resolve(), rounds, args.round_id, report)
    print(f"Summary: errors={len(report.errors)}, warnings={len(report.warnings)}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
