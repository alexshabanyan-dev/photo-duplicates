/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Полный базовый URL API, например http://127.0.0.1:3000/api. Если не задан — в dev используется /api и proxy Vite. */
  readonly VITE_API_BASE_URL?: string
}
