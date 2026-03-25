<template>
  <AppPage title="Распределение файлов" variant="distribution">
    <template #headerExtra>
      <n-text v-if="!loading && !listError" depth="3" class="file-distribution__meta">
        Всего файлов:
        <n-text strong>{{ totalCount }}</n-text>
        <span class="file-distribution__meta-sep">·</span>
        Обработано:
        <n-text strong>{{ processedCount }}</n-text>
        <span class="file-distribution__meta-sep">·</span>
        Удалено:
        <n-text strong>{{ markedDeleteCount }}</n-text>
        <span class="file-distribution__meta-sep">·</span>
        Осталось:
        <n-text strong>{{ remainingCount }}</n-text>
      </n-text>
    </template>

    <n-spin :show="loading" size="large">
      <n-space vertical :size="20">
        <n-alert v-if="listError" type="error" :show-icon="true" :title="listError">
          Проверь путь к JSON на сервере (FILE_DISTRIBUTION_JSON) и что файл создан сканером.
        </n-alert>

        <n-empty
          v-else-if="!item && !listError"
          description="Нет файлов в очереди (все помечены, удалены или список пуст)."
        />

        <template v-else-if="item">
          <div class="file-distribution__top-row">
            <n-space vertical :size="10" class="file-distribution__info">
              <n-text strong class="file-distribution__filename">{{ item.filename ?? '—' }}</n-text>
              <n-space align="flex-start" :size="8" wrap class="file-distribution__path-row">
                <n-text depth="3" class="file-distribution__path">{{ item.path ?? '—' }}</n-text>
                <n-button
                  size="tiny"
                  type="primary"
                  secondary
                  :disabled="!item.path"
                  @click="onCopyPath"
                >
                  {{ clipKind === 'path' ? 'Скопировано' : 'Копировать путь' }}
                </n-button>
                <n-button
                  size="tiny"
                  type="primary"
                  secondary
                  :disabled="!item.path"
                  title="В буфер: open «путь» для вставки в терминал (macOS)"
                  @click="onCopyOpenCommand"
                >
                  {{ clipKind === 'open' ? 'Скопировано' : 'Копировать команду' }}
                </n-button>
              </n-space>
              <n-code v-if="item.file_id">{{ item.file_id }}</n-code>
            </n-space>

            <n-space
              :size="8"
              wrap
              justify="flex-end"
              class="file-distribution__actions"
            >
              <n-button type="error" :disabled="acting || !item.file_id" :loading="acting" @click="onDelete">
                Удалить
              </n-button>
              <n-button type="default" :disabled="acting || !item.file_id" :loading="acting" @click="onKeep">
                Оставить
              </n-button>
            </n-space>
          </div>

          <n-alert v-if="previewError" type="warning" :show-icon="true" class="file-distribution__preview-alert">
            {{ previewError }}
          </n-alert>

          <div v-else class="file-distribution__preview" @click.stop>
            <n-spin v-if="previewsLoading" size="medium" />
            <n-image
              v-else-if="imageUrl"
              :src="imageUrl"
              object-fit="contain"
              :alt="item.filename ?? 'Файл'"
            />
          </div>
        </template>
      </n-space>
    </n-spin>
  </AppPage>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { onBeforeUnmount, ref } from 'vue'
import {
  fetchFirstPendingFileDistribution,
  FileDistributionRequestError,
  postMarkFileDistributionDelete,
  postMarkFileDistributionKeep,
} from '../api/fileDistribution'
import { fetchMediaBlob } from '../api/media'
import AppPage from '../components/AppPage.vue'
import type { FileDistributionItem } from '../types/fileDistribution'

const message = useMessage()

const loading = ref(true)
const listError = ref<string | null>(null)
const item = ref<FileDistributionItem | null>(null)
const totalCount = ref(0)
const processedCount = ref(0)
const markedDeleteCount = ref(0)
/** Ещё в очереди на решение (то же, что pending_count с API). */
const remainingCount = ref(0)

const previewsLoading = ref(false)
const previewError = ref<string | null>(null)
const imageUrl = ref<string | null>(null)

