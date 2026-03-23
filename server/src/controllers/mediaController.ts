import { Router, type NextFunction, type Request, type Response } from "express";
import { resolveAbsolutePathForFileId } from "../services/filesIndexService.js";

export const mediaController = Router();

/**
 * GET /api/media/:fileId
 * Отдаёт бинарный файл из <repo>/files по file_id из files-list.json (см. FILES_LIST_JSON).
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

      res.sendFile(abs, (err) => {
        if (err) next(err);
      });
    } catch (err) {
      next(err);
    }
  }
);
