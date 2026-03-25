#!/usr/bin/env python3
"""
Проставляет processed=true у пар near_duplicates, где хотя бы один файл уже удалён.

Удалённость определяется по entries в files-list-generator/result/*.files-list.json:
- если у записи есть file_id и deleted == true, считаем этот file_id удалённым.

Дальше скрипт проходит по analyze_duplicates/duplicates-list.json:
- near_duplicates[i].processed = true, если left.file_id или right.file_id входит в удалённые.

По умолчанию работает в режиме dry-run (без записи).
Для записи укажи --apply.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent

DEFAULT_DUPLICATES = SCRIPT_DIR / "duplicates-list.json"
DEFAULT_RESULT_DIR = SCRIPTS_DIR / "files-list-generator" / "result"


def normalize_file_id(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    t = v.strip().lower()
    return t or None


def load_entries_from_files_list(file_path: Path) -> list[dict[str, Any]]:
    data = json.loads(file_path.read_text("utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("files"), list):
        return [x for x in data["files"] if isinstance(x, dict)]
    return []


def collect_deleted_file_ids(result_dir: Path) -> tuple[set[str], int]:
    deleted_ids: set[str] = set()
    json_count = 0
    for fp in sorted(result_dir.rglob("*.files-list.json")):
        json_count += 1
        try:
            entries = load_entries_from_files_list(fp)
        except Exception as exc:  # noqa: BLE001 - лучше продолжить, чем падать на одном битом json
            print(f"[warn] skip invalid JSON: {fp} ({exc})", file=sys.stderr)
            continue
        for e in entries:
            if e.get("deleted") is not True:
                continue
            fid = normalize_file_id(e.get("file_id"))
            if fid:
                deleted_ids.add(fid)
    return deleted_ids, json_count


def mark_near_pairs_processed(
    doc: dict[str, Any], deleted_ids: set[str]
) -> tuple[int, int, int]:
    """
    Returns:
      matched_pairs        - near-пар, где хотя бы один side.file_id удалён
      updated_to_processed - сколько было изменено processed=false/absent -> true
      already_processed    - сколько уже было processed=true
    """
    near = doc.get("near_duplicates")
    if not isinstance(near, list):
        raise ValueError("duplicates-list.json: key 'near_duplicates' missing or not an array")

    matched_pairs = 0
    updated_to_processed = 0
    already_processed = 0

    for pair in near:
        if not isinstance(pair, dict):
            continue
        left = pair.get("left") if isinstance(pair.get("left"), dict) else {}
        right = pair.get("right") if isinstance(pair.get("right"), dict) else {}
        lf = normalize_file_id(left.get("file_id"))
        rf = normalize_file_id(right.get("file_id"))
        has_deleted = (lf in deleted_ids) if lf else False
        has_deleted = has_deleted or ((rf in deleted_ids) if rf else False)
        if not has_deleted:
            continue

        matched_pairs += 1
        if pair.get("processed") is True:
            already_processed += 1
            continue
        pair["processed"] = True
        updated_to_processed += 1

    return matched_pairs, updated_to_processed, already_processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ставит processed=true у near_duplicates, если хотя бы один файл пары "
            "уже deleted=true в result/*.files-list.json"
        )
    )
    parser.add_argument(
        "--duplicates",
        type=Path,
        default=DEFAULT_DUPLICATES,
        help=f"Путь к duplicates-list.json (по умолчанию: {DEFAULT_DUPLICATES})",
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=DEFAULT_RESULT_DIR,
        help=f"Папка с *.files-list.json (по умолчанию: {DEFAULT_RESULT_DIR})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записать изменения в duplicates-list.json (по умолчанию только dry-run)",
    )
    args = parser.parse_args()

    duplicates_path = args.duplicates.resolve()
    result_dir = args.result_dir.resolve()

    if not duplicates_path.is_file():
        print(f"duplicates-list.json not found: {duplicates_path}", file=sys.stderr)
        sys.exit(1)
    if not result_dir.is_dir():
        print(f"result dir not found: {result_dir}", file=sys.stderr)
        sys.exit(1)

    deleted_ids, scanned_json_files = collect_deleted_file_ids(result_dir)
    print(f"scanned_result_json_files: {scanned_json_files}")
    print(f"deleted_file_ids: {len(deleted_ids)}")

    doc = json.loads(duplicates_path.read_text("utf-8"))
    if not isinstance(doc, dict):
        print("duplicates-list.json must be a JSON object", file=sys.stderr)
        sys.exit(1)

    matched, updated, already = mark_near_pairs_processed(doc, deleted_ids)
    print(f"matched_near_pairs_with_deleted_side: {matched}")
    print(f"updated_processed_to_true: {updated}")
    print(f"already_processed_true: {already}")

    if not args.apply:
        print("dry-run: no file changes (use --apply to write)")
        return

    if updated == 0:
        print("no changes to write")
        return

    duplicates_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"written: {duplicates_path}")


if __name__ == "__main__":
    main()
