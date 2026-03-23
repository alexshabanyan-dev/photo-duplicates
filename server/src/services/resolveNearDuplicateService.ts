import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import type { DuplicatesAnalysisFile, FileSide, NearDuplicatePair } from "../types/analysis.js";
import { getDuplicatesAnalysisPath } from "../paths.js";
import { invalidateAnalysisCache } from "./analysisService.js";
import { markFileIdsToDeleteInResultLists } from "./filesListMarkService.js";
import { ResolveError } from "./resolveError.js";

export type ChosenSide = "left" | "right";

export type ResolveNearDuplicateBody = {
  pair_uid: string;
  key: "near_duplicates";
  /** true — только processed: true, без to_delete в files-list */
  keep_both?: boolean;
  chosen_side?: ChosenSide;
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

function isChosenSide(v: unknown): v is ChosenSide {
  return v === "left" || v === "right";
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
 * — иначе: у файла со стороны chosen_side в *.files-list.json — to_delete: true + processed: true.
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

  const fileToMark = fileSnapshot(pair[chosen_side]);
  const fid =
    typeof fileToMark.file_id === "string" && fileToMark.file_id.trim()
      ? fileToMark.file_id.trim().toLowerCase()
      : "";
  if (!fid) {
    throw new ResolveError(400, "Chosen side has no valid file_id");
  }

  await markFileIdsToDeleteInResultLists([fid]);

  pair.processed = true;
  await writeJsonAtomic(analysisPath, doc);

  invalidateAnalysisCache();

  return {
    ok: true,
    pair_uid,
    resolution: "delete_side",
    file_id: fileToMark.file_id,
  };
}
