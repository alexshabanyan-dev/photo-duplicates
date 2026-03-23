#!/usr/bin/env python3
"""
Подсчёт расширений по всем сгенерированным files-list.json.

Считает данные по массиву объектов в файлах, например:
  scripts/files-list-generator/result/**/*.files-list.json

На выход:
  scripts/define-extensions/extensions.json

Формат:
{
  "mp4": 123,
  "avi": 45,
  "...": ...
}
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


def _normalize_ext(ext: str | None) -> str:
    if not ext:
        return "без_расширения"
    e = str(ext).strip().lower()
    if e.startswith("."):
        e = e[1:]
    return e or "без_расширения"


def _get_entry_extension(entry: dict) -> str:
    # Основной путь: поле, которое записывает files-list-generator.*
    ext = entry.get("extension")
    if ext:
        return _normalize_ext(ext)

    # fallback: попробуем вытащить из path
    p = entry.get("path") or ""
    suffix = Path(str(p)).suffix
    return _normalize_ext(suffix)


@dataclass
class _ExtStats:
    total: int = 0
    deleted: int = 0

    @property
    def existed(self) -> int:
        return self.total - self.deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Подсчитать расширения из files-list.json.")
    repo_root = Path(__file__).resolve().parent.parent.parent
    default_input_dir = repo_root / "scripts" / "files-list-generator" / "result"
    default_output = Path(__file__).resolve().parent / "extensions.json"

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir,
        help=f"Где искать files-list*.json (по умолчанию: {default_input_dir})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Куда записать extensions.json (по умолчанию: {default_output})",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*files-list.json",
        help="Шаблон имени файлов для подсчёта (по умолчанию: *files-list.json)",
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    output_path: Path = args.output
    pattern: str = args.pattern

    if not input_dir.is_dir():
        print(f"Входная папка не найдена: {input_dir}", file=sys.stderr)
        sys.exit(1)

    stats: dict[str, _ExtStats] = {}
    total_entries = 0
    all_entries = 0
    to_delete_files = 0
    deleted_files = 0
    matched_files = 0

    # Рекурсивно: у тебя файлы лежат в подпапках (разные корни/имена).
    for json_path in sorted(input_dir.rglob("*.json")):
        if pattern == "*files-list.json":
            if not json_path.name.endswith("files-list.json"):
                continue
        else:
            # Фильтруем по имени файла, не по пути.
            if not json_path.name.match(pattern):
                continue

        try:
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"Ошибка чтения {json_path}: {e}", file=sys.stderr)
            continue

        if not isinstance(data, list):
            continue

        matched_files += 1
        for entry in data:
            if not isinstance(entry, dict):
                continue

            all_entries += 1

            # Глобальные счётчики по статусам
            is_deleted = entry.get("deleted") is True
            is_to_delete = entry.get("to_delete") is True

            if is_deleted:
                deleted_files += 1
            elif is_to_delete:
                to_delete_files += 1

            # Для статистики расширений учитываем только НЕ удалённые записи.
            if is_deleted:
                continue

            ext_key = _get_entry_extension(entry)
            st = stats.get(ext_key)
            if st is None:
                st = _ExtStats()
                stats[ext_key] = st

            st.total += 1
            if is_to_delete:
                st.deleted += 1
            total_entries += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_count = all_entries
    remaining_files = total_entries

    # Стабильный порядок: сначала сводка, затем расширения по алфавиту.
    extensions_obj: dict[str, object] = {
        "total_count": total_count,
        "to_delete_files": to_delete_files,
        "deleted_files": deleted_files,
        "remaining_files": remaining_files,
    }
    for k in sorted(stats.keys()):
        st = stats[k]
        extensions_obj[k] = {
            "count": st.total,
            "deleted": st.deleted,
            "existed": st.existed,
        }

    output_path.write_text(
        json.dumps(extensions_obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Готово. Файлы: {matched_files}, записей: {total_entries}. "
        f"Расширений: {len(stats)}. Выход: {output_path}"
    )


if __name__ == "__main__":
    main()

