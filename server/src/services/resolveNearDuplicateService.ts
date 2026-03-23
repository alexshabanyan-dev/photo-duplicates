import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import type { DuplicatesAnalysisFile, FileSide, NearDuplicatePair } from "../types/analysis.js";
import { getDuplicatesAnalysisPath, getItemsToDeletePath } from "../paths.js";
import { invalidateAnalysisCache } from "./analysisService.js";
import { ResolveError } from "./resolveError.js";

export type ChosenSide = "left" | "right";

export type ResolveNearDuplicateBody = {
  pair_uid: string;
  key: "near_duplicates";
  /** true — только processed: true, без записи в items_to_delete.json */
  keep_both?: boolean;
  chosen_side?: ChosenSide;
};

type ItemToDeleteEntry = {
  decided_at: string;
  pair_uid: string;
  category: "near_duplicates";
  side_marked_for_delete: ChosenSide;
  file: FileSide;
  /** после фактического удаления скриптом scripts/delete_marked_files.py */
  is_deleted?: boolean;
  deleted_at?: string;
};

type ItemsToDeleteDoc = {
  items: ItemToDeleteEntry[];
};

function isChosenSide(v: unknown): v is ChosenSide {
  return v === "left" || v === "right";
}

async function writeJsonAtomic(filePath: string, data: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  await mkdir(dir, { recursive: true });
  const base = path.basename(filePath);
  const tmp = path.join(dir, `.${base}.${process.pid}.${Date.now()}.tmp`);
  const content = `${JSON.stringify(data, null, 2)}\n`;
  await writeFile(tmp, content, "utf-8");
  await rename(tmp, filePath);
}

function fileSnapshot(side: FileSide): FileSide {
  return {
    file_id: side.file_id,
    filename: side.filename,
    extension: side.extension,
    path: side.path,
    sha256: side.sha256,
    phash: side.phash,
  };
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

function findNearPairByUid(
  doc: DuplicatesAnalysisFile,
  pairUid: string
): NearDuplicatePair | undefined {
  const arr = doc.near_duplicates;
  if (!Array.isArray(arr)) {
    return undefined;
  }
  return arr.find((p) => p.uid === pairUid);
}

/**
 * Принять решение по паре near_duplicates:
 * — keep_both: только processed: true в duplicates-list.json;
 * — иначе: в items_to_delete.json добавить файл со стороны chosen_side + processed: true.
 *
 * Порядок для delete: сначала items_to_delete (дедуп по pair_uid), затем analysis.
 */
export async function resolveNearDuplicateChoice(body: unknown): Promise<{
  ok: true;
  pair_uid: string;
  resolution: "delete_side" | "keep_both";
  file_id?: string;
}> {
  if (!body || typeof body !== "object") {
    throw new ResolveError(400, "Invalid JSON body");
  }
  const b = body as Record<string, unknown>;
  const pair_uid = typeof b.pair_uid === "string" ? b.pair_uid.trim() : "";
  const key = b.key;
  const keep_both = b.keep_both === true;
  const chosen_side = b.chosen_side;

  if (!pair_uid) {
    throw new ResolveError(400, "pair_uid is required");
  }
  if (key !== "near_duplicates") {
    throw new ResolveError(400, 'key must be "near_duplicates"');
  }

  const analysisPath = getDuplicatesAnalysisPath();
  const analysisBuf = await readFile(analysisPath, "utf-8");
  const doc = JSON.parse(analysisBuf) as DuplicatesAnalysisFile;

  const pair = findNearPairByUid(doc, pair_uid);
  if (!pair) {
    throw new ResolveError(404, "Pair not found");
  }
  if (pair.processed === true) {
    throw new ResolveError(409, "Pair already processed");
  }

  if (keep_both) {
    pair.processed = true;
    await writeJsonAtomic(analysisPath, doc);
    invalidateAnalysisCache();
    return {
      ok: true,
      pair_uid,
      resolution: "keep_both",
    };
  }

  if (!isChosenSide(chosen_side)) {
    throw new ResolveError(400, 'chosen_side must be "left" or "right" when keep_both is false');
  }

  const fileToQueue = fileSnapshot(pair[chosen_side]);

  const itemsDoc = await loadItemsToDelete();
  const alreadyQueued = itemsDoc.items.some((it) => it.pair_uid === pair_uid);
  if (!alreadyQueued) {
    itemsDoc.items.push({
      decided_at: new Date().toISOString(),
      pair_uid,
      category: "near_duplicates",
      side_marked_for_delete: chosen_side,
      file: fileToQueue,
    });
    await writeJsonAtomic(getItemsToDeletePath(), itemsDoc);
  }

  pair.processed = true;
  await writeJsonAtomic(analysisPath, doc);

  invalidateAnalysisCache();

  return {
    ok: true,
    pair_uid,
    resolution: "delete_side",
    file_id: fileToQueue.file_id,
  };
}
