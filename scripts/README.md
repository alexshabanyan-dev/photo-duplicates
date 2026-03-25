# photo-duplicates (папка `scripts/`)

Скрипты для индексации файлов (SHA256 + pHash), анализа дублей и просмотра расширений в папке с медиа.

**Рабочая директория** — эта папка (`scripts/`): здесь лежат скрипты и **`result/`** с отчётами. **Медиа** — в **`<корень_репо>/files/`** (папка `files` в корне проекта, рядом с `scripts/`).

Если ты перенёс проект или переименовал папку, пересобери индекс и отчёт, иначе в `result/*.json` останутся устаревшие абсолютные пути и команды `open` будут неверными:

```bash
cd /path/to/photo-duplicates/scripts
source .venv/bin/activate
python3 scan_files_to_json.py
python3 analyze_duplicates/analyze_duplicates.py
```

---

## Подготовка (один раз)

На macOS с Python от Homebrew пакеты в системный интерпретатор ставить нельзя (PEP 668) — нужен **виртуальный `.venv` внутри `scripts/`**.

```bash
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts

python3 -m venv .venv
./.venv/bin/python3 -m pip install --upgrade pip
./.venv/bin/python3 -m pip install -r requirements.txt
```

**Надёжный запуск** (не зависит от `activate` и от того, есть ли команда `python`):

```bash
./.venv/bin/python3 scan_files_to_json.py
./.venv/bin/python3 analyze_duplicates/analyze_duplicates.py
```

После `source .venv/bin/activate` проверь: **`which python3`** → `.../scripts/.venv/bin/python3`.

**Если показывает Homebrew:** часто `scripts/.venv` **скопировали** с уровня `photo-duplicates/.venv` — тогда внутри `bin/activate` и в `pyvenv.cfg` остаётся чужой путь, и `PATH` настраивается не на `scripts`. Исправление — **удалить и создать venv заново только из `scripts`:**

```bash
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts
rm -rf .venv
python3 -m venv .venv
./.venv/bin/python3 -m pip install --upgrade pip
./.venv/bin/python3 -m pip install -r requirements.txt
source .venv/bin/activate
which python3   # должно быть .../scripts/.venv/bin/python3
```

Пока venv чинишь, можно всегда вызывать **`./.venv/bin/python3`** без `activate`.

Дальше в той же сессии (или снова `source .venv/bin/activate`):

---

## 1. Индекс файлов — `scan_files_to_json.py`

Рекурсивно обходит папку, для каждого файла считает **SHA256**; для изображений из списка расширений — **pHash**. В каждую запись: **`file_id`** (SHA256 от абсолютного пути), **`extension`** (суффикс с точкой в нижнем регистре, например `.jpg`, или пустая строка). Сохраняет JSON в **`result/`**.

**Базовый запуск** (корень сканирования по умолчанию — `<корень_репо>/files/`):

```bash
source .venv/bin/activate
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts

python3 scan_files_to_json.py
```

**Свой каталог и имя отчёта** (путь к файлу всегда внутри `result/`):

```bash
python3 scan_files_to_json.py --root /путь/к/медиа -o files_index.json
python3 scan_files_to_json.py -o backup/index_2025.json
```

**Полезные опции:**

```bash
# порог Хэмминга для pHash (пишется в каждую запись)
python3 scan_files_to_json.py --hamming-threshold 10

# относительные пути в JSON (относительно --root)
python3 scan_files_to_json.py --relative-paths

# обёртка: объект с метаданными и массивом files
python3 scan_files_to_json.py --with-meta

# включить скрытые файлы и папки (.DS_Store и т.п.)
python3 scan_files_to_json.py --include-hidden
```

**Выход по умолчанию:** `result/files_index.json`

**Дубликат отчёта в другом месте:** `files-list-generator/files-list-generator.py` строит **тот же массив записей** (`file_id`, `path`, `sha256`, `phash`, …), что и `scan_files_to_json`, и сохраняет в **`files-list-generator/files-list.json`** (логика общая — `common/file_index_core.py`). Нужны те же зависимости (venv).

