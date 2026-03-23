import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { REPO_ROOT, getFilesListJsonPath, getStorageFilesRoot } from "../paths.js";
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

let cache: { mtimeMs: number; idToPath: Map<string, string> } | null = null;

export async function getIdToPathMap(): Promise<Map<string, string>> {
  const filePath = getFilesListJsonPath();
  let st;
  try {
    st = await stat(filePath);
  } catch (e) {
    const code = e && typeof e === "object" && "code" in e ? (e as NodeJS.ErrnoException).code : undefined;
    if (code === "ENOENT") {
      return new Map();
    }
    throw e;
  }
  if (cache && cache.mtimeMs === st.mtimeMs) {
    return cache.idToPath;
  }

  const buf = await readFile(filePath);
  const raw: unknown = JSON.parse(buf.toString("utf-8"));
  const { entries, scanRoot } = parseEntries(raw);
  const idToPath = new Map<string, string>();
  const storageRoot = path.resolve(getStorageFilesRoot());

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
    if (!isSafeInsideRoot(abs, storageRoot)) continue;
    idToPath.set(id, abs);
  }

  cache = { mtimeMs: st.mtimeMs, idToPath };
  return idToPath;
}

export async function resolveAbsolutePathForFileId(fileId: string): Promise<string | null> {
  const normalized = fileId.trim().toLowerCase();
  if (!FILE_ID_RE.test(normalized)) return null;
  const map = await getIdToPathMap();
  const p = map.get(normalized);
  if (!p) return null;
  const storageRoot = path.resolve(getStorageFilesRoot());
  if (!isSafeInsideRoot(p, storageRoot)) return null;
  return p;
}
