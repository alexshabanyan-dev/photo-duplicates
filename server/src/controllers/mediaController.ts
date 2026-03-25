import { Router, type NextFunction, type Request, type Response } from "express";
import { resolveAbsolutePathForFileId } from "../services/filesIndexService.js";
import { isHeicLikePath, tryHeicToJpegBuffer } from "../services/heicToJpeg.js";

export const mediaController = Router();

/**
 * GET /api/media/:fileId
 * Отдаёт файл по file_id из индекса. HEIC/HEIF на macOS перекодируются в JPEG на лету (sips),
 * исходник на диске не меняется.
 */
mediaController.get(
  "/media/:fileId",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const fileId = req.params.fileId ?? "";
      const abs = await resolveAbsolutePathForFileId(fileId);
      if (!abs) {
        res.status(404).json({ error: "Unknown or invalid file_id" });
        return;
      }

      if (isHeicLikePath(abs)) {
        const jpeg = await tryHeicToJpegBuffer(abs);
        if (jpeg !== null && jpeg.length > 0) {
          res.setHeader("Content-Type", "image/jpeg");
          res.setHeader("X-Original-Format", "heic");
          res.send(jpeg);
          return;
        }
      }

      res.sendFile(abs, (err) => {
        if (err) next(err);
      });
    } catch (err) {
      next(err);
    }
  }
);