const acting = ref(false)
/** Какая кнопка копирования недавно сработала (для подписи «Скопировано»). */
const clipKind = ref<'path' | 'open' | null>(null)
let clipResetTimer: ReturnType<typeof setTimeout> | null = null

function macOpenCommand(filePath: string): string {
  const escaped = filePath.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
  return `open "${escaped}"`
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const ta = document.createElement('textarea')
  ta.value = text
  ta.setAttribute('readonly', '')
  ta.className = 'clipboard-fallback-textarea'
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
}

function flashClipKind(kind: 'path' | 'open'): void {
  if (clipResetTimer !== null) clearTimeout(clipResetTimer)
  clipKind.value = kind
  clipResetTimer = setTimeout(() => {
    clipKind.value = null
    clipResetTimer = null
  }, 2000)
}

function revokeImageUrl(): void {
  if (imageUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(imageUrl.value)
  }
  imageUrl.value = null
}

async function loadPreview(it: FileDistributionItem): Promise<void> {
  revokeImageUrl()
  previewError.value = null
  const fid = it.file_id?.trim()
  if (!fid) {
    previewError.value = 'Нет file_id — пересобери список файлов.'
    return
  }
  previewsLoading.value = true
  try {
    const blob = await fetchMediaBlob(fid)
    imageUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    previewError.value = e instanceof Error ? e.message : 'Не удалось загрузить изображение'
  } finally {
    previewsLoading.value = false
  }
}

async function loadFirst(): Promise<void> {
  loading.value = true
  listError.value = null
  revokeImageUrl()
  item.value = null
  totalCount.value = 0
  processedCount.value = 0
  markedDeleteCount.value = 0
  remainingCount.value = 0
  try {
    const data = await fetchFirstPendingFileDistribution()
    if (typeof data.error === 'string' && data.error) {
      listError.value = data.error
      totalCount.value = 0
      processedCount.value = 0
      markedDeleteCount.value = 0
      remainingCount.value = 0
      return
    }
    totalCount.value = data.total_count ?? 0
    processedCount.value = data.processed_count ?? 0
    markedDeleteCount.value = data.marked_delete_count ?? 0
    remainingCount.value = data.pending_count ?? 0
    item.value = data.item
    if (data.item) {
      await loadPreview(data.item)
    }
  } catch (e) {
    listError.value =
      e instanceof FileDistributionRequestError
        ? e.message
        : e instanceof Error
          ? e.message
          : 'Не удалось загрузить список'
  } finally {
    loading.value = false
  }
}

async function onCopyPath(): Promise<void> {
  const p = item.value?.path?.trim()
  if (!p) return
  try {
    await copyTextToClipboard(p)
    flashClipKind('path')
  } catch {
    message.error('Не удалось скопировать путь')
  }
}

async function onCopyOpenCommand(): Promise<void> {
  const p = item.value?.path?.trim()
  if (!p) return
  try {
    await copyTextToClipboard(macOpenCommand(p))
    flashClipKind('open')
  } catch {
    message.error('Не удалось скопировать команду')
  }
}

async function onDelete(): Promise<void> {
  const fid = item.value?.file_id?.trim()
  if (!fid) return
  acting.value = true
  try {
    await postMarkFileDistributionDelete(fid)
    message.success('Помечено к удалению (to_delete)')
    await loadFirst()
  } catch (e) {
    message.error(
      e instanceof FileDistributionRequestError ? e.message : 'Не удалось сохранить',
    )
  } finally {
    acting.value = false
  }
}

async function onKeep(): Promise<void> {
  const fid = item.value?.file_id?.trim()
  if (!fid) return
  acting.value = true
  try {
    await postMarkFileDistributionKeep(fid)
    message.success('Оставляем — запись убрана из очереди')
    await loadFirst()
  } catch (e) {
    message.error(
      e instanceof FileDistributionRequestError ? e.message : 'Не удалось сохранить',
    )
  } finally {
    acting.value = false
  }
}

onBeforeUnmount(() => {
  revokeImageUrl()
  if (clipResetTimer !== null) clearTimeout(clipResetTimer)
})

void loadFirst()
</script>
