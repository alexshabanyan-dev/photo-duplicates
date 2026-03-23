import { Router, type NextFunction, type Request, type Response } from "express";
import {
  countNotProcessedByKey,
  countNotProcessedExactGroups,
  getAnalysisDocument,
  getFirstNotProcessedByKey,
  getFirstNotProcessedExactGroup,
} from "../services/analysisService.js";
import { resolveExactDuplicateChoice } from "../services/resolveExactDuplicateService.js";
import { resolveNearDuplicateChoice } from "../services/resolveNearDuplicateService.js";
import { ResolveError } from "../services/resolveError.js";

export const duplicatesController = Router();

/**
 * GET /api/duplicates/near_duplicates/first-not-processed
 */
duplicatesController.get(
  "/near_duplicates/first-not-processed",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const doc = await getAnalysisDocument();
      const key = "near_duplicates" as const;
      const arr = doc[key];

      if (!Array.isArray(arr) || arr.length === 0) {
        res.status(404).json({
          error: "Array is empty or missing",
          key,
        });
        return;
      }

      const first = getFirstNotProcessedByKey(doc, key);
      if (first === undefined) {
        res.status(404).json({
          error: "All items are already processed",
          key,
        });
        return;
      }

      const unprocessed_pair_count = countNotProcessedByKey(doc, key);

      res.json({
        key,
        item: first,
        unprocessed_pair_count,
      });
    } catch (err) {
      next(err);
    }
  }
);

/**
 * POST /api/duplicates/near_duplicates/resolve-choice
 * Body: { pair_uid, key: "near_duplicates", chosen_side?: "left"|"right", keep_both?: boolean }
 * keep_both: true — только processed, без to_delete.
 * Иначе chosen_side — сторона к удалению: to_delete: true в *.files-list.json (FILES_LIST_RESULT_DIR).
 */
duplicatesController.post(
  "/near_duplicates/resolve-choice",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await resolveNearDuplicateChoice(req.body);
      res.json(result);
    } catch (err) {
      if (err instanceof ResolveError) {
        res.status(err.statusCode).json({
          error: err.message,
          key: "near_duplicates",
        });
        return;
      }
      next(err);
    }
  }
);

/**
 * GET /api/duplicates/exact_duplicates/first-not-processed
 */
duplicatesController.get(
  "/exact_duplicates/first-not-processed",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const doc = await getAnalysisDocument();
      const key = "exact_duplicates" as const;
      const arr = doc[key];
      if (!Array.isArray(arr) || arr.length === 0) {
        res.status(404).json({
          error: "Array is empty or missing",
          key,
        });
        return;
      }
      const first = getFirstNotProcessedExactGroup(doc);
      if (first === undefined) {
        res.status(404).json({
          error: "All groups are already processed",
          key,
        });
        return;
      }
      const unprocessed_group_count = countNotProcessedExactGroups(doc);
      res.json({
        key,
        item: first,
        unprocessed_group_count,
      });
    } catch (err) {
      next(err);
    }
  }
);

/**
 * POST /api/duplicates/exact_duplicates/resolve-choice
 * Body: { group_uid, key: "exact_duplicates", keep_all?: true, delete_all?: true, keep_file_id?: "64hex" }
 */
duplicatesController.post(
  "/exact_duplicates/resolve-choice",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await resolveExactDuplicateChoice(req.body);
      res.json(result);
    } catch (err) {
      if (err instanceof ResolveError) {
        res.status(err.statusCode).json({
          error: err.message,
          key: "exact_duplicates",
        });
        return;
      }
      next(err);
    }
  }
);
