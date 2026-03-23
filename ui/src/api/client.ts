/**
 * Базовый URL API без завершающего слэша.
 * В dev по умолчанию `/api` (см. proxy в vite.config.ts).
 * Для продакшена или прямого обхода прокси: VITE_API_BASE_URL=http://127.0.0.1:3000/api
 */
export function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL
  if (typeof fromEnv === 'string' && fromEnv.trim() !== '') {
    return fromEnv.replace(/\/$/, '')
  }
  return '/api'
}

export async function parseJsonResponse<T>(res: Response): Promise<T> {
  const text = await res.text()
  if (!text) {
    throw new Error('Пустой ответ сервера')
  }
  try {
    return JSON.parse(text) as T
  } catch {
    throw new Error('Ответ сервера не JSON')
  }
}
