import { createHash } from "node:crypto";

/** Должен совпадать с scripts/analyze_duplicates/analyze_duplicates.py и scripts/common/file_index_core.py */
export function stableFileIdFromCanonicalPath(canonicalPath: string): string {
  return createHash("sha256").update(canonicalPath, "utf8").digest("hex");
}
