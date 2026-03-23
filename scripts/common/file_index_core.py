"""
Общая логика индексации файлов (SHA256, pHash) для генераторов списка файлов.

Pillow/imagehash импортируются внутри compute_phash; для полного скана они обязательны
(скрипты проверяют зависимости при старте).
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from .media_constants import IMAGE_EXTENSIONS

SYSTEM_JUNK_FILES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_phash(path: Path) -> tuple[str | None, str | None]:
    """
    Возвращает (phash_hex, error_message).
    """
    try:
        from PIL import Image, UnidentifiedImageError
        import imagehash
    except ImportError:
        return None, "missing_pillow_imagehash"

    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            ph = imagehash.phash(img)
        return str(ph), None
    except UnidentifiedImageError:
        return None, "unidentified_image"
    except OSError as e:
        return None, f"os_error: {e}"
    except Exception as e:  # noqa: BLE001
        return None, f"decode_error: {e}"


def should_skip(path: Path, include_hidden: bool) -> bool:
    if path.name in SYSTEM_JUNK_FILES:
        return True
    if include_hidden:
        return False
    return any(part.startswith(".") for part in path.parts)


def iter_files_streaming(root: Path, include_hidden: bool) -> Iterator[Path]:
    """
    Ленивый обход дерева без полного списка и без сортировки (порядок как у rglob).
    Удобно для потоковой подачи задач в пул, чтобы не ждать окончания полного скана.
    """
    root = root.resolve()
    for p in root.rglob("*"):
        if p.is_file() and not should_skip(p, include_hidden=include_hidden):
            yield p


def iter_files(root: Path, include_hidden: bool) -> list[Path]:
    files = list(iter_files_streaming(root, include_hidden))
    files.sort(key=lambda x: str(x).lower())
    return files


def build_entry_for_path(
    path: Path,
    root: Path,
    *,
    hamming_threshold: int,
    relative_paths: bool,
) -> dict[str, Any]:
    """
    Одна запись индекса для файла (тот же формат, что и в build_file_index_entries).
    Удобно вызывать из параллельных воркеров.
    """
    root = root.resolve()
    hamming_threshold = max(0, hamming_threshold)
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    display_path = str(rel) if relative_paths else str(path.resolve())
    name = path.name
    ext = path.suffix.lower()

    sha = sha256_file(path)

    phash_val: str | None = None
    phash_error: str | None = None
    if ext in IMAGE_EXTENSIONS:
        phash_val, phash_error = compute_phash(path)

    canon = str(path.resolve())
    item: dict[str, Any] = {
        "file_id": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
        "filename": name,
        "extension": ext,
        "path": display_path,
        "sha256": sha,
        "phash": phash_val,
        "hamming_threshold": hamming_threshold,
    }
    if phash_error is not None:
        item["phash_error"] = phash_error
    return item


def parallel_build_entry_task(
    args: tuple[int, str, str, int, bool],
) -> tuple[int, dict[str, Any]]:
    """
    Воркер для multiprocessing: должен жить в импортируемом модуле (не в __main__),
    иначе на macOS/Windows со spawn дочерние процессы не смогут его поднять.
    """
    idx, path_str, root_str, hamming_threshold, relative_paths = args
    entry = build_entry_for_path(
        Path(path_str),
        Path(root_str),
        hamming_threshold=hamming_threshold,
        relative_paths=relative_paths,
    )
    return idx, entry


def build_file_index_entries(
    root: Path,
    *,
    hamming_threshold: int,
    relative_paths: bool,
    include_hidden: bool,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Тот же формат записей, что и в result/files_index.json (корень — массив объектов).

    progress_callback: вызывается после обработки каждого файла с аргументами (текущий, всего),
    где текущий — от 1 до N (удобно для строки прогресса в консоли).
    """
    root = root.resolve()
    hamming_threshold = max(0, hamming_threshold)
    entries: list[dict[str, Any]] = []

    if progress_callback is not None:
        sys.stderr.write("Сбор списка файлов… ")
        sys.stderr.flush()
    paths = iter_files(root, include_hidden=include_hidden)
    total = len(paths)
    if progress_callback is not None:
        sys.stderr.write(f"\rНайдено файлов: {total}. ")
        sys.stderr.flush()

    for path in paths:
        entries.append(
            build_entry_for_path(
                path,
                root,
                hamming_threshold=hamming_threshold,
                relative_paths=relative_paths,
            )
        )
        if progress_callback is not None:
            progress_callback(len(entries), total)

    return entries