```bash
python3 files-list-generator/files-list-generator.py
python3 files-list-generator/files-list-generator.py --relative-paths
```

---

## 2. Анализ дублей — `analyze_duplicates/analyze_duplicates.py`

Скрипт лежит в **`analyze_duplicates/`**. **Вход по умолчанию:** `files-list-generator/files-list.json` (формат записей как у `result/files_index.json`). **Выход по умолчанию:** `analyze_duplicates/duplicates-list.json`.

Строит отчёт: точные дубли по **SHA256**, похожие по **pHash** (пары с расстоянием Хэмминга ≤ порога; пары с одинаковым SHA256 в «похожие» не дублируются).

```bash
source .venv/bin/activate
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts

python3 analyze_duplicates/analyze_duplicates.py
```

**Явно указать вход/выход** (`-o` — только внутри папки `analyze_duplicates/`):

```bash
python3 analyze_duplicates/analyze_duplicates.py --input files-list-generator/files-list.json
python3 analyze_duplicates/analyze_duplicates.py -i result/files_index.json -o duplicates-list.json
python3 analyze_duplicates/analyze_duplicates.py -i files-list-generator/files-list.json -o reports/dupes.json
```

**Порог по умолчанию**, если в записи нет `hamming_threshold`:

```bash
python3 analyze_duplicates/analyze_duplicates.py --hamming-threshold 10
```

**Старые пути в индексе:** медиа ищутся под `<репо>/files`. Если в индексе остались абсолютные пути к `…/storage/files/…` или `…/scripts/files/…`, хвост переносится в `…/files/…`; в отчёте смотри `index_paths_rewritten_to_storage` (число переписанных путей).

**Удалённые файлы:** отчёт строится по выбранному JSON со списком файлов. Если файл уже удалили, а список не пересобирали, такие строки отбрасываются (поля `index_entry_count`, `skipped_missing_files`, `file_count`). Чтобы учитывать все строки без проверки диска:

```bash
python3 analyze_duplicates/analyze_duplicates.py --include-missing
```

После массовых удалений лучше снова: `files-list-generator` и/или `scan_files_to_json.py` → `analyze_duplicates/analyze_duplicates.py`.

**Выход по умолчанию:** `analyze_duplicates/duplicates-list.json`

В отчёте: у каждой пары/группы **`uid`** — **стабильный** 64-символьный id (SHA256 от `file_id` участников; при той же паре файлов не меняется между пересборками). У файлов в индексе и в паре — **`file_id`** (SHA256 от пути). **`processed`: `false`** — отметь **`true`**, когда разобрал. Решения «что удалить» храни отдельно (sidecar/API), не в этом JSON.

**Массово пометить near-пары с удалённой стороной как processed** — `analyze_duplicates/mark_near_processed_if_deleted.py`:

```bash
cd scripts/analyze_duplicates
python3 mark_near_processed_if_deleted.py          # dry-run
python3 mark_near_processed_if_deleted.py --apply  # записать в duplicates-list.json
```

**near_duplicates: пары «Ева (чат)» × «Iphone Диана»** — у пути с Дианой в result ставится `to_delete: true`, у пары `processed: true` — `analyze_duplicates/resolve_near_eva_chat_vs_iphone_diana.py`:

```bash
cd scripts/analyze_duplicates
python3 resolve_near_eva_chat_vs_iphone_diana.py
python3 resolve_near_eva_chat_vs_iphone_diana.py --apply
```

**near_duplicates: оба пути содержат подстроку** (по умолчанию `INDIA2026`) — только `processed: true`, `*.files-list.json` не меняются — `analyze_duplicates/mark_near_processed_both_paths_needle.py`:

```bash
cd scripts/analyze_duplicates
python3 mark_near_processed_both_paths_needle.py
python3 mark_near_processed_both_paths_needle.py --apply
```

**Массово: exact_duplicates, оставить копию из папки по подстроке пути** — `analyze_duplicates/resolve_exact_keep_one_by_path_needle.py`:

