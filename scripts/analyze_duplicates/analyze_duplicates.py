#!/usr/bin/env python3
"""
Читает список файлов (по умолчанию files-list-generator/files-list.json — тот же формат записей,
что у result/files_index.json) и строит отчёт по дублям:
- exact_duplicates: у каждой группы uid (стабильный SHA256 от file_id файлов группы), processed; у каждого файла file_id
- near_duplicates: у каждой пары uid (стабильный SHA256 от двух file_id), processed; у сторон left/right — file_id

Выход по умолчанию: scripts/analyze_duplicates/duplicates-list.json.

По умолчанию записи из индекса, у которых файл уже удалён с диска, не участвуют
в анализе. Медиа лежат в <репо>/files; если в индексе остались абсолютные пути
к старым каталогам …/storage/files/… или …/scripts/files/…, они переназначаются на …/files/….
Флаг --include-missing отключает фильтрацию.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Скрипт лежит в scripts/analyze_duplicates/; отчёт по умолчанию — в этой же папке.
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _SCRIPTS_DIR.parent

DEFAULT_INPUT = _SCRIPTS_DIR / "files-list-generator" / "files-list.json"
DEFAULT_OUTPUT = _SCRIPT_DIR / "duplicates-list.json"

# Медиа в корне репозитория; старые абсолютные пути могли указывать на …/storage/files/… или …/scripts/files/…
MEDIA_FILES_ROOT = _REPO_ROOT / "files"
_LEGACY_MEDIA_ROOTS = (
    _REPO_ROOT / "storage" / "files",
    _SCRIPTS_DIR / "files",
)


def resolve_output_in_script_dir(output_arg: Path) -> Path:
    """Итоговый JSON всегда внутри папки скрипта (scripts/analyze_duplicates/)."""
    out_root = _SCRIPT_DIR.resolve()
    rel = Path(output_arg.name) if output_arg.is_absolute() else output_arg
    if str(rel).strip() == "" or rel == Path("."):
        print("Укажи имя файла для --output, например duplicates-list.json", file=sys.stderr)
        sys.exit(1)
    out_path = (out_root / rel).resolve()
    try:
        out_path.relative_to(out_root)
    except ValueError:
        print(f"--output должен быть внутри {out_root}", file=sys.stderr)
        sys.exit(1)
    return out_path


def stable_file_id(canonical_path: str) -> str:
    """Стабильный id файла для API (SHA256 от абсолютного пути в UTF-8)."""
    return hashlib.sha256(canonical_path.encode("utf-8")).hexdigest()


def stable_near_pair_uid(file_id_left: Any, file_id_right: Any) -> str:
    """
    Стабильный id пары near_duplicates: одинаковый при пересборке отчёта для тех же двух файлов.
    SHA256 от двух file_id в лексикографическом порядке (разделитель \\n).
    """
    a = file_id_left if isinstance(file_id_left, str) and file_id_left.strip() else None
    b = file_id_right if isinstance(file_id_right, str) and file_id_right.strip() else None
    if a is not None and b is not None:
        x, y = sorted((a.lower(), b.lower()))
        return hashlib.sha256(f"{x}\n{y}".encode("utf-8")).hexdigest()
    return str(uuid.uuid4())


def stable_exact_group_uid(items: list[dict[str, Any]], content_sha256: str) -> str:
    """
    Стабильный id группы exact_duplicates по множеству file_id участников.
    Если file_id нет — fallback на отсортированные path, иначе на sha256 контента.
    """
    ids = sorted(
        {
            str(x).lower()
            for x in (item.get("file_id") for item in items)
            if isinstance(x, str) and x.strip()
        }
    )
    if len(ids) >= 2:
        return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
    paths = sorted(
        {
            str(p)
            for item in items
            for p in [item.get("path")]
            if isinstance(p, str) and p.strip()
        }
    )
    if len(paths) >= 2:
        return hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest()
    return hashlib.sha256(f"exact:sha256:{content_sha256}".encode("utf-8")).hexdigest()


def resolve_entry_media_path(path_str: str) -> Path | None:
    """
    Сначала путь как в индексе; если файла нет — пробуем переназначить
    старые префиксы …/storage/files/… или …/scripts/files/… на …/files/….
    """
    raw = Path(path_str).expanduser()
    try:
        direct = raw.resolve()
    except OSError:
        direct = None
    if direct is not None and direct.is_file():
        return direct

    if not MEDIA_FILES_ROOT.is_dir():
        return None

    media = MEDIA_FILES_ROOT.resolve()
    absolute = direct if direct is not None else raw.resolve()
    for old_base in _LEGACY_MEDIA_ROOTS:
        try:
            ob = old_base.resolve()
            rel = absolute.relative_to(ob)
            candidate = (media / rel).resolve()
            if candidate.is_file():
                return candidate
        except (ValueError, OSError):
            continue

    # Путь уже под <репо>/files, но resolve() не указывал на существующий файл — проверка ещё раз
    try:
        absolute = direct if direct is not None else raw.resolve()
        rel = absolute.relative_to(media)
        candidate = (media / rel).resolve()
        if candidate.is_file():
            return candidate
    except (ValueError, OSError):
        pass

    return None


def filter_entries_existing_on_disk(
    entries: list[dict[str, Any]],
    *,
    include_missing: bool,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Оставляет записи с существующим файлом; path в записи при необходимости
    обновляется на актуальный абсолютный путь (<репо>/files/…).

    Возвращает (список, число_пропущенных, число_переписанных_путей).
    """
    if include_missing:
        rewritten = 0
        for e in entries:
            p = e.get("path")
            if not isinstance(p, str) or not p.strip():
                continue
            resolved = resolve_entry_media_path(p)
            if resolved is not None:
                canonical = str(resolved)
                if canonical != p:
                    e["path"] = canonical
                    rewritten += 1
                e["file_id"] = stable_file_id(canonical)
            else:
                try:
                    e["file_id"] = stable_file_id(str(Path(p).expanduser().resolve()))
                except OSError:
                    e["file_id"] = stable_file_id(p)
        return entries, 0, rewritten
    kept: list[dict[str, Any]] = []
    skipped = 0
    path_rewritten = 0
    for e in entries:
        p = e.get("path")
        if not isinstance(p, str) or not p.strip():
            skipped += 1
            continue
        resolved = resolve_entry_media_path(p)
        if resolved is None:
            skipped += 1
            continue
        canonical = str(resolved)
        if canonical != p:
            path_rewritten += 1
            e["path"] = canonical
        e["file_id"] = stable_file_id(canonical)
        kept.append(e)
    return kept, skipped, path_rewritten


