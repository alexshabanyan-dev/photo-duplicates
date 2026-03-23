/** Элемент массива files внутри группы exact_duplicates. */
export type ExactDuplicateFileEntry = {
  file_id?: string
  filename?: string
  path?: string
  phash?: string | null
}

export type ExactDuplicateGroupItem = {
  uid?: string
  sha256: string
  count: number
  command: string | null
  processed?: boolean
  files: ExactDuplicateFileEntry[]
}

export type ExactDuplicatesKey = 'exact_duplicates'

/** Успешный ответ GET .../exact_duplicates/first-not-processed */
export type FirstNotProcessedExactGroupResponse = {
  key: ExactDuplicatesKey
  item: ExactDuplicateGroupItem
  unprocessed_group_count: number
}

export type ResolveExactDuplicateRequestBody = {
  group_uid: string
  key: ExactDuplicatesKey
  /** Только отметить группу обработанной, без to_delete */
  keep_all?: boolean
  /** Удалить все копии в группе (to_delete: true для всех в *.files-list.json) */
  delete_all?: boolean
  /** Файл, который оставляем; остальные — to_delete: true в *.files-list.json */
  keep_file_id?: string
}

export type ResolveExactDuplicateResponseBody = {
  ok: true
  group_uid: string
  resolution: 'delete_others' | 'keep_all' | 'delete_all'
  queued_file_ids?: string[]
}
