import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import type { DuplicatesAnalysisFile, ExactDuplicateGroup, FileSide } from "../types/analysis.js";
import { getDuplicatesAnalysisPath, getItemsToDeletePath } from "../paths.js";
import { invalidateAnalysisCache } from "./analysisService.js";
import { ResolveError } from "./resolveError.js";

type ItemToDeleteEntry = {
  decided_at: string;
  pair_uid: string;
  category: "near_duplicates" | "exact_duplicates";
  side_marked_for_delete?: "left" | "right";
  file: FileSide;
  is_deleted?: boolean;
  deleted_at?: string;
};

type ItemsToDeleteDoc = {
  items: ItemToDeleteEntry[];
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

async function loadItemsToDelete(): Promise<ItemsToDeleteDoc> {
  const p = getItemsToDeletePath();
  try {
    const buf = await readFile(p, "utf-8");
    const parsed: unknown = JSON.parse(buf);
    if (
      parsed &&
      typeof parsed === "object" &&
      "items" in parsed &&
      Array.isArray((parsed as ItemsToDeleteDoc).items)
    ) {
      return parsed as ItemsToDeleteDoc;
    }
    return { items: [] };
  } catch (e: unknown) {
    const code = (e as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return { items: [] };
    }
    throw e;
  }
}

function fileSnapshotExact(f: ExactDuplicateGroup["files"][number]): FileSide {
  const name = typeof f.filename === "string" ? f.filename : undefined;
  const ext = name ? path.extname(name).toLowerCase() : "";
  return {
    file_id: f.file_id,
    filename: name,
    extension: ext || undefined,
    path: f.path,
    sha256: undefined,
    phash: f.phash ?? undefined,
  };
}

function findExactGroupByUid(
  doc: DuplicatesAnalysisFile,
  groupUid: string
): ExactDuplicateGroup | undefined {
  const arr = doc.exact_duplicates;
  if (!Array.isArray(arr)) {
    return undefined;
  }
  return arr.find((g) => g.uid === groupUid);
}

const FILE_ID_RE = /^[a-f0-9]{64}$/;

/**
 * Принять решение по группе exact_duplicates:
 * — keep_all: только processed: true;
 * — иначе keep_file_id: этот файл оставляем, остальные из группы — в items_to_delete.json.
 */
export async function resolveExactDuplicateChoice(body: unknown): Promise<{
  ok: true;
  group_uid: string;
  resolution: "delete_others" | "keep_all";
  queued_file_ids?: string[];
}> {
  if (!body || typeof body !== "object") {
    throw new ResolveError(400, "Invalid JSON body");
  }
  const b = body as Record<string, unknown>;
  const group_uid = typeof b.group_uid === "string" ? b.group_uid.trim() : "";
  const key = b.key;
  const keep_all = b.keep_all === true;
  const keep_file_id_raw = typeof b.keep_file_id === "string" ? b.keep_file_id.trim().toLowerCase() : "";

  if (!group_uid) {
    throw new ResolveError(400, "group_uid is required");
  }
  if (key !== "exact_duplicates") {
    throw new ResolveError(400, 'key must be "exact_duplicates"');
  }

  const analysisPath = getDuplicatesAnalysisPath();
  const analysisBuf = await readFile(analysisPath, "utf-8");
  const doc = JSON.parse(analysisBuf) as DuplicatesAnalysisFile;

  const group = findExactGroupByUid(doc, group_uid);
  if (!group) {
    throw new ResolveError(404, "Exact duplicate group not found");
  }
  if (group.processed === true) {
    throw new ResolveError(409, "Group already processed");
  }

  const files = Array.isArray(group.files) ? group.files : [];
  if (files.length < 2) {
    throw new ResolveError(400, "Group must contain at least 2 files");
  }

  if (keep_all) {
    group.processed = true;
    await writeJsonAtomic(analysisPath, doc);
    invalidateAnalysisCache();
    return {
      ok: true,
      group_uid,
      resolution: "keep_all",
    };
  }

  if (!keep_file_id_raw || !FILE_ID_RE.test(keep_file_id_raw)) {
    throw new ResolveError(
      400,
      'keep_file_id must be a 64-char hex file_id when keep_all is false'
    );
  }

  const idsInGroup = new Set(
    files.map((f) => (typeof f.file_id === "string" ? f.file_id.trim().toLowerCase() : "")).filter(Boolean)
  );
  if (!idsInGroup.has(keep_file_id_raw)) {
    throw new ResolveError(400, "keep_file_id is not in this group");
  }

  const toQueue = files.filter((f) => {
    const id = typeof f.file_id === "string" ? f.file_id.trim().toLowerCase() : "";
    return id && id !== keep_file_id_raw;
  });

  if (toQueue.length === 0) {
    throw new ResolveError(400, "Nothing to delete");
  }

  const itemsDoc = await loadItemsToDelete();
  itemsDoc.items = itemsDoc.items.filter(
    (it) => !(it.pair_uid === group_uid && it.category === "exact_duplicates")
  );

  const queuedIds: string[] = [];
  for (const f of toQueue) {
    const snap = fileSnapshotExact(f);
    const fid = typeof snap.file_id === "string" ? snap.file_id.trim().toLowerCase() : "";
    if (fid) queuedIds.push(fid);
    itemsDoc.items.push({
      decided_at: new Date().toISOString(),
      pair_uid: group_uid,
      category: "exact_duplicates",
      file: snap,
    });
  }

  await writeJsonAtomic(getItemsToDeletePath(), itemsDoc);

  group.processed = true;
  await writeJsonAtomic(analysisPath, doc);
  invalidateAnalysisCache();

  return {
    ok: true,
    group_uid,
    resolution: "delete_others",
    queued_file_ids: queuedIds,
  };
}
