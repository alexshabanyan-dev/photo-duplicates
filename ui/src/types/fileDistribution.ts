export type FileDistributionItem = {
  file_id?: string
  filename?: string
  extension?: string
  path?: string
  sha256?: string
  phash?: string | null
  hamming_threshold?: number
  to_delete?: boolean
  deleted?: boolean
  distribution_kept?: boolean
  phash_error?: string
}

export type FirstPendingFileDistributionResponse = {
  item: FileDistributionItem | null
  pending_count: number
  total_count: number
  processed_count: number
  marked_delete_count: number
  error?: string
}
