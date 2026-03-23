export type DuplicateKey = "exact_duplicates" | "near_duplicates";

export interface FileSide {
  /** 64 hex: SHA256(UTF-8 абсолютный путь); как в files-list.json / duplicates-list.json */
  file_id?: string;
  filename?: string;
  /** Суффикс в нижнем регистре с точкой, например ".jpg"; пустая строка если нет расширения */
  extension?: string;
  path?: string;
  sha256?: string;
  phash?: string;
}

export interface NearDuplicatePair {
  /** Стабильный id пары (64 hex от двух file_id); раньше мог быть UUID v4 */
  uid?: string;
  distance: number;
  threshold_used: number;
  command: string | null;
  /** Пара просмотрена / решение принято */
  processed?: boolean;
  left: FileSide;
  right: FileSide;
}

export interface ExactDuplicateGroup {
  /** Стабильный id группы (64 hex от file_id участников) */
  uid?: string;
  sha256: string;
  count: number;
  command: string | null;
  /** Группа дублей обработана */
  processed?: boolean;
  files: Array<{
    file_id?: string;
    filename?: string;
    path?: string;
    phash?: string | null;
  }>;
}

export interface DuplicatesAnalysisFile {
  source_index?: string;
  generated_at?: string;
  index_entry_count?: number;
  skipped_missing_files?: number;
  /** Сколько путей в индексе переписано на канонический медиа-корень (в т.ч. старые …/storage|scripts/files → …/files) */
  index_paths_rewritten_to_storage?: number;
  file_count?: number;
  exact_duplicates_group_count?: number;
  near_duplicates_pair_count?: number;
  exact_duplicates: ExactDuplicateGroup[];
  near_duplicates: NearDuplicatePair[];
}
