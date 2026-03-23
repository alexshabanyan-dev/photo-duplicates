#!/usr/bin/env python3
"""
Удаление файлов по флагу `to_delete` из всех files-list.json в result.

Логика:
1) Ищем все файлы: scripts/files-list-generator/result/**/*.files-list.json
2) Для каждой записи, где to_delete == true и deleted != true:
   - удаляем файл по entry["path"]
   - ставим entry["deleted"] = true
3) Сохраняем изменённый JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


RESULT_DIR = (
    Path(__file__).resolve().parent.parent
    / "files-list-generator"
    / "result"
)


def main() -> None:
    if not RESULT_DIR.is_dir():
        print(f"RESULT_DIR не найден: {RESULT_DIR}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(RESULT_DIR.rglob("*.files-list.json"))
    if not json_files:
        print(f"Не найдено файлов *.files-list.json в: {RESULT_DIR}")
        return

    total_json = len(json_files)
    updated_json = 0
    deleted_files_count = 0
    failed_delete_count = 0
    skipped_count = 0
    changed_files: list[str] = []

    for json_path in json_files:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"Ошибка чтения {json_path}: {e}", file=sys.stderr)
            continue

        if not isinstance(data, list):
            continue

        changed = False
        for entry in data:
            if not isinstance(entry, dict):
                continue

            if entry.get("to_delete") is not True:
                continue

            if entry.get("deleted") is True:
                skipped_count += 1
                continue

            raw_path = entry.get("path")
            if not raw_path:
                failed_delete_count += 1
                continue

            path = Path(str(raw_path))
            try:
                if path.exists():
                    path.unlink()
                    deleted_files_count += 1
                # Если файла уже нет — считаем это "удалён".
                entry["deleted"] = True
                changed = True
            except Exception as e:  # noqa: BLE001
                failed_delete_count += 1
                print(f"Не удалось удалить {path}: {e}", file=sys.stderr)

        if changed:
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            updated_json += 1
            changed_files.append(str(json_path))

    print(f"Всего JSON-файлов: {total_json}")
    print(f"Обновлено JSON-файлов: {updated_json}")
    print(f"Удалено файлов с диска: {deleted_files_count}")
    print(f"Пропущено (уже deleted=true): {skipped_count}")
    print(f"Ошибок удаления: {failed_delete_count}")
    if changed_files:
        print("\nИзменённые JSON:")
        for p in changed_files:
            print(f"  {p}")


if __name__ == "__main__":
    main()