def load_entries(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("files"), list):
        return [x for x in data["files"] if isinstance(x, dict)]
    print("Неверный формат входного JSON: ожидается массив или объект с ключом files", file=sys.stderr)
    sys.exit(1)


def open_two_files_command(path_left: str, path_right: str) -> str:
    """Команда для терминала macOS: открыть оба файла."""
    return f"open {shlex.quote(path_left)} {shlex.quote(path_right)}"


def hamming_distance_hex(a: str, b: str) -> int:
    if len(a) != len(b):
        raise ValueError("pHash разной длины")
    # Быстрое расстояние: xor и подсчёт установленных битов.
    return (int(a, 16) ^ int(b, 16)).bit_count()


def group_exact_duplicates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sha: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        sha = entry.get("sha256")
        if isinstance(sha, str) and sha:
            by_sha.setdefault(sha, []).append(entry)

    groups: list[dict[str, Any]] = []
    for sha, items in by_sha.items():
        if len(items) < 2:
            continue
        paths_two: list[str] = []
        for item in items:
            p = item.get("path")
            if isinstance(p, str) and p:
                paths_two.append(p)
            if len(paths_two) >= 2:
                break
        cmd: str | None = (
            open_two_files_command(paths_two[0], paths_two[1]) if len(paths_two) >= 2 else None
        )
        groups.append(
            {
                "uid": stable_exact_group_uid(items, sha),
                "sha256": sha,
                "count": len(items),
                "command": cmd,
                "processed": False,
                "files": [
                    {
                        "file_id": item.get("file_id"),
                        "filename": item.get("filename"),
                        "extension": item.get("extension"),
                        "path": item.get("path"),
                        "phash": item.get("phash"),
                    }
                    for item in items
                ],
            }
        )

    groups.sort(key=lambda g: g["count"], reverse=True)
    return groups


