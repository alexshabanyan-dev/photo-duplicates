import { getApiBaseUrl, parseJsonResponse } from './client'
import { NearDuplicatesRequestError } from './nearDuplicates'
import type { DuplicatesApiErrorBody } from '../types/nearDuplicates'
import type {
  FirstNotProcessedExactGroupResponse,
  ResolveExactDuplicateRequestBody,
  ResolveExactDuplicateResponseBody,
} from '../types/exactDuplicates'

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

function asErrorBody(data: unknown): DuplicatesApiErrorBody | null {
  if (!isRecord(data)) return null
  if (typeof data.error !== 'string') return null
  const key = typeof data.key === 'string' ? data.key : 'exact_duplicates'
  return { error: data.error, key }
}

/**
 * GET /api/duplicates/exact_duplicates/first-not-processed
 */
export async function fetchFirstNotProcessedExactGroup(): Promise<FirstNotProcessedExactGroupResponse> {
  const url = `${getApiBaseUrl()}/duplicates/exact_duplicates/first-not-processed`
  const res = await fetch(url)
  const data: unknown = await parseJsonResponse(res)

  if (!res.ok) {
    const errBody = asErrorBody(data)
    const message =
      errBody?.error ?? (typeof data === 'string' ? data : `HTTP ${res.status}`)
    throw new NearDuplicatesRequestError(res.status, message, errBody)
  }

  return data as FirstNotProcessedExactGroupResponse
}

/**
 * POST /api/duplicates/exact_duplicates/resolve-choice
 */
export async function submitResolveExactDuplicateChoice(
  body: ResolveExactDuplicateRequestBody,
): Promise<ResolveExactDuplicateResponseBody> {
  const url = `${getApiBaseUrl()}/duplicates/exact_duplicates/resolve-choice`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data: unknown = await parseJsonResponse(res)

  if (!res.ok) {
    const errBody = asErrorBody(data)
    const message =
      errBody?.error ?? (typeof data === 'string' ? data : `HTTP ${res.status}`)
    throw new NearDuplicatesRequestError(res.status, message, errBody)
  }

  return data as ResolveExactDuplicateResponseBody
}
