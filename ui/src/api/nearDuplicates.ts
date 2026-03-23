import { getApiBaseUrl, parseJsonResponse } from './client'
import type {
  DuplicatesApiErrorBody,
  FirstNotProcessedNearDuplicateResponse,
  ResolveNearDuplicateRequestBody,
  ResolveNearDuplicateResponseBody,
} from '../types/nearDuplicates'

export class NearDuplicatesRequestError extends Error {
  readonly status: number
  readonly body: DuplicatesApiErrorBody | null

  constructor(status: number, message: string, body: DuplicatesApiErrorBody | null) {
    super(message)
    this.name = 'NearDuplicatesRequestError'
    this.status = status
    this.body = body
  }
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

function asErrorBody(data: unknown): DuplicatesApiErrorBody | null {
  if (!isRecord(data)) return null
  if (typeof data.error !== 'string') return null
  const key = typeof data.key === 'string' ? data.key : 'near_duplicates'
  return { error: data.error, key }
}

/**
 * GET /api/duplicates/near_duplicates/first-not-processed
 */
export async function fetchFirstNotProcessedNearDuplicate(): Promise<FirstNotProcessedNearDuplicateResponse> {
  const url = `${getApiBaseUrl()}/duplicates/near_duplicates/first-not-processed`
  const res = await fetch(url)
  const data: unknown = await parseJsonResponse(res)

  if (!res.ok) {
    const errBody = asErrorBody(data)
    const message =
      errBody?.error ??
      (typeof data === 'string' ? data : `HTTP ${res.status}`)
    throw new NearDuplicatesRequestError(res.status, message, errBody)
  }

  return data as FirstNotProcessedNearDuplicateResponse
}

/**
 * POST /api/duplicates/near_duplicates/resolve-choice
 * keep_both — только processed; иначе chosen_side — to_delete: true в *.files-list.json.
 */
export async function submitResolveNearDuplicateChoice(
  body: ResolveNearDuplicateRequestBody,
): Promise<ResolveNearDuplicateResponseBody> {
  const url = `${getApiBaseUrl()}/duplicates/near_duplicates/resolve-choice`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data: unknown = await parseJsonResponse(res)

  if (!res.ok) {
    const errBody = asErrorBody(data)
    const message =
      errBody?.error ??
      (typeof data === 'string' ? data : `HTTP ${res.status}`)
    throw new NearDuplicatesRequestError(res.status, message, errBody)
  }

  return data as ResolveNearDuplicateResponseBody
}
