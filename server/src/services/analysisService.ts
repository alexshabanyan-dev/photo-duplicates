import { readFile, stat } from "node:fs/promises";
import type { DuplicatesAnalysisFile, ExactDuplicateGroup, NearDuplicatePair } from "../types/analysis.js";
import { getDuplicatesAnalysisPath } from "../paths.js";

let cache: { mtimeMs: number; data: DuplicatesAnalysisFile } | null = null;

export async function getAnalysisDocument(): Promise<DuplicatesAnalysisFile> {
  const filePath = getDuplicatesAnalysisPath();
  const st = await stat(filePath);
  if (cache && cache.mtimeMs === st.mtimeMs) {
    return cache.data;
  }
  const buf = await readFile(filePath);
  const data = JSON.parse(buf.toString("utf-8")) as DuplicatesAnalysisFile;
  cache = { mtimeMs: st.mtimeMs, data };
  return data;
}

/** Сброс кэша после записи duplicates-list.json на диск. */
export function invalidateAnalysisCache(): void {
  cache = null;
}

/** Первая пара near_duplicates с processed !== true (поле отсутствует — необработана). */
export function getFirstNotProcessedByKey(
  doc: DuplicatesAnalysisFile,
  key: "near_duplicates"
): NearDuplicatePair | undefined {
  const arr = doc[key];
  if (!Array.isArray(arr)) {
    return undefined;
  }
  return arr.find((item) => item.processed !== true);
}

/** Сколько пар в массиве с processed !== true (нет поля — считается необработанной). */
export function countNotProcessedByKey(
  doc: DuplicatesAnalysisFile,
  key: "near_duplicates"
): number {
  const arr = doc[key];
  if (!Array.isArray(arr)) {
    return 0;
  }
  return arr.filter((item) => item.processed !== true).length;
}

/** Первая группа exact_duplicates с processed !== true. */
export function getFirstNotProcessedExactGroup(
  doc: DuplicatesAnalysisFile
): ExactDuplicateGroup | undefined {
  const arr = doc.exact_duplicates;
  if (!Array.isArray(arr)) {
    return undefined;
  }
  return arr.find((g) => g.processed !== true);
}

/** Сколько групп exact_duplicates ещё с processed !== true. */
export function countNotProcessedExactGroups(doc: DuplicatesAnalysisFile): number {
  const arr = doc.exact_duplicates;
  if (!Array.isArray(arr)) {
    return 0;
  }
  return arr.filter((g) => g.processed !== true).length;
}
