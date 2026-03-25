#!/usr/bin/env python3
"""
Пометить файлы для удаления флагом `to_delete: true` в files-list.json.

Алгоритм:
1) В начале файла задаёшь EXTENSIONS_TO_MARK (например ["aae", "bin"])
2) Скрипт проходит по всем *.files-list.json в scripts/files-list-generator/result
3) Для записей, у которых extension входит в EXTENSIONS_TO_MARK, ставит entry["to_delete"] = MARK_VALUE
   и сохраняет JSON обратно на диск.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Расширения (без разницы с точкой или без): например ["aae", ".bin", "dll"]
EXTENSIONS_TO_MARK = ["webp"]
# Что проставлять в entry["to_delete"] для записей с нужным расширением.
MARK_VALUE = True

# Где лежат входные файлы (files-list-generator/result/**/*.files-list.json)
RESULT_DIR = (
    Path(__file__).resolve().parent.parent
    / "files-list-generator"
    / "result"
)


def _normalize_ext(ext: str) -> str:
    e = str(ext).strip().lower()
    if e.startswith("."):
        e = e[1:]
    return e


def main() -> None:
    ext_norms = {_normalize_ext(x) for x in EXTENSIONS_TO_MARK if _normalize_ext(x)}
    if not ext_norms:
        print("EXTENSIONS_TO_MARK не задан или пустой.", file=sys.stderr)
        sys.exit(1)

    if not RESULT_DIR.is_dir():
        print(f"RESULT_DIR не найден: {RESULT_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(RESULT_DIR.rglob("*.files-list.json"))
    if not files:
        print(f"Не найдено файлов *.files-list.json в: {RESULT_DIR}")
        return

    updated_files = 0
    marked_entries = 0
    updated_files_list: list[tuple[Path, int]] = []

    for json_path in files:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"Ошибка чтения {json_path}: {e}", file=sys.stderr)
            continue

        if not isinstance(data, list):
            continue

        changed = False
        marked_entries_in_file = 0
        for entry in data:
            if not isinstance(entry, dict):
                continue

            entry_ext = entry.get("extension") or ""
            entry_ext_norm = _normalize_ext(entry_ext)
            if entry_ext_norm not in ext_norms:
                continue

            current = entry.get("to_delete")
            if current != MARK_VALUE:
                entry["to_delete"] = MARK_VALUE
                changed = True
            marked_entries += 1
            marked_entries_in_file += 1

        if changed:
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            updated_files += 1
            updated_files_list.append((json_path, marked_entries_in_file))

    print(f"EXTENSIONS_TO_MARK={sorted(ext_norms)}")
    print(f"Всего файлов: {len(files)}")
    print(f"Обновлено файлов: {updated_files}")
    print(f"Помечено записей: {marked_entries}")
    if updated_files_list:
        print("\nФайлы, где были изменения:")
        for p, cnt in updated_files_list:
            print(f"  {p} (помечено записей: {cnt})")


if __name__ == "__main__":
    main()

