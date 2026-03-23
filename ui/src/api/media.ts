import { getApiBaseUrl } from './client'

/** GET /api/media/:fileId */
export function getMediaUrl(fileId: string): string {
  const id = fileId.trim()
  return `${getApiBaseUrl()}/media/${encodeURIComponent(id)}`
}

export async function fetchMediaBlob(fileId: string): Promise<Blob> {
  const url = getMediaUrl(fileId)
  const res = await fetch(url)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    let detail = `HTTP ${res.status}`
    try {
      const j = JSON.parse(text) as { error?: string }
      if (typeof j.error === 'string') detail = j.error
    } catch {
      if (text) detail = text.slice(0, 120)
    }
    throw new Error(detail)
  }
  return res.blob()
}
