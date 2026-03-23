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
  /** Только отметить группу обработанной, без очереди на удаление */
  keep_all?: boolean
  /** Файл, который оставляем; остальные из группы — в items_to_delete */
  keep_file_id?: string
}

export type ResolveExactDuplicateResponseBody = {
  ok: true
  group_uid: string
  resolution: 'delete_others' | 'keep_all'
  queued_file_ids?: string[]
}
