/** Сторона пары near-duplicate (левый / правый файл). */
export type NearDuplicateSide = {
  /** 64 hex — для GET /api/media/:fileId */
  file_id?: string
  filename?: string
  /** Суффикс с точкой, нижний регистр, например ".jpg" */
  extension?: string
  path?: string
  sha256?: string
  phash?: string
}

/** Элемент массива near_duplicates из анализа. */
export type NearDuplicatePairItem = {
  uid?: string
  distance: number
  threshold_used: number
  command: string | null
  processed?: boolean
  left: NearDuplicateSide
  right: NearDuplicateSide
}

export type NearDuplicatesKey = 'near_duplicates'

/** Успешный ответ GET .../near_duplicates/first-not-processed */
export type FirstNotProcessedNearDuplicateResponse = {
  key: NearDuplicatesKey
  item: NearDuplicatePairItem
  /** Сколько пар near_duplicates ещё с processed !== true (включая текущую) */
  unprocessed_pair_count: number
}

/** Тело ошибки 404 от API дубликатов. */
export type DuplicatesApiErrorBody = {
  error: string
  key: string
}

/** Тело POST .../near_duplicates/resolve-choice */
export type ResolveNearDuplicateRequestBody = {
  pair_uid: string
  key: NearDuplicatesKey
  /** true — только отметить пару обработанной, без to_delete в files-list */
  keep_both?: boolean
  /** Нужен, если keep_both не true: сторона файла к удалению (to_delete: true в *.files-list.json) */
  chosen_side?: 'left' | 'right'
}

export type ResolveNearDuplicateResponseBody = {
  ok: true
  pair_uid: string
  resolution?: 'delete_side' | 'keep_both'
  file_id?: string
}
