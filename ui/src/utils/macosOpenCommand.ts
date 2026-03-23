/**
 * macOS Terminal: open file in default app.
 * Path in single quotes; each ' escaped as '\'' for sh/zsh.
 */
export function macOpenCommand(path: string | undefined | null): string {
  const p = typeof path === 'string' ? path.trim() : ''
  if (!p) return ''
  const escaped = p.replace(/'/g, `'\\''`)
  return `open '${escaped}'`
}
