import express from "express";
import { duplicatesController } from "./controllers/duplicatesController.js";
import { mediaController } from "./controllers/mediaController.js";
import {
  getDuplicatesAnalysisPath,
  getFilesListJsonPath,
  getFilesListResultDirPath,
} from "./paths.js";

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.use(express.json());

app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", process.env.CORS_ORIGIN ?? "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") {
    res.sendStatus(204);
    return;
  }
  next();
});

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.use("/api/duplicates", duplicatesController);
app.use("/api", mediaController);

app.use(
  (
    err: unknown,
    _req: express.Request,
    res: express.Response,
    _next: express.NextFunction
  ) => {
    console.error(err);
    const code =
      err &&
      typeof err === "object" &&
      "code" in err &&
      (err as { code?: string }).code === "ENOENT"
        ? 404
        : 500;
    const message = err instanceof Error ? err.message : "Internal server error";
    res.status(code).json({
      error: code === 404 ? "Required data file not found" : "Internal server error",
      details: process.env.NODE_ENV === "development" ? message : undefined,
    });
  }
);

app.listen(PORT, () => {
  const fromEnv = process.env.FILES_LIST_JSON || process.env.FILES_INDEX_JSON;
  console.log(`Server http://127.0.0.1:${PORT}`);
  if (fromEnv) {
    console.log(`  (1) files-list (single): ${getFilesListJsonPath()}`);
  } else {
    console.log(`  (1) files-list (merged dir): ${getFilesListResultDirPath()}/*.files-list.json`);
  }
  console.log(`  (2) duplicates: ${getDuplicatesAnalysisPath()}`);
  console.log(`  GET /api/duplicates/near_duplicates/first-not-processed`);
  console.log(`  POST /api/duplicates/near_duplicates/resolve-choice`);
  console.log(`  GET /api/duplicates/exact_duplicates/first-not-processed`);
  console.log(`  POST /api/duplicates/exact_duplicates/resolve-choice`);
  console.log(`  GET /api/media/:fileId   (64 hex, file_id из files-list)`);
});
