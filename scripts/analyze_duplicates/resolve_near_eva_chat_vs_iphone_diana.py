#!/usr/bin/env python3
"""
near_duplicates: пары, где один путь содержит «Ева (чат)», другой — «Iphone Диана».

Для каждой такой пары (только если на одной стороне только «Ева (чат)», на другой только
«Iphone Диана» в смысле проверки ниже):
  • в *.files-list.json у файла с «Iphone Диана» ставим to_delete: true;
  • файл с «Ева (чат)» не меняем;
  • паре в duplicates-list.json — processed: true (при --apply).

Сравнение подстрок в path после Unicode NFC. По умолчанию dry-run.

Пример:
  cd scripts/analyze_duplicates
  python3 resolve_near_eva_chat_vs_iphone_diana.py
  python3 resolve_near_eva_chat_vs_iphone_diana.py --apply
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


# Подстроки после NFC (как в путях на диске).
NEEDLE_EVA_CHAT_NFC = nfc("Ева (чат)")
NEEDLE_IPHONE_DIANA_NFC = nfc("Iphone Диана")


def collect_files_list_json(result_dir: Path) -> list[Path]:
    if not result_dir.is_dir():
        return []
    return sorted(result_dir.rglob("*.files-list.json"))


def get_mutable_entries(data: Any) -> tuple[list[dict[str, Any]], Any, bool]:
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


def path_contains(path: str | None, needle_nfc: str) -> bool:
    if not path or not isinstance(path, str):
        return False
    return needle_nfc in nfc(path)


def classify_pair_side(
    path: str | None, *, eva_nfc: str, diana_nfc: str
) -> tuple[bool, bool]:
    """(has_eva, has_diana) после NFC."""
    if not path or not isinstance(path, str):
        return False, False
    pn = nfc(path)
    return eva_nfc in pn, diana_nfc in pn


def diana_file_id_to_delete_for_pair(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    eva_nfc: str,
    diana_nfc: str,
) -> str | None:
    """
    Возвращает file_id стороны «Iphone Диана», если:
    - с одной стороны путь содержит eva и не содержит diana;
    - с другой стороны путь содержит diana и не содержит eva.
    Иначе None.
    """
    le, ld = classify_pair_side(left.get("path"), eva_nfc=eva_nfc, diana_nfc=diana_nfc)
    re, rd = classify_pair_side(right.get("path"), eva_nfc=eva_nfc, diana_nfc=diana_nfc)

    if le and not ld and rd and not re:
        fid = right.get("file_id")
        return fid.strip() if isinstance(fid, str) and fid.strip() else None
    if re and not rd and ld and not le:
        fid = left.get("file_id")
        return fid.strip() if isinstance(fid, str) and fid.strip() else None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "near_duplicates: пары «Ева (чат)» × «Iphone Диана» — пометить Diana to_delete, паре processed."
        ),
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
        "--eva-needle",
        type=str,
        default="Ева (чат)",
        help="Подстрока пути для стороны «оставляем» (NFC)",
    )
    parser.add_argument(
        "--diana-needle",
        type=str,
        default="Iphone Диана",
        help="Подстрока пути для стороны to_delete (NFC)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записать изменения; без флага — только план (dry-run).",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Обрабатывать и пары с processed: true (по умолчанию только необработанные).",
    )
    args = parser.parse_args()

    eva_nfc = nfc(args.eva_needle.strip())
    diana_nfc = nfc(args.diana_needle.strip())
    if not eva_nfc or not diana_nfc:
        print("Пустая --eva-needle или --diana-needle", file=sys.stderr)
        sys.exit(1)

    dup_path = args.duplicates.resolve()
    result_dir = args.result_dir.resolve()

    if not dup_path.is_file():
        print(f"Нет файла: {dup_path}", file=sys.stderr)
        sys.exit(1)
    if not result_dir.is_dir():
        print(f"Нет каталога result: {result_dir}", file=sys.stderr)
        sys.exit(1)

    doc = json.loads(dup_path.read_text(encoding="utf-8"))
    pairs = doc.get("near_duplicates")
    if not isinstance(pairs, list):
        print("В JSON нет массива near_duplicates", file=sys.stderr)
        sys.exit(1)

    apply = bool(args.apply)
    mode = "ПРИМЕНЕНИЕ (--apply)" if apply else "DRY-RUN (без записи)"

    to_mark_ids: set[str] = set()
    matched_indices: list[int] = []
    skipped_processed = 0
    skipped_no_fid = 0

    for idx, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            continue
        if pair.get("processed") is True and not args.include_processed:
            skipped_processed += 1
            continue

        left = pair.get("left") if isinstance(pair.get("left"), dict) else {}
        right = pair.get("right") if isinstance(pair.get("right"), dict) else {}

        delete_fid = diana_file_id_to_delete_for_pair(
            left, right, eva_nfc=eva_nfc, diana_nfc=diana_nfc
        )
        if not delete_fid:
            continue
        if len(delete_fid.strip()) != 64:
            skipped_no_fid += 1
            print(
                f"  [warn] pair[{idx}] невалидный file_id для to_delete: {delete_fid!r}",
                file=sys.stderr,
            )
            continue

        to_mark_ids.add(delete_fid)
        matched_indices.append(idx)

    print(f"=== {mode} ===")
    print(f"eva needle (NFC): {eva_nfc!r}")
    print(f"diana needle (NFC): {diana_nfc!r}")
    print(f"duplicates: {dup_path}")
    print(f"result-dir: {result_dir}")
    print(f"Пар near_duplicates всего: {len(pairs)}")
    print(f"Пропущено (уже processed): {skipped_processed}")
    print(f"Совпало пар (Ева × Диана по правилам): {len(matched_indices)}")
    print(f"Пропущено (битый file_id): {skipped_no_fid}")
    print(f"Уникальных file_id к to_delete (Диана): {len(to_mark_ids)}")

    for i in matched_indices[:20]:
        pair = pairs[i]
        uid = (pair.get("uid") or "")[:16] if isinstance(pair.get("uid"), str) else "?"
        left = pair.get("left") if isinstance(pair.get("left"), dict) else {}
        right = pair.get("right") if isinstance(pair.get("right"), dict) else {}
        df = diana_file_id_to_delete_for_pair(left, right, eva_nfc=eva_nfc, diana_nfc=diana_nfc)
        print(f"  - pair[{i}] uid={uid}… to_delete file_id={df[:16] if df else '?'}…")
    if len(matched_indices) > 20:
        print(f"  … и ещё {len(matched_indices) - 20} пар")

    if not matched_indices:
        print("Нечего делать.")
        return

    if apply:
        marked, json_touched = mark_to_delete_in_result(to_mark_ids, result_dir, apply=True)
        print(f"\nПомечено to_delete в записях: {marked}, перезаписано JSON: {json_touched}")

        for idx in matched_indices:
            p = pairs[idx]
            if isinstance(p, dict):
                p["processed"] = True

        write_json_atomic(dup_path, doc)
        print(f"Обновлён duplicates-list.json (processed для {len(matched_indices)} пар).")
    else:
        marked, json_touched = mark_to_delete_in_result(to_mark_ids, result_dir, apply=False)
        print(f"\n[DRY-RUN] было бы помечено записей to_delete: {marked} (JSON файлов: {json_touched})")
        print("Запусти с --apply чтобы записать.")


if __name__ == "__main__":
    main()
