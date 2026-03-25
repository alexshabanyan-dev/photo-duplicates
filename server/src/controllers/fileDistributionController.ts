import { Router, type NextFunction, type Request, type Response } from "express";
import {
  FileDistributionError,
  getFirstPendingFileDistributionEntry,
  markFileDistributionKept,
  markFileDistributionToDelete,
} from "../services/fileDistributionService.js";

export const fileDistributionController = Router();

/**
 * GET /api/file-distribution/first-pending
 */
fileDistributionController.get(
  "/first-pending",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await getFirstPendingFileDistributionEntry();
      res.json(result);
    } catch (err) {
      if (err instanceof FileDistributionError) {
        res.json({
          item: null,
          pending_count: 0,
          total_count: 0,
          processed_count: 0,
          marked_delete_count: 0,
          error: err.message,
        });
        return;
      }
      next(err);
    }
  },
);

/**
 * POST /api/file-distribution/mark-delete
 * Body: { "file_id": "64hex" }
 */
fileDistributionController.post(
  "/mark-delete",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = req.body as Record<string, unknown> | undefined;
      const file_id = typeof body?.file_id === "string" ? body.file_id : "";
      const result = await markFileDistributionToDelete(file_id);
      res.json(result);
    } catch (err) {
      if (err instanceof FileDistributionError) {
        res.status(err.statusCode).json({ error: err.message });
        return;
      }
      next(err);
    }
  },
);

/**
 * POST /api/file-distribution/mark-keep
 * Body: { "file_id": "64hex" } — проставляет distribution_kept: true, запись больше не в очереди.
 */
fileDistributionController.post(
  "/mark-keep",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = req.body as Record<string, unknown> | undefined;
      const file_id = typeof body?.file_id === "string" ? body.file_id : "";
      const result = await markFileDistributionKept(file_id);
      res.json(result);
    } catch (err) {
      if (err instanceof FileDistributionError) {
        res.status(err.statusCode).json({ error: err.message });
        return;
      }
      next(err);
    }
  },
);