def build_near_duplicate_pairs(entries: list[dict[str, Any]], default_threshold: int) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for entry in entries:
        ph = entry.get("phash")
        if isinstance(ph, str) and ph:
            valid.append(entry)

    pairs: list[dict[str, Any]] = []
    for i in range(len(valid)):
        a = valid[i]
        a_phash = str(a["phash"])
        a_thr = int(a.get("hamming_threshold", default_threshold))
        for j in range(i + 1, len(valid)):
            b = valid[j]
            b_phash = str(b["phash"])
            b_thr = int(b.get("hamming_threshold", default_threshold))
            # Exact-дубли не дублируем в разделе near_duplicates.
            a_sha = a.get("sha256")
            b_sha = b.get("sha256")
            if isinstance(a_sha, str) and isinstance(b_sha, str) and a_sha and a_sha == b_sha:
                continue

            if len(a_phash) != len(b_phash):
                continue

            distance = hamming_distance_hex(a_phash, b_phash)
            threshold = min(a_thr, b_thr)
            if distance <= threshold:
                path_a = a.get("path")
                path_b = b.get("path")
                cmd: str | None = None
                if isinstance(path_a, str) and isinstance(path_b, str) and path_a and path_b:
                    cmd = open_two_files_command(path_a, path_b)
                pairs.append(
                    {
                        "uid": stable_near_pair_uid(a.get("file_id"), b.get("file_id")),
                        "distance": distance,
                        "threshold_used": threshold,
                        "command": cmd,
                        "processed": False,
                        "left": {
                            "file_id": a.get("file_id"),
                            "filename": a.get("filename"),
                            "extension": a.get("extension"),
                            "path": a.get("path"),
                            "sha256": a.get("sha256"),
                            "phash": a_phash,
                        },
                        "right": {
                            "file_id": b.get("file_id"),
                            "filename": b.get("filename"),
                            "extension": b.get("extension"),
                            "path": b.get("path"),
                            "sha256": b.get("sha256"),
                            "phash": b_phash,
                        },
                    }
                )
    pairs.sort(key=lambda p: p["distance"])
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Анализ дублей по списку файлов (JSON с записями как в files_index)")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Входной JSON с индексом файлов (по умолчанию: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("duplicates-list.json"),
        help=f"Имя/подпуть выходного JSON внутри analyze_duplicates/ (по умолчанию: {DEFAULT_OUTPUT.name})",
    )
    parser.add_argument(
        "--hamming-threshold",
        type=int,
        default=8,
        help="Дефолтный порог Хэмминга, если в записи нет hamming_threshold",
    )
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Не отфильтровывать удалённые файлы (по умолчанию в отчёт попадают только существующие на диске)",
    )
    args = parser.parse_args()

    in_path = args.input.resolve() if args.input.is_absolute() else (Path.cwd() / args.input).resolve()
    if not in_path.is_file():
        print(f"Входной файл не найден: {in_path}", file=sys.stderr)
        sys.exit(1)

    out_path = resolve_output_in_script_dir(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    entries_all = load_entries(in_path)
    entries, skipped_missing, paths_rewritten = filter_entries_existing_on_disk(
        entries_all,
        include_missing=args.include_missing,
    )
    if paths_rewritten:
        print(
            f"Путей из индекса переписано на канонический медиа-корень: {paths_rewritten} "
            f"(в т.ч. старые …/storage|scripts/files/… → …/files/…)",
            file=sys.stderr,
        )
    if skipped_missing:
        print(
            f"Пропущено записей (файла нет на диске): {skipped_missing} "
            f"(пересканируй: scan_files_to_json.py, или используй --include-missing)",
            file=sys.stderr,
        )
    default_threshold = max(0, args.hamming_threshold)

    exact_groups = group_exact_duplicates(entries)
    near_pairs = build_near_duplicate_pairs(entries, default_threshold=default_threshold)

    report = {
        "source_index": str(in_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_entry_count": len(entries_all),
        "skipped_missing_files": skipped_missing,
        "index_paths_rewritten_to_storage": paths_rewritten,
        "file_count": len(entries),
        "exact_duplicates_group_count": len(exact_groups),
        "near_duplicates_pair_count": len(near_pairs),
        "exact_duplicates": exact_groups,
        "near_duplicates": near_pairs,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Готово: отчёт сохранён в {out_path}")
    print(f"Точные дубли (группы): {len(exact_groups)}")
    print(f"Похожие дубли (пары): {len(near_pairs)}")


if __name__ == "__main__":
    main()
