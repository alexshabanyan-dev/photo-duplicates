/** Расширения, для которых в карточках показываем <video>, а не <img>. */
const VIDEO_EXTENSIONS = new Set([
  '.mp4',
  '.webm',
  '.mov',
  '.m4v',
  '.mkv',
  '.avi',
  '.mpeg',
  '.mpg',
  '.ogv',
  '.wmv',
  '.3gp',
])

function extensionFromFilename(filename: string): string {
  const i = filename.lastIndexOf('.')
  if (i < 0) return ''
  return filename.slice(i).toLowerCase()
}

/** По имени файла (или пути) — подходит ли для превью через <video>. */
export function isVideoFilename(filename: string | undefined | null): boolean {
  if (!filename || typeof filename !== 'string') return false
  const base = filename.split(/[/\\]/).pop() ?? filename
  const ext = extensionFromFilename(base)
  return VIDEO_EXTENSIONS.has(ext)
}
