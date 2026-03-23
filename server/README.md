# photo-duplicates-server

Node.js + TypeScript + Express.

## Источники данных (строго)

| # | Назначение | Файл по умолчанию (от корня репо) | API |
|---|------------|-----------------------------------|-----|
| **1** | Полный список файлов (`path`, `file_id`, SHA256, pHash, …) | `scripts/files-list-generator/files-list.json` | `GET /api/media/:fileId` |
| **2** | Отчёт по дубликатам (`near_duplicates`, `exact_duplicates`, `processed`, …) | `scripts/analyze_duplicates/duplicates-list.json` | `GET/POST /api/duplicates/...` |

Других JSON для каталога или анализа **нет** (нет `files_index.json`, нет слияния нескольких списков).

**Пометка на удаление из UI:** при `POST .../resolve-choice` с удалением сервер ставит **`to_delete: true`** у соответствующих записей в **`*.files-list.json`** внутри каталога **`FILES_LIST_RESULT_DIR`** (по умолчанию `scripts/files-list-generator/result`). Для работы с копией списков (например `result_copy`) задайте `FILES_LIST_RESULT_DIR` на эту папку **и** используйте тот же каталог для `/api/media`, если индекс не в одном `FILES_LIST_JSON`. Файл `scripts/result/items_to_delete.json` сервер **больше не заполняет** (устаревший формат).

## Установка и запуск

```bash
cd server
npm install
npm run dev
```

Переменные окружения:

- `PORT` — порт (по умолчанию `3000`)
- `DUPLICATES_ANALYSIS_JSON` — путь к **(2)** duplicates-list (по умолчанию `../scripts/analyze_duplicates/duplicates-list.json`)
- `FILES_LIST_JSON` — путь к **(1)** files-list (по умолчанию `../scripts/files-list-generator/files-list.json`). Для совместимости читается и устаревший `FILES_INDEX_JSON`, если `FILES_LIST_JSON` не задан
- `FILES_LIST_RESULT_DIR` — каталог с фрагментами **`*.files-list.json`**: для `/api/media` (если не задан `FILES_LIST_JSON`) и для **проставления `to_delete`** при resolve-choice (по умолчанию `../scripts/files-list-generator/result`)
- `STORAGE_FILES_ROOT` — корень медиа (по умолчанию `../files` в корне репозитория); если задан — файлы вне него не отдаются; если не задан — допускаются абсолютные пути из индекса
- `ITEMS_TO_DELETE_JSON` — устарело; сервер при resolve-choice не пишет в `items_to_delete.json` (оставлено для совместимости со старыми скриптами, если путь нужен вручную)
- `CORS_ORIGIN` — заголовок CORS (по умолчанию `*`)

## API

### Первая **необработанная** пара `near_duplicates`

```http
GET /api/duplicates/near_duplicates/first-not-processed
```

`processed !== true` (если поля нет — считается необработанной).

**Успех (200):**

```json
{
  "key": "near_duplicates",
  "item": { ... },
  "unprocessed_pair_count": 42
}
```

`unprocessed_pair_count` — сколько пар ещё с `processed !== true` (включая текущую `item`). На фронте для оценки «файлов в очереди» обычно считают `2 × unprocessed_pair_count` (один файл может входить в несколько пар — это верхняя граница).

**404:** пустой массив или все пары уже с `processed: true`.

```bash
curl -s http://127.0.0.1:3000/api/duplicates/near_duplicates/first-not-processed | jq .
```

### Зафиксировать решение по паре

```http
POST /api/duplicates/near_duplicates/resolve-choice
Content-Type: application/json
```

**Удалить один файл** — тело:

```json
{
  "pair_uid": "<uid из item>",
  "key": "near_duplicates",
  "chosen_side": "left"
}
```

`chosen_side` — сторона к удалению: в соответствующей записи в `*.files-list.json` — `to_delete: true`. В `duplicates-list.json` у пары — `processed: true`.

**Оставить оба** — только отметить пару, без списка на удаление:

```json
{
  "pair_uid": "<uid>",
  "key": "near_duplicates",
  "keep_both": true
}
```

**Успех (200):** `{ "ok": true, "pair_uid": "...", "resolution": "delete_side"|"keep_both", "file_id": "..." }` (`file_id` только при удалении одной стороны).

**404:** пара не найдена. **409:** уже обработана.

```bash
# удалить выбранную сторону
curl -s -X POST http://127.0.0.1:3000/api/duplicates/near_duplicates/resolve-choice \
  -H 'Content-Type: application/json' \
  -d '{"pair_uid":"<uid>","key":"near_duplicates","chosen_side":"left"}' | jq .

# оставить оба
curl -s -X POST http://127.0.0.1:3000/api/duplicates/near_duplicates/resolve-choice \
  -H 'Content-Type: application/json' \
  -d '{"pair_uid":"<uid>","key":"near_duplicates","keep_both":true}' | jq .
```

### Первая **необработанная** группа `exact_duplicates`

```http
GET /api/duplicates/exact_duplicates/first-not-processed
```

У группы `processed !== true` (если поля нет — считается необработанной).

**Успех (200):**

```json
{
  "key": "exact_duplicates",
  "item": { "uid": "...", "sha256": "...", "files": [ ... ] },
  "unprocessed_group_count": 12
}
```

**404:** пустой массив `exact_duplicates` или все группы уже с `processed: true`.

```bash
curl -s http://127.0.0.1:3000/api/duplicates/exact_duplicates/first-not-processed | jq .
```

### Зафиксировать решение по группе точных дублей

```http
POST /api/duplicates/exact_duplicates/resolve-choice
Content-Type: application/json
```

**Оставить одну копию, остальные пометить `to_delete: true`** — тело:

```json
{
  "group_uid": "<uid группы из item>",
  "key": "exact_duplicates",
  "keep_file_id": "<64 hex file_id копии, которую оставляем>"
}
```

**Оставить все копии** — только отметить группу, без `to_delete`:

```json
{
  "group_uid": "<uid>",
  "key": "exact_duplicates",
  "keep_all": true
}
```

**Удалить все копии в группе** — у всех файлов группы в `*.files-list.json` — `to_delete: true`:

```json
{
  "group_uid": "<uid>",
  "key": "exact_duplicates",
  "delete_all": true
}
```

**Успех (200):** `{ "ok": true, "group_uid": "...", "resolution": "delete_others"|"keep_all"|"delete_all", "queued_file_ids": [...] }` (`queued_file_ids` — `file_id`, для которых выставлен `to_delete: true`, при любом режиме удаления).

```bash
curl -s -X POST http://127.0.0.1:3000/api/duplicates/exact_duplicates/resolve-choice \
  -H 'Content-Type: application/json' \
  -d '{"group_uid":"<uid>","key":"exact_duplicates","keep_all":true}' | jq .
```

### Файл по `file_id` (превью на фронте)

```http
GET /api/media/:fileId
```

`file_id` — 64 hex-символа (SHA256 от **абсолютного** пути в UTF-8). Берётся из `files-list.json` и дублируется в `duplicates-list.json` после `analyze_duplicates/analyze_duplicates.py`.

Отдаётся только путь, который лежит внутри `<репо>/files` (или `STORAGE_FILES_ROOT`).

```bash
# подставь file_id из JSON ответа пары дублей
curl -sOJ http://127.0.0.1:3000/api/media/<64_hex_символа>
```

На фронте: `<img :src="'http://127.0.0.1:3000/api/media/' + left.file_id" />` (или через прокси Vite).

## Сборка

```bash
npm run build
npm start
```
