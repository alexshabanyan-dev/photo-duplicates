#!/usr/bin/env python3
"""
Параллельная генерация files-list.json: те же записи, что у files-list-generator.py,
но обработка файлов идёт в нескольких процессах (SHA256 + pHash параллельно на разных ядрах).

Запуск из папки scripts/:

  python3 files-list-generator/files-list-generator-parallel.py

По умолчанию корень скана и путь к JSON задаются SCAN_ROOT, OUTPUT_RESULT_SUBDIR и
OUTPUT_JSON_FILENAME (см. комментарии к константам). Зависимости и перезапуск через scripts/.venv —
как у files-list-generator.py.

По умолчанию в индекс попадают только фото и картинки (см. common.media_constants.PHOTO_INDEX_EXTENSIONS:
jpg, png, heic, cr2, … без mov/mp4/avi и т.д.). Полный обход без фильтра — флаг --all-files.

Сначала полный обход: считаем файлы и печатаем «Найдено файлов: N», затем обработка.
В stderr строка прогресса «Обработано: текущий/всего», имя файла и размер. В конце в stdout — время.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from pathlib import Path
from typing import Any

# =============================================================================
# Настройка: сколько параллельных процессов (подбери под CPU и диск).
# 0 или отрицательное значение → автоматически os.cpu_count() (минимум 1).
# =============================================================================
WORKER_COUNT = 4

# Папка для скана и выходной JSON в files-list-generator/result/.
# OUTPUT_RESULT_SUBDIR:
#   • если в строке есть «/» или «\» — это подпапки под result/, путь: result/…/OUTPUT_JSON_FILENAME;
#   • иначе — префикс имени файла БЕЗ подпапок: result/(OUTPUT_RESULT_SUBDIR + OUTPUT_JSON_FILENAME).
#     Пример: "Фото.Диана." + "files-list.json" → result/Фото.Диана.files-list.json
# OUTPUT_JSON_FILENAME — хвост имени файла (например files-list.json).
SCAN_ROOT = Path('/Volumes/SAE 1/Фото')
OUTPUT_RESULT_SUBDIR = "results."
OUTPUT_JSON_FILENAME = "files-list.json"

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _SCRIPT_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _venv_python() -> Path | None:
    if platform.system() == "Windows":
        candidates = [_SCRIPTS_DIR / ".venv" / "Scripts" / "python.exe"]
    else:
        bin_dir = _SCRIPTS_DIR / ".venv" / "bin"
        candidates = [bin_dir / "python3", bin_dir / "python"]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _running_in_scripts_venv() -> bool:
    try:
        venv_home = (_SCRIPTS_DIR / ".venv").resolve()
        prefix = Path(sys.prefix).resolve()
    except OSError:
        return False
    return prefix == venv_home


def _ensure_pillow_imagehash() -> None:
    try:
        import imagehash  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        venv_py = _venv_python()
        script = Path(__file__).resolve()
        if venv_py is not None and not _running_in_scripts_venv():
            r = subprocess.run(
                [str(venv_py), str(script), *sys.argv[1:]],
                check=False,
            )
            raise SystemExit(r.returncode if r.returncode is not None else 1)
        print(
            "Нет Pillow / ImageHash. Установи зависимости (scripts/README.md, requirements.txt).",
            file=sys.stderr,
        )
        sys.exit(1)


_ensure_pillow_imagehash()

from common.file_index_core import (  # noqa: E402
    build_entry_for_path,
    iter_files_streaming,
    parallel_build_entry_task,
)
from common.media_constants import IMAGE_EXTENSIONS, PHOTO_INDEX_EXTENSIONS  # noqa: E402


def _effective_workers(requested: int) -> int:
    if requested <= 0:
        return max(1, os.cpu_count() or 1)
    return requested


def _default_output_path() -> Path:
    """
    result/…/OUTPUT_JSON_FILENAME если в OUTPUT_RESULT_SUBDIR есть разделитель пути;
    иначе result/(OUTPUT_RESULT_SUBDIR + OUTPUT_JSON_FILENAME) в одном каталоге result/.
    """
    base = _SCRIPT_DIR / "result"
    raw = OUTPUT_RESULT_SUBDIR or ""
    normalized = raw.replace("\\", "/")
    if "/" in normalized:
        parts = [p for p in normalized.strip("/").split("/") if p]
        if parts:
            base = base.joinpath(*parts)
        return base / OUTPUT_JSON_FILENAME
    return base / f"{raw}{OUTPUT_JSON_FILENAME}"


def _format_duration(seconds: float) -> str:
    """Человекочитаемая длительность для вывода в консоль."""
    if seconds < 0:
        seconds = 0.0
    if seconds < 60:
        return f"{seconds:.1f} с"
    total = int(round(seconds))
    m, s = divmod(total, 60)
    if m < 60:
        return f"{m} мин {s} с"
    h, m = divmod(m, 60)
    return f"{h} ч {m} мин {s} с"


def _human_bytes(n: int) -> str:
    """Размер файла для строки прогресса."""
    if n < 0:
        return "?"
    if n < 1024:
        return f"{n} B"
    x = float(n)
    for unit in ("KB", "MB", "GB", "TB"):
        x /= 1024.0
        if x < 1024.0 or unit == "TB":
            return f"{x:.1f} {unit}"
    return f"{n} B"


_PROGRESS_NAME_MAX = 52


def _shorten_filename(name: str, max_len: int = _PROGRESS_NAME_MAX) -> str:
    if len(name) <= max_len:
        return name
    return name[: max_len - 1] + "…"


def main() -> None:
    default_root = SCAN_ROOT
    default_out = _default_output_path()

    parser = argparse.ArgumentParser(
        description=(
            "Параллельно сгенерировать files-list.json (несколько процессов, см. WORKER_COUNT в скрипте)."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root,
        help=f"Корень обхода (по умолчанию: константа SCAN_ROOT={default_root})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=default_out,
        help=(
            "Куда записать JSON (по умолчанию: "
            f"{default_out.relative_to(_SCRIPT_DIR)}, сейчас {default_out})"
        ),
    )
    parser.add_argument(
        "--hamming-threshold",
        type=int,
        default=8,
        help="Порог Хэмминга в каждой записи",
    )
    parser.add_argument(
        "--relative-paths",
        action="store_true",
        help="В path писать путь относительно --root",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Учитывать скрытые файлы/папки",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Не печатать сводку по расширениям",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Не выводить прогресс в stderr",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        metavar="N",
        help=f"Число процессов (по умолчанию константа WORKER_COUNT={WORKER_COUNT}; 0 = авто по CPU)",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Не фильтровать по расширению: как раньше, все файлы под корнем (включая видео)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Папка не найдена: {root}", file=sys.stderr)
        sys.exit(1)

    t_start = time.perf_counter()

    workers = _effective_workers(args.jobs if args.jobs is not None else WORKER_COUNT)
    show_progress = not args.quiet and not args.no_progress

    if show_progress:
        try:
            sys.stderr.reconfigure(line_buffering=True)  # чаще сбрасывать строку прогресса
        except (AttributeError, OSError, ValueError):
            pass

    root_s = str(root)
    hamming = max(0, args.hamming_threshold)
    rel_paths = args.relative_paths

    if show_progress:
        sys.stderr.write("Сбор списка файлов… ")
        sys.stderr.flush()
    paths = list(iter_files_streaming(root, include_hidden=args.include_hidden))
    paths.sort(key=lambda x: str(x).lower())
    found_all = len(paths)
    if not args.all_files:
        ext_set = PHOTO_INDEX_EXTENSIONS
        paths = [p for p in paths if p.suffix.lower() in ext_set]
    total_files = len(paths)
    if show_progress:
        if args.all_files:
            sys.stderr.write(f"\rНайдено файлов: {total_files}. Процессов: {workers}\n")
        else:
            sys.stderr.write(
                f"\rНайдено файлов: {found_all} (после фильтра фото: {total_files}). "
                f"Процессов: {workers}\n"
            )
        sys.stderr.flush()

    done_count = 0

    def _progress_line(current_path: Path | None) -> None:
        head = f"Обработано: {done_count}/{total_files}"
        if current_path is not None:
            try:
                size_b = current_path.stat().st_size
            except OSError:
                size_b = -1
            nm = _shorten_filename(current_path.name)
            sz = _human_bytes(size_b) if size_b >= 0 else "?"
            line = f"{head}  ·  {nm}  ({sz})"
        else:
            line = head
        sys.stderr.write("\r" + line + "\033[K")
        sys.stderr.flush()

    entries_list: list[dict[str, Any]] = []

    if workers == 1:
        for path in paths:
            entries_list.append(
                build_entry_for_path(
                    path,
                    root,
                    hamming_threshold=hamming,
                    relative_paths=rel_paths,
                )
            )
            done_count += 1
            if show_progress:
                _progress_line(path)
        if show_progress:
            sys.stderr.write("\n")
    else:
        results_by_idx: dict[int, dict[str, Any]] = {}
        pending: set[Future] = set()
        max_in_flight = max(workers * 8, 32)
        idx = 0
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for path in paths:
                task = (idx, str(path.resolve()), root_s, hamming, rel_paths)
                pending.add(pool.submit(parallel_build_entry_task, task))
                idx += 1
                while len(pending) >= max_in_flight:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for f in done:
                        i, entry = f.result()
                        results_by_idx[i] = entry
                        done_count += 1
                        if show_progress:
                            _progress_line(paths[i])
            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for f in done:
                    i, entry = f.result()
                    results_by_idx[i] = entry
                    done_count += 1
                    if show_progress:
                        _progress_line(paths[i])
        if show_progress:
            sys.stderr.write("\n")
        entries_list = [results_by_idx[i] for i in range(idx)]

    entries_list.sort(key=lambda x: str(x.get("path", "")))

    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries_list, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    elapsed = time.perf_counter() - t_start
    mode = "все файлы" if args.all_files else "только фото (PHOTO_INDEX_EXTENSIONS)"
    print(
        f"Записано: {out_path} ({len(entries_list)} записей, корень: {root}, "
        f"процессов: {workers}, режим: {mode})"
    )
    print(f"Время выполнения: {_format_duration(elapsed)}")

    if args.quiet:
        return

    counter: Counter[str] = Counter()
    for item in entries_list:
        p = item.get("path") or ""
        ext = Path(str(p)).suffix.lower() or "(без расширения)"
        counter[ext] += 1

    video_exts = {
        ".mp4",
        ".m4v",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".wmv",
        ".flv",
        ".3gp",
        ".mts",
        ".m2ts",
    }

    if not counter:
        return

    print(f"\nВсего файлов: {sum(counter.values())}, уникальных расширений: {len(counter)}\n")

    for ext, n in counter.most_common():
        flags: list[str] = []
        if ext in IMAGE_EXTENSIONS:
            flags.append("pHash: да (пробуем)")
        elif ext in video_exts:
            flags.append("pHash: нет (видео → только SHA256 в текущем сканере)")
        elif ext == "(без расширения)":
            flags.append("pHash: нет")
        else:
            flags.append("pHash: нет (не в IMAGE_EXTENSIONS → только SHA256)")

        print(f"  {ext!r:28} {n:6}  {'; '.join(flags)}")

    no_phash = [e for e in counter if e not in IMAGE_EXTENSIONS]
    if no_phash:
        print("\n--- Расширения без попытки pHash (см. common.media_constants.IMAGE_EXTENSIONS) ---")
        for e in sorted(no_phash):
            print(f"  {e} ({counter[e]} шт.)")


if __name__ == "__main__":
    main()
