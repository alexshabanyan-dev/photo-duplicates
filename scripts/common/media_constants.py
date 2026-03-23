"""
Общие константы для скриптов scripts/ без тяжёлых зависимостей (Pillow и т.д.).
"""

from __future__ import annotations

# Расширения, для которых индексация пробует посчитать pHash (остальные — только SHA256).
IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".heic",
        ".heif",
    }
)
