#!/usr/bin/env python3
"""
Строит индекс в том же формате, что и scan_files_to_json → result/files_index.json:
корень JSON — **массив** объектов с полями file_id, filename, extension, path, sha256, phash,
hamming_threshold и при необходимости phash_error.

По умолчанию пишет **files-list.json** в этой папке (`scripts/files-list-generator/`).

В stderr: сначала «Сбор списка файлов…», затем «Найдено: …», далее одна обновляемая строка «Обработано: N/M»
(отключить: `--quiet` или `--no-progress`).

Нужны Pillow и ImageHash (как у scan_files_to_json). Если есть `scripts/.venv` с зависимостями,
скрипт при запуске «чужим» python3 сам перезапустится через интерпретатор из `scripts/.venv`.

Запуск из папки `scripts/` (достаточно системного python3, если venv уже настроен):

  python3 files-list-generator/files-list-generator.py
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _SCRIPTS_DIR.parent
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
    """
    True только если процесс реально использует site-packages из scripts/.venv.

    Нельзя сравнивать sys.executable с .venv/bin/python3 через samefile: на macOS/Homebrew
    bin из venv часто симлинк на тот же бинарник, что и `python3` в PATH — тогда samefile
    совпадает, но sys.prefix у «системного» запуска не указывает на .venv и пакеты не видны.
    """
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
        v1 = (
            f"    {venv_py} {script}\n"
            if venv_py is not None
            else "    (нет scripts/.venv — создай по scripts/README.md, затем pip install -r requirements.txt)\n"
        )
        in_venv = _running_in_scripts_venv()
        extra = ""
        if in_venv:
            extra = (
                "  (Сейчас уже интерпретатор из .venv, но пакетов нет — поставь в этот venv:)\n"
                "    ./.venv/bin/pip install -r requirements.txt\n\n"
            )
        print(
            "Нет Pillow / ImageHash в этом интерпретаторе.\n"
            + extra
            + "  Вариант 1: явно через venv:\n"
            + v1
            + "  Вариант 2: активируй venv, затем снова запусти скрипт:\n"
            "    cd scripts && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate\n"
            "    python3 files-list-generator/files-list-generator.py\n"
            "  Вариант 3: зависимости в текущий Python:\n"
            "    cd scripts && pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)


_ensure_pillow_imagehash()

from common.file_index_core import build_file_index_entries  # noqa: E402
from common.media_constants import IMAGE_EXTENSIONS  # noqa: E402


def main() -> None:
    default_root = Path("/Volumes/SAE 1/Фото")
    default_out = _SCRIPT_DIR / "files-list.json"

    parser = argparse.ArgumentParser(
        description=(
            "Сгенерировать files-list.json в формате files_index.json "
            "(массив записей с SHA256 и pHash)."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root,
        help=f"Корень обхода (по умолчанию: {default_root})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=default_out,
        help=f"Куда записать JSON (по умолчанию: {default_out})",
    )
    parser.add_argument(
        "--hamming-threshold",
        type=int,
        default=8,
        help="Порог Хэмминга для поля hamming_threshold в каждой записи (как у scan_files_to_json)",
    )
    parser.add_argument(
        "--relative-paths",
        action="store_true",
        help="В path писать путь относительно --root (по умолчанию — абсолютный, как в твоём files_index.json)",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Учитывать скрытые файлы/папки",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Не печатать сводку по расширениям в консоль",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Не выводить строку «Обработано: N/M» (и не мешать quiet)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Папка не найдена: {root}", file=sys.stderr)
        sys.exit(1)

    show_progress = not args.quiet and not args.no_progress

    def _progress(current: int, total: int) -> None:
        # ljust — затереть хвост от более длинной предыдущей строки
        line = f"Обработано: {current}/{total}"
        sys.stderr.write("\r" + line.ljust(72))
        sys.stderr.flush()

    entries = build_file_index_entries(
        root,
        hamming_threshold=args.hamming_threshold,
        relative_paths=args.relative_paths,
        include_hidden=args.include_hidden,
        progress_callback=_progress if show_progress else None,
    )
    if show_progress:
        sys.stderr.write("\n")

    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Записано: {out_path} ({len(entries)} записей, корень: {root})")

    if args.quiet:
        return

    counter: Counter[str] = Counter()
    for item in entries:
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
