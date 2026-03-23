import { onBeforeUnmount, ref } from 'vue'

export type PathCopySide = 'left' | 'right'

export function usePathCopy() {
  const pathCopiedSide = ref<PathCopySide | null>(null)
  let pathCopyResetTimer: ReturnType<typeof setTimeout> | null = null

  async function copyFilePath(side: PathCopySide, path: string | undefined): Promise<void> {
    const p = path?.trim()
    if (!p) return

    const write = async (): Promise<void> => {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(p)
        return
      }
      const ta = document.createElement('textarea')
      ta.value = p
      ta.setAttribute('readonly', '')
      ta.className = 'clipboard-fallback-textarea'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }

    try {
      await write()
      if (pathCopyResetTimer !== null) {
        clearTimeout(pathCopyResetTimer)
      }
      pathCopiedSide.value = side
      pathCopyResetTimer = setTimeout(() => {
        pathCopiedSide.value = null
        pathCopyResetTimer = null
      }, 2000)
    } catch {
      // без уведомления
    }
  }

  onBeforeUnmount(() => {
    if (pathCopyResetTimer !== null) {
      clearTimeout(pathCopyResetTimer)
    }
  })

  return { pathCopiedSide, copyFilePath }
}
