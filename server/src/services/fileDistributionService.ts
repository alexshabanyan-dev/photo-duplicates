import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { getFileDistributionJsonPath } from "../paths.js";
import { invalidateFilesIndexCache } from "./filesIndexService.js";

const FILE_ID_RE = /^[a-f0-9]{64}$/i;

export class FileDistributionError extends Error {
  readonly statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.name = "FileDistributionError";
    this.statusCode = statusCode;
  }
}

export type FileDistributionItem = Record<string, unknown>;

export type FirstPendingFileDistributionResponse = {
  item: FileDistributionItem | null;
  /** Записей ещё без решения (не deleted / to_delete / distribution_kept). */
  pending_count: number;
  /** Всего записей в JSON. */
  total_count: number;
  /** Уже не в очереди: удалён с диска в индексе, помечен to_delete или «оставить». */
  processed_count: number;
  /** С to_delete: true (помечено к удалению). */
  marked_delete_count: number;
};

async function writeJsonAtomic(filePath: string, data: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  await mkdir(dir, { recursive: true });
  const base = path.basename(filePath);
  const tmp = path.join(dir, `.${base}.${process.pid}.${Date.now()}.tmp`);
  const content = `${JSON.stringify(data, null, 2)}\n`;
  await writeFile(tmp, content, "utf-8");
  await rename(tmp, filePath);
}

type LoadedDoc = {
  root: unknown;
  entries: FileDistributionItem[];
};

async function loadDoc(filePath: string): Promise<LoadedDoc> {
  let buf: string;
  try {
    buf = await readFile(filePath, "utf-8");
  } catch (e) {
    const code = e && typeof e === "object" && "code" in e ? (e as NodeJS.ErrnoException).code : undefined;
    if (code === "ENOENT") {
      throw new FileDistributionError(404, `File distribution list not found: ${filePath}`);
    }
    throw e;
  }
  const raw: unknown = JSON.parse(buf);
  if (Array.isArray(raw)) {
    return { root: raw, entries: raw as FileDistributionItem[] };
  }
  if (raw && typeof raw === "object" && Array.isArray((raw as { files?: unknown }).files)) {
    return { root: raw, entries: (raw as { files: FileDistributionItem[] }).files };
  }
  throw new Error("Invalid file distribution JSON: expected array or { files: [] }");
}

function isPendingEntry(e: FileDistributionItem): boolean {
  if (e.deleted === true) return false;
  if (e.to_delete === true) return false;
  if (e.distribution_kept === true) return false;
  return true;
}

function normalizeFileId(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim().toLowerCase();
  if (!t || !FILE_ID_RE.test(t)) return null;
  return t;
}

function entryToClient(e: FileDistributionItem): FileDistributionItem {
  const out: FileDistributionItem = {};
  const keys = [
    "file_id",
    "filename",
    "extension",
    "path",
    "sha256",
    "phash",
    "hamming_threshold",
    "to_delete",
    "deleted",
    "distribution_kept",
    "phash_error",
  ] as const;
  for (const k of keys) {
    if (k in e) out[k] = e[k];
  }
  return out;
}

function computeDistributionStats(entries: FileDistributionItem[]): {
  pending_count: number;
  total_count: number;
  processed_count: number;
  marked_delete_count: number;
} {
  const total_count = entries.length;
  let pending_count = 0;
  let marked_delete_count = 0;
  for (const e of entries) {
    if (e.to_delete === true) marked_delete_count += 1;
    if (isPendingEntry(e)) pending_count += 1;
  }
  const processed_count = total_count - pending_count;
  return { total_count, pending_count, processed_count, marked_delete_count };
}

export async function getFirstPendingFileDistributionEntry(): Promise<FirstPendingFileDistributionResponse> {
  const filePath = getFileDistributionJsonPath();
  const { entries } = await loadDoc(filePath);
  const pending = entries.filter(isPendingEntry);
  const first = pending[0];
  const stats = computeDistributionStats(entries);
  return {
    item: first ? entryToClient(first) : null,
    pending_count: stats.pending_count,
    total_count: stats.total_count,
    processed_count: stats.processed_count,
    marked_delete_count: stats.marked_delete_count,
  };
}

function findEntryIndex(entries: FileDistributionItem[], fileIdNorm: string): number {
  return entries.findIndex((e) => normalizeFileId(e.file_id) === fileIdNorm);
}

export async function markFileDistributionToDelete(fileIdRaw: string): Promise<{ ok: true }> {
  const fileId = fileIdRaw.trim().toLowerCase();
  if (!FILE_ID_RE.test(fileId)) {
    throw new FileDistributionError(400, "Invalid file_id");
  }
  const filePath = getFileDistributionJsonPath();
  const { root, entries } = await loadDoc(filePath);
  const idx = findEntryIndex(entries, fileId);
  if (idx < 0) {
    throw new FileDistributionError(404, "file_id not found in file distribution list");
  }
  entries[idx].to_delete = true;
  await writeJsonAtomic(filePath, root);
  invalidateFilesIndexCache();
  return { ok: true };
}

export async function markFileDistributionKept(fileIdRaw: string): Promise<{ ok: true }> {
  const fileId = fileIdRaw.trim().toLowerCase();
  if (!FILE_ID_RE.test(fileId)) {
    throw new FileDistributionError(400, "Invalid file_id");
  }
  const filePath = getFileDistributionJsonPath();
  const { root, entries } = await loadDoc(filePath);
  const idx = findEntryIndex(entries, fileId);
  if (idx < 0) {
    throw new FileDistributionError(404, "file_id not found in file distribution list");
  }
  entries[idx].distribution_kept = true;
  await writeJsonAtomic(filePath, root);
  invalidateFilesIndexCache();
  return { ok: true };
}
