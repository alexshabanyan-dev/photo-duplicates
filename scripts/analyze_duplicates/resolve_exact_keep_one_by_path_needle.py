#!/usr/bin/env python3
"""
Для групп exact_duplicates в duplicates-list.json:

  • если в группе есть хотя бы один файл, чей path содержит заданную подстроку
    (сравнение после Unicode NFC). По умолчанию: «INDIA2026»
    (см. DEFAULT_PATH_NEEDLES_NFC). Другую подстроку — через --needle.

  • оставляем одну копию — первую в массиве files среди путей с этой подстрокой;

  • всем остальным file_id из группы ставим to_delete: true в *.files-list.json
    в каталоге result;

  • группе в duplicates-list.json выставляем processed: true (при --apply).

Запуск без --apply только печатает план (dry-run).

Пример:
  cd scripts/analyze_duplicates
  python3 resolve_exact_keep_one_by_path_needle.py
  python3 resolve_exact_keep_one_by_path_needle.py --apply
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
REPO_SCRIPTS = SCRIPT_DIR.parent


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def path_matches_any(path: str | None, needles_nfc: list[str]) -> bool:
    if not path or not isinstance(path, str):
        return False
    pn = nfc(path)
    return any(n in pn for n in needles_nfc)


DEFAULT_PATH_NEEDLES_NFC: list[str] = [
    nfc("INDIA2026"),
]


def collect_files_list_json(result_dir: Path) -> list[Path]:
    if not result_dir.is_dir():
        return []
    return sorted(result_dir.rglob("*.files-list.json"))


def get_mutable_entries(data: Any) -> tuple[list[dict[str, Any]], Any, bool]:
    """
    Возвращает (entries, root_for_save, root_is_list).
    root_for_save — тот же объект, что писать обратно (список или dict с files).
    """
    if isinstance(data, list):
        return data, data, True  # type: ignore[return-value]
    if isinstance(data, dict) and isinstance(data.get("files"), list):
        return data["files"], data, False  # type: ignore[return-value]
    return [], data, True


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def mark_to_delete_in_result(
    file_ids: set[str],
    result_dir: Path,
    *,
    apply: bool,
) -> tuple[int, int]:
    """Возвращает (сколько записей помечено, сколько json-файлов перезаписано)."""
    if not file_ids:
        return 0, 0
    ids_lower = {x.strip().lower() for x in file_ids if isinstance(x, str) and len(x.strip()) == 64}

    marked = 0
    touched_files = 0

    for jpath in collect_files_list_json(result_dir):
        try:
            raw = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] не JSON: {jpath}: {e}", file=sys.stderr)
            continue

        entries, root, _ = get_mutable_entries(raw)
        if not entries:
            continue

        changed = False
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            fid = entry.get("file_id")
            if not isinstance(fid, str):
                continue
            key = fid.strip().lower()
            if key not in ids_lower:
                continue
            if entry.get("to_delete") is True:
                continue
            if apply:
                entry["to_delete"] = True
            marked += 1
            changed = True

        if changed:
            if apply:
                write_json_atomic(jpath, root)
            touched_files += 1

    return marked, touched_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="exact_duplicates: оставить одну копию с путём по подстроке, остальные to_delete в result.",
    )
    parser.add_argument(
        "--duplicates",
        type=Path,
        default=SCRIPT_DIR / "duplicates-list.json",
        help="Путь к duplicates-list.json",
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=REPO_SCRIPTS / "files-list-generator" / "result",
        help="Каталог с *.files-list.json",
    )
    parser.add_argument(
        "--needle",
        type=str,
        default=None,
        metavar="TEXT",
        help=(
            "Подстрока в path (после NFC). "
            "Если не задано — по умолчанию: INDIA2026. "
            "Пример: --needle 'Помолвка 24.02.2019'."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записать изменения; без флага — только план (dry-run).",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Обрабатывать и группы с processed: true (по умолчанию только необработанные).",
    )
    args = parser.parse_args()

    dup_path: Path = args.duplicates.resolve()
    result_dir: Path = args.result_dir.resolve()
    if args.needle is None:
        needles_nfc = list(DEFAULT_PATH_NEEDLES_NFC)
    else:
        one = nfc(args.needle.strip())
        if not one:
            print("Пустая --needle", file=sys.stderr)
            sys.exit(1)
        needles_nfc = [one]

    if not dup_path.is_file():
        print(f"Нет файла: {dup_path}", file=sys.stderr)
        sys.exit(1)
    if not result_dir.is_dir():
        print(f"Нет каталога result: {result_dir}", file=sys.stderr)
        sys.exit(1)

    doc = json.loads(dup_path.read_text(encoding="utf-8"))
    groups = doc.get("exact_duplicates")
    if not isinstance(groups, list):
        print("В JSON нет массива exact_duplicates", file=sys.stderr)
        sys.exit(1)

    apply = bool(args.apply)
    mode = "ПРИМЕНЕНИЕ (--apply)" if apply else "DRY-RUN (без записи)"

    to_mark_ids: set[str] = set()
    groups_to_process: list[tuple[int, dict[str, Any], str, str]] = []
    # (index, group, keep_id, reason skip message if empty)

    skipped_processed = 0
    no_match = 0

    for idx, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        if group.get("processed") is True and not args.include_processed:
            skipped_processed += 1
            continue

        files = group.get("files")
        if not isinstance(files, list) or len(files) < 2:
            continue

        keep_fid: str | None = None
        for f in files:
            if not isinstance(f, dict):
                continue
            p = f.get("path")
            fid = f.get("file_id")
            if path_matches_any(p if isinstance(p, str) else None, needles_nfc):
                if isinstance(fid, str) and fid.strip():
                    keep_fid = fid.strip()
                    break

        if not keep_fid:
            no_match += 1
            continue

        all_ids: list[str] = []
        for f in files:
            if isinstance(f, dict) and isinstance(f.get("file_id"), str):
                h = f["file_id"].strip()
                if h:
                    all_ids.append(h)

        delete_ids = [x for x in all_ids if x.lower() != keep_fid.lower()]
        if not delete_ids:
            # В группе только один файл или все с одинаковым id (аномалия)
            groups_to_process.append((idx, group, keep_fid, "only_one_copy"))
            continue

        groups_to_process.append((idx, group, keep_fid, "ok"))
        for d in delete_ids:
            to_mark_ids.add(d)

    print(f"=== {mode} ===")
    print(f"Подстроки (NFC), достаточно одной: {needles_nfc!r}")
    print(f"duplicates: {dup_path}")
    print(f"result-dir: {result_dir}")
    print(f"Групп exact_duplicates всего: {len(groups)}")
    print(f"Пропущено (уже processed): {skipped_processed}")
    print(f"Групп без совпадения по path: {no_match}")
    print(f"Групп к обработке: {len(groups_to_process)}")
    print(f"Уникальных file_id к to_delete: {len(to_mark_ids)}")

    for idx, group, keep_fid, reason in groups_to_process[:15]:
        uid = group.get("uid", "")[:16] if isinstance(group.get("uid"), str) else "?"
        print(f"  - group[{idx}] uid={uid}… keep={keep_fid[:12]}… ({reason})")
    if len(groups_to_process) > 15:
        print(f"  … и ещё {len(groups_to_process) - 15} групп")

    if not groups_to_process:
        print("Нечего делать.")
        return

    if apply:
        marked, json_touched = mark_to_delete_in_result(to_mark_ids, result_dir, apply=True)
        print(f"\nПомечено to_delete в записях: {marked}, перезаписано JSON: {json_touched}")

        for _idx, group, _keep_fid, _reason in groups_to_process:
            group["processed"] = True

        write_json_atomic(dup_path, doc)
        print(f"Обновлён duplicates-list.json (processed для {len(groups_to_process)} групп).")
    else:
        marked, json_touched = mark_to_delete_in_result(to_mark_ids, result_dir, apply=False)
        print(f"\n[DRY-RUN] было бы помечено записей to_delete: {marked} (JSON файлов: {json_touched})")
        print("Запусти с --apply чтобы записать.")


if __name__ == "__main__":
    main()
