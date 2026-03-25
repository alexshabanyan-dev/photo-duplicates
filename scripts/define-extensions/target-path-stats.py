#!/usr/bin/env python3
"""
Статистика по подпапкам 1-го уровня внутри TARGET_PATH.

Как пользоваться:
- В начале файла задай TARGET_PATH (абсолютный путь к папке, как в поле path в JSON).
- Скрипт найдёт ВСЕ подпапки, которые лежат ПРЯМО внутри TARGET_PATH (1 уровень),
  и посчитает статистику по всем файлам внутри каждой подпапки (включая вложенные подпапки).
- На выходе: target_path_data.json рядом со скриптом.

Метрики:
- total_files: всего найдено записей в этой подпапке
- processed_files: уже обработано (deleted == true OR to_delete == true OR distribution_kept == true)
- deleted_files: deleted == true
- remaining_to_process: ещё в очереди (НЕ deleted/ to_delete/ distribution_kept)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Абсолютный путь к папке (как в поле path в JSON). Пример:
# TARGET_PATH = "/Volumes/SAE 1/Фото/Iphone Диана"
TARGET_PATH = "/Volumes/SAE 1/Фото"


def _is_true(v: object) -> bool:
    return v is True


def _normalize_dir_prefix(p: str) -> str:
    return p.rstrip("/")


def _child_dir_name(file_path: str, target_dir: str) -> str | None:
    """
    Возвращает имя подпапки 1-го уровня внутри target_dir, к которой относится file_path.
    Если файл лежит прямо в target_dir (без подпапки) — возвращает None.
    """
    base = _normalize_dir_prefix(target_dir)
    prefix = base + "/"
    if not file_path.startswith(prefix):
        return None
    rest = file_path[len(prefix) :]
    if not rest:
        return None
    first = rest.split("/", 1)[0]
    return first or None


def main() -> int:
    if not TARGET_PATH.strip():
        print("TARGET_PATH пустой — задай путь к папке в начале файла.", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parent.parent.parent
    input_json = repo_root / "scripts" / "files-list-generator" / "result" / "results.files-list.json"
    output_json = Path(__file__).resolve().parent / "target_path_data.json"

    if not input_json.is_file():
        print(f"Не найден входной JSON: {input_json}", file=sys.stderr)
        return 1

    with input_json.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Ожидался JSON-массив в results.files-list.json", file=sys.stderr)
        return 1

    target_dir = _normalize_dir_prefix(TARGET_PATH)
    prefix = target_dir + "/"

    # child_dir_name -> counters
    stats: dict[str, dict[str, int]] = {}

    for item in data:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        if not isinstance(p, str):
            continue
        if not p.startswith(prefix):
            continue

        child = _child_dir_name(p, target_dir)
        if child is None:
            # Файлы, которые лежат прямо в TARGET_PATH, не относятся ни к одной подпапке 1-го уровня.
            continue

        st = stats.get(child)
        if st is None:
            st = {
                "total_files": 0,
                "processed_files": 0,
                "deleted_files": 0,
                "remaining_to_process": 0,
            }
            stats[child] = st

        st["total_files"] += 1

        is_deleted = _is_true(item.get("deleted"))
        is_to_delete = _is_true(item.get("to_delete"))
        is_kept = _is_true(item.get("distribution_kept"))

        if is_deleted:
            st["deleted_files"] += 1

        if is_deleted or is_to_delete or is_kept:
            st["processed_files"] += 1
        else:
            st["remaining_to_process"] += 1

    subfolders = []
    for child_name in sorted(stats.keys()):
        st = stats[child_name]
        subfolders.append(
            {
                "target_path": f"{target_dir}/{child_name}",
                "input_json": str(input_json),
                **st,
            }
        )

    out = {
        "target_path": target_dir,
        "input_json": str(input_json),
        "subfolders": subfolders,
    }

    with output_json.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"OK: wrote {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
