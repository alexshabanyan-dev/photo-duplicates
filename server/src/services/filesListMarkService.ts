import { mkdir, readdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { getFilesListResultDirPath } from "../paths.js";

const FILE_ID_RE = /^[a-f0-9]{64}$/i;

async function writeJsonAtomic(filePath: string, data: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  await mkdir(dir, { recursive: true });
  const base = path.basename(filePath);
  const tmp = path.join(dir, `.${base}.${process.pid}.${Date.now()}.tmp`);
  const content = `${JSON.stringify(data, null, 2)}\n`;
  await writeFile(tmp, content, "utf-8");
  await rename(tmp, filePath);
}

async function collectFilesListJsonRecursive(dir: string): Promise<string[]> {
  const out: string[] = [];
  let list;
  try {
    list = await readdir(dir, { withFileTypes: true });
  } catch (e: unknown) {
    const code = (e as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return [];
    }
    throw e;
  }
  for (const ent of list) {
    const abs = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      out.push(...(await collectFilesListJsonRecursive(abs)));
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

function normalizeFileId(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const t = raw.trim().toLowerCase();
  if (!t || !FILE_ID_RE.test(t)) return null;
  return t;
}

/**
 * Проставляет `to_delete: true` у записей с указанными `file_id` во всех
 * `*.files-list.json` в каталоге `FILES_LIST_RESULT_DIR` (по умолчанию
 * `scripts/files-list-generator/result`). Формат файла — как у сканера:
 * либо массив объектов, либо `{ scan_root?, files: [...] }`.
 */
export async function markFileIdsToDeleteInResultLists(fileIds: Iterable<string>): Promise<{
  touched_json_files: string[];
  marked_entries: number;
  found_ids: Set<string>;
}> {
  const want = new Set<string>();
  for (const id of fileIds) {
    const n = normalizeFileId(id);
    if (n) want.add(n);
  }

  const foundIds = new Set<string>();
  const touched: string[] = [];
  let markedEntries = 0;

  if (want.size === 0) {
    return { touched_json_files: touched, marked_entries: markedEntries, found_ids: foundIds };
  }

  const rootDir = getFilesListResultDirPath();
  const jsonFiles = await collectFilesListJsonRecursive(rootDir);

  for (const filePath of jsonFiles) {
    let raw: unknown;
    try {
      raw = JSON.parse(await readFile(filePath, "utf-8"));
    } catch {
      console.warn(`[filesListMarkService] skip invalid JSON: ${filePath}`);
      continue;
    }

    let modified = false;

    const applyToEntries = (entries: Array<Record<string, unknown>>) => {
      for (const entry of entries) {
        const fid = normalizeFileId(entry.file_id);
        if (!fid || !want.has(fid)) continue;
        foundIds.add(fid);
        if (entry.to_delete === true) continue;
        entry.to_delete = true;
        modified = true;
        markedEntries += 1;
      }
    };

    if (Array.isArray(raw)) {
      applyToEntries(raw as Array<Record<string, unknown>>);
      if (modified) {
        await writeJsonAtomic(filePath, raw);
        touched.push(filePath);
      }
      continue;
    }

    if (raw && typeof raw === "object" && Array.isArray((raw as { files?: unknown }).files)) {
      const doc = raw as { files: Array<Record<string, unknown>> };
      applyToEntries(doc.files);
      if (modified) {
        await writeJsonAtomic(filePath, raw);
        touched.push(filePath);
      }
      continue;
    }
  }

  const missing = [...want].filter((id) => !foundIds.has(id));
  if (missing.length > 0) {
    console.warn(
      `[filesListMarkService] file_id not found in any *.files-list.json under ${rootDir}: ${missing.join(", ")}`
    );
  }

  return {
    touched_json_files: touched,
    marked_entries: markedEntries,
    found_ids: foundIds,
  };
}
