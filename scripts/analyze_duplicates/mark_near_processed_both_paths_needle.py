#!/usr/bin/env python3
"""
near_duplicates: если у обеих сторон пары path содержит заданную подстроку
(после Unicode NFC), ставим у пары processed: true.

Файлы и *.files-list.json не меняются.

По умолчанию подстрока: INDIA2026. Dry-run без --apply.

Пример:
  cd scripts/analyze_duplicates
  python3 mark_near_processed_both_paths_needle.py
  python3 mark_near_processed_both_paths_needle.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_DUPLICATES = SCRIPT_DIR / "duplicates-list.json"
DEFAULT_NEEDLE = "INDIA2026"


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def path_has_needle(path: str | None, needle_nfc: str) -> bool:
    if not path or not isinstance(path, str):
        return False
    return needle_nfc in nfc(path)


def mark_pairs(
    near: list[Any],
    needle_nfc: str,
    *,
    include_processed: bool,
) -> tuple[int, int, int, int]:
    """
    Returns:
      skipped_processed — пары с processed=true, пропущенные (без --include-processed)
      matched_both_paths — оба path содержат подстроку (и не пропущены по processed)
      updated_to_processed — выставили processed=true
      already_matched_processed — оба path ок, но processed уже true
    """
    skipped_processed = 0
    matched = 0
    updated = 0
    already = 0

    for pair in near:
        if not isinstance(pair, dict):
            continue

        left = pair.get("left") if isinstance(pair.get("left"), dict) else {}
        right = pair.get("right") if isinstance(pair.get("right"), dict) else {}
        lp = left.get("path")
        rp = right.get("path")

        if not path_has_needle(lp if isinstance(lp, str) else None, needle_nfc):
            continue
        if not path_has_needle(rp if isinstance(rp, str) else None, needle_nfc):
            continue

        if pair.get("processed") is True and not include_processed:
            skipped_processed += 1
            continue

        matched += 1
        if pair.get("processed") is True:
            already += 1
            continue
        pair["processed"] = True
        updated += 1

    return skipped_processed, matched, updated, already


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "near_duplicates: оба path содержат подстроку → processed=true (без правок files-list)."
        ),
    )
    parser.add_argument(
        "--duplicates",
        type=Path,
        default=DEFAULT_DUPLICATES,
        help=f"Путь к duplicates-list.json (по умолчанию: {DEFAULT_DUPLICATES})",
    )
    parser.add_argument(
        "--needle",
        type=str,
        default=DEFAULT_NEEDLE,
        help=f"Подстрока в path после NFC (по умолчанию: {DEFAULT_NEEDLE})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записать duplicates-list.json (иначе dry-run)",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Не пропускать пары с processed: true (учесть и их в счётчиках; to_delete не трогаем)",
    )
    args = parser.parse_args()

    dup_path = args.duplicates.resolve()
    needle_nfc = nfc(args.needle.strip())
    if not needle_nfc:
        print("Пустая --needle", file=sys.stderr)
        sys.exit(1)

    if not dup_path.is_file():
        print(f"Нет файла: {dup_path}", file=sys.stderr)
        sys.exit(1)

    doc = json.loads(dup_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        print("duplicates-list.json: ожидается объект JSON", file=sys.stderr)
        sys.exit(1)

    near = doc.get("near_duplicates")
    if not isinstance(near, list):
        print("Нет массива near_duplicates", file=sys.stderr)
        sys.exit(1)

    skipped_proc, matched, updated, already = mark_pairs(
        near, needle_nfc, include_processed=bool(args.include_processed)
    )

    mode = "ПРИМЕНЕНИЕ (--apply)" if args.apply else "DRY-RUN"
    print(f"=== {mode} ===")
    print(f"needle (NFC): {needle_nfc!r}")
    print(f"duplicates: {dup_path}")
    print(f"пропущено (processed, без --include-processed): {skipped_proc}")
    print(f"пар с обоими path по подстроке (к обработке): {matched}")
    print(f"будет выставлено processed=true: {updated}")
    print(f"уже processed=true среди совпавших: {already}")

    if not args.apply:
        print("Запусти с --apply чтобы записать duplicates-list.json.")
        return

    if updated == 0:
        print("Нечего записывать.")
        return

    write_json_atomic(dup_path, doc)
    print(f"Записано: {dup_path}")


if __name__ == "__main__":
    main()
