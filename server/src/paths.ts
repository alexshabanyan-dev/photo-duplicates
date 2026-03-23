import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Корень репозитория photo-duplicates (на уровень выше папки server) */
export const REPO_ROOT = path.resolve(__dirname, "..", "..");

/**
 * Канонические JSON для бизнес-данных (ровно два файла читаются как «истина»):
 *
 * 1. Список всех файлов (SHA256, pHash, path, file_id) — один файл, без слияний и без files_index.
 * 2. Анализ дублей (exact / near, processed, …) — один файл.
 *
 * Отдельно: `items_to_delete.json` — только очередь решений UI (запись при resolve-choice), не каталог и не отчёт дублей.
 */

/** Путь к списку файлов относительно корня репозитория */
const FILES_LIST_SEGMENTS = ["scripts", "files-list-generator", "files-list.json"] as const;

/** Путь к отчёту дублей относительно корня репозитория */
const DUPLICATES_LIST_SEGMENTS = ["scripts", "analyze_duplicates", "duplicates-list.json"] as const;

function defaultFilesListJson(): string {
  return path.join(REPO_ROOT, ...FILES_LIST_SEGMENTS);
}

function defaultDuplicatesListJson(): string {
  return path.join(REPO_ROOT, ...DUPLICATES_LIST_SEGMENTS);
}

/**
 * (1) Полный список файлов — единственный источник для `/api/media/:fileId` (карта file_id → path).
 * Переопределение: `FILES_LIST_JSON` (предпочтительно) или устаревший `FILES_INDEX_JSON`.
 */
export function getFilesListJsonPath(): string {
  const fromEnv = process.env.FILES_LIST_JSON || process.env.FILES_INDEX_JSON;
  if (fromEnv) return path.resolve(fromEnv);
  return defaultFilesListJson();
}

/**
 * @deprecated Используй `getFilesListJsonPath()`. Оставлено для совместимости с прежним именем.
 */
export function getFilesIndexPath(): string {
  return getFilesListJsonPath();
}

/** (2) Анализ дублей — единственный источник для API `/api/duplicates/...`. */
export function getDuplicatesAnalysisPath(): string {
  const fromEnv = process.env.DUPLICATES_ANALYSIS_JSON;
  if (fromEnv) return path.resolve(fromEnv);
  return defaultDuplicatesListJson();
}

/** Медиа для превью: <repo>/files (в корне проекта) */
export function getStorageFilesRoot(): string {
  const fromEnv = process.env.STORAGE_FILES_ROOT;
  if (fromEnv) return path.resolve(fromEnv);
  return path.join(REPO_ROOT, "files");
}

/** Очередь на удаление после решений в UI (сервер дописывает при delete_side). Не смешивать с (1) и (2). */
export function getItemsToDeletePath(): string {
  const fromEnv = process.env.ITEMS_TO_DELETE_JSON;
  if (fromEnv) return path.resolve(fromEnv);
  return path.join(REPO_ROOT, "scripts", "result", "items_to_delete.json");
}
