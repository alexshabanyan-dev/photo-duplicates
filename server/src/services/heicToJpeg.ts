import { execFile } from "child_process";
import { mkdtemp, readFile, rm } from "fs/promises";
import os from "os";
import path from "path";

function execFilePromise(
  file: string,
  args: readonly string[],
  options: { maxBuffer?: number },
): Promise<void> {
  return new Promise((resolve, reject) => {
    execFile(file, args, options, (err) => {
      if (err) reject(err);
      else resolve();
    });
  });
}

const HEIC_LIKE = new Set([".heic", ".heif", ".hif"]);

export function isHeicLikePath(filePath: string): boolean {
  const ext = path.extname(filePath).toLowerCase();
  return HEIC_LIKE.has(ext);
}

/**
 * macOS: sips → JPEG в память. Исходный файл не меняется.
 * На других ОС или при ошибке — null (отдаём оригинал как есть).
 */
export async function tryHeicToJpegBuffer(sourceAbs: string): Promise<Buffer | null> {
  if (process.platform !== "darwin") {
    return null;
  }
  if (!isHeicLikePath(sourceAbs)) {
    return null;
  }

  const tmpDir = await mkdtemp(path.join(os.tmpdir(), "pd-heic-"));
  const outJpg = path.join(tmpDir, "preview.jpg");
  try {
    await execFilePromise(
      "sips",
      ["-s", "format", "jpeg", sourceAbs, "--out", outJpg],
      { maxBuffer: 64 * 1024 * 1024 },
    );
    return await readFile(outJpg);
  } catch (e) {
    console.warn("[heicToJpeg] sips failed:", sourceAbs, e);
    return null;
  } finally {
    await rm(tmpDir, { recursive: true, force: true }).catch(() => {});
  }
}
