import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import {
  REPO_ROOT,
  getFileDistributionJsonPath,
  getFilesListJsonPath,
  getFilesListResultDirPath,
  getStorageFilesRoot,
} from "../paths.js";
import { stableFileIdFromCanonicalPath } from "./stableFileId.js";

function isSafeInsideRoot(candidate: string, root: string): boolean {
  const c = path.resolve(candidate);
  const r = path.resolve(root);
  return c === r || c.startsWith(r + path.sep);
}

function parseEntries(data: unknown): {
  entries: Array<Record<string, unknown>>;
  scanRoot: string | null;
} {
  if (Array.isArray(data)) {
    return { entries: data as Array<Record<string, unknown>>, scanRoot: null };
  }
  if (data && typeof data === "object" && Array.isArray((data as { files?: unknown }).files)) {
    const scanRoot =
      typeof (data as { scan_root?: unknown }).scan_root === "string"
        ? (data as { scan_root: string }).scan_root
        : null;
    return {
      entries: (data as { files: Array<Record<string, unknown>> }).files,
      scanRoot,
    };
  }
  return { entries: [], scanRoot: null };
}

function resolveEntryPath(entryPath: string, scanRoot: string | null): string | null {
  const trimmed = entryPath.trim();
  if (!trimmed) return null;
  if (path.isAbsolute(trimmed)) {
    return path.resolve(trimmed);
  }
  if (scanRoot) {
    return path.resolve(scanRoot, trimmed);
  }
  return path.resolve(REPO_ROOT, trimmed);
}

/** Старые индексы: …/storage/files/… или …/scripts/files/… → актуальный корень медиа …/files/… */
function remapLegacyStorageFilesPath(resolvedAbs: string): string {
  const mediaRoot = path.resolve(getStorageFilesRoot());
  const legacyRoots = [
    path.resolve(REPO_ROOT, "storage", "files"),
    path.resolve(REPO_ROOT, "scripts", "files"),
  ];
  const abs = path.resolve(resolvedAbs);
  for (const legacyRoot of legacyRoots) {
    if (abs === legacyRoot || abs.startsWith(legacyRoot + path.sep)) {
      const rel = path.relative(legacyRoot, abs);
      return path.join(mediaRoot, rel);
    }
  }
  return abs;
}

const FILE_ID_RE = /^[a-f0-9]{64}$/;

type ParsedIndex = { entries: Array<Record<string, unknown>>; scanRoot: string | null };
type CacheState = { signature: string; idToPath: Map<string, string> };

let cache: CacheState | null = null;

/** Сброс кэша карты file_id → path (после правок JSON со списком файлов). */
export function invalidateFilesIndexCache(): void {
  cache = null;
}

async function appendFileDistributionIndexIfPresent(
  signatureParts: string[],
  indexes: ParsedIndex[],
): Promise<void> {
  const fdPath = getFileDistributionJsonPath();
  try {
    const st = await stat(fdPath);
    const buf = await readFile(fdPath);
    const raw: unknown = JSON.parse(buf.toString("utf-8"));
    signatureParts.push(`fd:${fdPath}:${st.mtimeMs}`);
    indexes.push(parseSingleIndex(raw));
  } catch (e) {
    const code = e && typeof e === "object" && "code" in e ? (e as NodeJS.ErrnoException).code : undefined;
    if (code === "ENOENT") {
      return;
    }
    console.warn(`[filesIndexService] skip FILE_DISTRIBUTION_JSON ${fdPath}:`, e);
  }
}

async function collectIndexFilesRecursive(dir: string): Promise<string[]> {
  const out: string[] = [];
  const list = await readdir(dir, { withFileTypes: true });
  for (const ent of list) {
    const abs = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      out.push(...(await collectIndexFilesRecursive(abs)));
      continue;
    }
    if (!ent.isFile()) continue;
    if (ent.name.endsWith(".files-list.json")) {
      out.push(abs);
    }
  }
  out.sort((a, b) => a.localeCompare(b));
  return out;
}

