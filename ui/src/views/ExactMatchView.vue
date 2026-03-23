<template>
  <AppPage title="Точное совпадение" variant="exact">
    <template v-if="payload" #headerExtra>
      <ExactGroupMeta
        :group-key="payload.key"
        :item="payload.item"
        :unprocessed-group-count="payload.unprocessed_group_count"
      />
    </template>

    <UncertainFetchState
      :loading="loading"
      :error-message="errorMessage"
      loading-hint="Загрузка первой необработанной группы точных дублей…"
      @retry="loadFirstNotProcessed"
    >
      <ExactGroupContent
        v-if="payload"
        :payload="payload"
        :previews-loading="previewsLoading"
        :preview-error="previewError"
        :preview-urls="previewUrls"
        :path-copied-file-id="pathCopiedFileId"
        @copy-path="onCopyPath"
        @resolved="loadFirstNotProcessed"
      />
    </UncertainFetchState>
  </AppPage>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AppPage from '../components/AppPage.vue'
import ExactGroupContent from '../components/exact/ExactGroupContent.vue'
import ExactGroupMeta from '../components/exact/ExactGroupMeta.vue'
import UncertainFetchState from '../components/uncertain/UncertainFetchState.vue'
import { fetchFirstNotProcessedExactGroup } from '../api/exactDuplicates'
import { NearDuplicatesRequestError } from '../api/nearDuplicates'
import { fetchMediaBlob } from '../api/media'
import { usePathCopy } from '../composables/usePathCopy'
import type {
  ExactDuplicateGroupItem,
  FirstNotProcessedExactGroupResponse,
} from '../types/exactDuplicates'

const { copyFilePath } = usePathCopy()
const pathCopiedFileId = ref<string | null>(null)

const loading = ref(true)
const errorMessage = ref<string | null>(null)
const payload = ref<FirstNotProcessedExactGroupResponse | null>(null)

const previewsLoading = ref(false)
const previewError = ref<string | null>(null)
const previewUrls = ref<Record<string, string>>({})

function onCopyPath(fileId: string | undefined, path: string | undefined): void {
  const id = fileId?.trim()
  pathCopiedFileId.value = id ?? null
  void copyFilePath('left', path)
}

function revokeAllPreviewUrls(): void {
  for (const url of Object.values(previewUrls.value)) {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  }
  previewUrls.value = {}
}

async function loadPreviewImages(item: ExactDuplicateGroupItem): Promise<void> {
  revokeAllPreviewUrls()
  previewError.value = null

  const ids = item.files
    .map((f) => f.file_id?.trim())
    .filter((id): id is string => !!id)

  if (ids.length === 0) {
    previewError.value =
      'Нет file_id у файлов группы. Пересобери индекс и отчёт: scan_files_to_json.py и analyze_duplicates.py.'
    return
  }

  previewsLoading.value = true
  try {
    const entries = await Promise.all(
      ids.map(async (id) => {
        const blob = await fetchMediaBlob(id)
        return [id, URL.createObjectURL(blob)] as const
      }),
    )
    const next: Record<string, string> = {}
    for (const [id, url] of entries) {
      next[id] = url
    }
    previewUrls.value = next
  } catch (e) {
    previewError.value =
      e instanceof Error ? e.message : 'Не удалось загрузить превью файлов'
  } finally {
    previewsLoading.value = false
  }
}

async function loadFirstNotProcessed(): Promise<void> {
  loading.value = true
  errorMessage.value = null
  payload.value = null
  revokeAllPreviewUrls()
  previewError.value = null

  try {
    const data = await fetchFirstNotProcessedExactGroup()
    payload.value = data
    await loadPreviewImages(data.item)
  } catch (e) {
    if (e instanceof NearDuplicatesRequestError) {
      errorMessage.value = e.message
    } else if (e instanceof Error) {
      errorMessage.value = e.message
    } else {
      errorMessage.value = 'Неизвестная ошибка'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadFirstNotProcessed()
})

onBeforeUnmount(() => {
  revokeAllPreviewUrls()
})
</script>
