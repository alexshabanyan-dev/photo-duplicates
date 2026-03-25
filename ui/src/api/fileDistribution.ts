import { getApiBaseUrl, parseJsonResponse } from './client'
import type { FirstPendingFileDistributionResponse } from '../types/fileDistribution'

export class FileDistributionRequestError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, message: string, body: unknown) {
    super(message)
    this.name = 'FileDistributionRequestError'
    this.status = status
    this.body = body
  }
}

/** GET /api/file-distribution/first-pending */
export async function fetchFirstPendingFileDistribution(): Promise<FirstPendingFileDistributionResponse> {
  const url = `${getApiBaseUrl()}/file-distribution/first-pending`
  const res = await fetch(url)
  const data: unknown = await parseJsonResponse(res)
  if (!res.ok) {
    const err = data as { error?: string }
    throw new FileDistributionRequestError(
      res.status,
      typeof err.error === 'string' ? err.error : `HTTP ${res.status}`,
      data,
    )
  }
  return data as FirstPendingFileDistributionResponse
}

export async function postMarkFileDistributionDelete(fileId: string): Promise<void> {
  const url = `${getApiBaseUrl()}/file-distribution/mark-delete`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId }),
  })
  const data: unknown = await parseJsonResponse(res)
  if (!res.ok) {
    const err = data as { error?: string }
    throw new FileDistributionRequestError(
      res.status,
      typeof err.error === 'string' ? err.error : `HTTP ${res.status}`,
      data,
    )
  }
}

export async function postMarkFileDistributionKeep(fileId: string): Promise<void> {
  const url = `${getApiBaseUrl()}/file-distribution/mark-keep`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId }),
  })
  const data: unknown = await parseJsonResponse(res)
  if (!res.ok) {
    const err = data as { error?: string }
    throw new FileDistributionRequestError(
      res.status,
      typeof err.error === 'string' ? err.error : `HTTP ${res.status}`,
      data,
    )
  }
}
