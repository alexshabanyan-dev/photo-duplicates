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

# Расширения для режима «только фото/картинки» в генераторах files-list (без видео и прочих файлов).
# Совпадает с типичным набором из define-extensions (jpg, jpeg, png, heic, cr2, …).
CANON_RAW_EXTENSIONS: frozenset[str] = frozenset({".cr2"})

PHOTO_INDEX_EXTENSIONS: frozenset[str] = IMAGE_EXTENSIONS | CANON_RAW_EXTENSIONS