- Находит группы, где в `path` есть подстрока (по умолчанию **`Армения 2013`**; сравнение после Unicode NFC). Своя подстрока: `--needle '…'`.
- В каждой такой группе оставляет **первую** по списку копию с этой подстрокой, остальным `file_id` ставит **`to_delete: true`** в `files-list-generator/result/**/*.files-list.json`.
- Группе выставляет **`processed: true`** в `duplicates-list.json`.

```bash
cd scripts/analyze_duplicates
python3 resolve_exact_keep_one_by_path_needle.py             # только план (без записи)
python3 resolve_exact_keep_one_by_path_needle.py --apply       # записать
# другая подстрока пути, например Тайланд:
python3 resolve_exact_keep_one_by_path_needle.py --needle 'Тайланд + Малайзия' --apply
# другой каталог списков:
python3 resolve_exact_keep_one_by_path_needle.py --result-dir ../files-list-generator/result_copy --apply
```

---

## 3. Список расширений — `list_extensions.py`

Показывает, какие расширения есть в папке и для каких из них скрипт индексации пробует **pHash** (список расширений берётся из **`common/media_constants.py`**).

**Зависимости не нужны** (только стандартная библиотека Python) — venv для этого скрипта не обязателен.

```bash
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts
python3 list_extensions.py
```

Из корня репозитория:

```bash
python3 scripts/list_extensions.py --root ../files
```

**Другая папка:**

```bash
python3 list_extensions.py --root /Users/alexander/Desktop/MyProjects/photo-duplicates/files
python3 list_extensions.py --root ../files --include-hidden
```

Вывод только в консоль, файлы не создаёт.

---

## Типичный пайплайн

```bash
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts
source .venv/bin/activate

python3 scan_files_to_json.py
python3 analyze_duplicates/analyze_duplicates.py
```

При необходимости сначала посмотреть состав файлов:

```bash
python3 list_extensions.py --root ../files
```

---

## 4. Удалить файл-дубль — `delete_file.py`

По умолчанию файл уходит **в Корзину** (через Finder), не в `rm`. Только **macOS**.

1. Открой **`delete_file.py`** и задай **`FILE_TO_DELETE`**: абсолютный путь или `_REPO_ROOT / "files" / ...` (корень репозитория).
2. Запусти:

```bash
source .venv/bin/activate
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts

python3 delete_file.py --dry-run
python3 delete_file.py --yes
```

**Безвозвратно** (не Корзина):

```bash
python3 delete_file.py --permanent --yes
```

---

## 5. Удаление после решений в UI

**Текущий поток:** сервер при выборе «удалить» в интерфейсе ставит **`to_delete: true`** в записях внутри **`*.files-list.json`** (каталог как у сканера, по умолчанию `files-list-generator/result`; см. `FILES_LIST_RESULT_DIR` на сервере). Физическое удаление с диска — скриптом **`delete-files/delete-marked-files-from-result.py`** (читает те же JSON).

### Устаревшее: очередь `items_to_delete.json` — `delete_marked_files.py`

Читает **`result/items_to_delete.json`** (сервер **больше не дописывает** этот файл при resolve-choice). Для каждой строки **без** `is_deleted: true`:

1. Удаляет **`file.path`** с диска (если файла уже нет — считается успехом).
2. Ставит **`is_deleted: true`** и **`deleted_at`** (ISO UTC), сохраняет JSON **атомарно** после каждой успешной операции.

Безопасность: удаляются только пути, которые после `resolve()` лежат внутри **`<репо>/files/`** (см. `--files-root`).

```bash
cd /Users/alexander/Desktop/MyProjects/photo-duplicates/scripts

# сначала посмотреть, что будет сделано (JSON не меняется)
./.venv/bin/python3 delete_marked_files.py --dry-run

# выполнить
./.venv/bin/python3 delete_marked_files.py
```

Свой файл очереди:

```bash
./.venv/bin/python3 delete_marked_files.py -i result/items_to_delete.json
```

---

## Зависимости

См. **`requirements.txt`** (Pillow, ImageHash). Видео (`.mov`, `.mp4` и т.д.) в текущей версии индексируются **только по SHA256**; pHash для них не считается.