function parseSingleIndex(raw: unknown): ParsedIndex {
  return parseEntries(raw);
}

async function buildIndexesInput(): Promise<{
  signature: string;
  indexes: ParsedIndex[];
}> {
  const fromEnv = process.env.FILES_LIST_JSON || process.env.FILES_INDEX_JSON;
  if (fromEnv) {
    const filePath = getFilesListJsonPath();
    const st = await stat(filePath);
    const buf = await readFile(filePath);
    const raw: unknown = JSON.parse(buf.toString("utf-8"));
    const sigParts = [`single:${filePath}:${st.mtimeMs}`];
    const indexes = [parseSingleIndex(raw)];
    await appendFileDistributionIndexIfPresent(sigParts, indexes);
    return {
      signature: sigParts.join("|"),
      indexes,
    };
  }

  const resultDir = getFilesListResultDirPath();
  let files: string[] = [];
  try {
    files = await collectIndexFilesRecursive(resultDir);
  } catch (e) {
    const code = e && typeof e === "object" && "code" in e ? (e as NodeJS.ErrnoException).code : undefined;
    if (code === "ENOENT") {
      const sigParts = [`dir:${resultDir}:missing`];
      const indexes: ParsedIndex[] = [];
      await appendFileDistributionIndexIfPresent(sigParts, indexes);
      return { signature: sigParts.join("|"), indexes };
    }
    throw e;
  }
  if (files.length === 0) {
    const sigParts = [`dir:${resultDir}:empty`];
    const indexes: ParsedIndex[] = [];
    await appendFileDistributionIndexIfPresent(sigParts, indexes);
    return { signature: sigParts.join("|"), indexes };
  }

  const sigParts: string[] = [`dir:${resultDir}`];
  const indexes: ParsedIndex[] = [];
  for (const fp of files) {
    const st = await stat(fp);
    sigParts.push(`${fp}:${st.mtimeMs}`);
    const buf = await readFile(fp);
    const raw: unknown = JSON.parse(buf.toString("utf-8"));
    indexes.push(parseSingleIndex(raw));
  }
  await appendFileDistributionIndexIfPresent(sigParts, indexes);
  return { signature: sigParts.join("|"), indexes };
}

export async function getIdToPathMap(): Promise<Map<string, string>> {
  const input = await buildIndexesInput();
  if (cache && cache.signature === input.signature) {
    return cache.idToPath;
  }
  const idToPath = new Map<string, string>();
  const storageRoot = path.resolve(getStorageFilesRoot());
  const strictStorageRoot = Boolean(process.env.STORAGE_FILES_ROOT);

  for (const idx of input.indexes) {
    const { entries, scanRoot } = idx;
    for (const e of entries) {
      const p = e.path;
      if (typeof p !== "string" || !p.trim()) continue;
      const rawAbs = resolveEntryPath(p, scanRoot);
      if (!rawAbs) continue;
      const abs = remapLegacyStorageFilesPath(rawAbs);
      const existingId = typeof e.file_id === "string" ? e.file_id : undefined;
      const id =
        existingId && FILE_ID_RE.test(existingId.toLowerCase())
          ? existingId.toLowerCase()
          : stableFileIdFromCanonicalPath(abs);
      if (strictStorageRoot && !isSafeInsideRoot(abs, storageRoot)) continue;
      idToPath.set(id, abs);
    }
  }

  cache = { signature: input.signature, idToPath };
  return idToPath;
}

export async function resolveAbsolutePathForFileId(fileId: string): Promise<string | null> {
  const normalized = fileId.trim().toLowerCase();
  if (!FILE_ID_RE.test(normalized)) return null;
  const map = await getIdToPathMap();
  const p = map.get(normalized);
  if (!p) return null;
  const storageRoot = path.resolve(getStorageFilesRoot());
  const strictStorageRoot = Boolean(process.env.STORAGE_FILES_ROOT);
  if (strictStorageRoot && !isSafeInsideRoot(p, storageRoot)) return null;
  return p;
}
