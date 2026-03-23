<template>
  <n-space vertical :size="16" class="uncertain-pair">
    <div class="uncertain-pair__primary-actions">
      <n-space vertical :size="8" align="center" class="uncertain-choice-actions">
        <n-space justify="center" wrap :size="12">
          <n-button
            type="warning"
            size="medium"
            :disabled="!selectedKeepFileId || submitting || !payload.item.uid"
            :loading="submitting"
            @click="onDeleteOthers"
          >
            Удалить остальные (оставить выбранную копию)
          </n-button>
          <n-button
            type="default"
            size="medium"
            :disabled="submitting || !payload.item.uid"
            :loading="submitting"
            @click="onKeepAll"
          >
            Оставить все копии в группе
          </n-button>
        </n-space>
        <n-alert
          v-if="resolveError"
          type="error"
          :show-icon="true"
          class="uncertain-choice-actions__error"
        >
          {{ resolveError }}
        </n-alert>
      </n-space>
    </div>

    <n-divider dashed />

    <n-space vertical :size="12" class="uncertain-previews">
      <n-space
        v-if="previewsLoading"
        vertical
        :size="8"
        align="center"
        justify="center"
        class="uncertain-previews__loading"
      >
        <n-spin size="medium" />
        <n-text depth="3">Загрузка превью…</n-text>
      </n-space>

      <n-alert v-else-if="previewError" type="warning" :show-icon="true" :bordered="true">
        {{ previewError }}
      </n-alert>

      <n-grid
        v-else
        :cols="previewGridCols"
        :x-gap="12"
        :y-gap="12"
        responsive="screen"
        class="uncertain-previews__grid"
      >
        <n-gi v-for="(f, idx) in payload.item.files" :key="fileRowKey(f, idx)">
          <n-card
            size="small"
            :bordered="true"
            class="media-preview-card uncertain-file-card uncertain-preview-column"
            :class="{ 'uncertain-preview-column--selected': isSelected(f) }"
          >
            <n-space vertical :size="10">
              <n-button
                block
                :type="isSelected(f) ? 'warning' : 'default'"
                :secondary="!isSelected(f)"
                :disabled="!f.file_id"
                @click="selectedKeepFileId = f.file_id?.trim() ?? null"
              >
                {{
                  isSelected(f)
                    ? 'Оставляем эту копию'
                    : 'Оставить эту копию'
                }}
              </n-button>
              <div class="uncertain-preview__media" @click.stop>
                <n-image
                  v-if="previewBlobUrl(f)"
                  class="uncertain-preview__image"
                  :src="previewBlobUrl(f)"
                  object-fit="contain"
                  :alt="f.filename ?? `Файл ${idx + 1}`"
                />
              </div>
              <n-space vertical :size="6">
                <n-text strong class="uncertain-file__name">{{ f.filename ?? `file ${idx + 1}` }}</n-text>
                <n-code v-if="f.file_id" class="uncertain-file__code">{{ f.file_id }}</n-code>
                <n-text v-else depth="3" italic>нет file_id</n-text>
              </n-space>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>

    <n-grid
      :cols="previewGridCols"
      :x-gap="12"
      :y-gap="12"
      responsive="screen"
      class="uncertain-files-grid"
    >
      <n-gi v-for="(f, idx) in payload.item.files" :key="`${fileRowKey(f, idx)}-detail`">
        <ExactFileDetailCard
          :label="`Файл ${idx + 1}`"
          :file="f"
          :path-copied="pathCopiedFor(f.file_id)"
          @copy-path="(p) => emit('copy-path', f.file_id, p)"
        />
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { submitResolveExactDuplicateChoice } from '../../api/exactDuplicates'
import { NearDuplicatesRequestError } from '../../api/nearDuplicates'
import type {
  ExactDuplicateFileEntry,
  FirstNotProcessedExactGroupResponse,
} from '../../types/exactDuplicates'
import ExactFileDetailCard from './ExactFileDetailCard.vue'

const props = defineProps<{
  payload: FirstNotProcessedExactGroupResponse
  previewsLoading: boolean
  previewError: string | null
  /** file_id → object URL */
  previewUrls: Record<string, string>
  pathCopiedFileId: string | null
}>()

const emit = defineEmits<{
  'copy-path': [fileId: string | undefined, path: string | undefined]
  resolved: []
}>()

const selectedKeepFileId = ref<string | null>(null)
const submitting = ref(false)
const resolveError = ref<string | null>(null)
const message = useMessage()

/** Как UncertainPairContent: две колонки при 2 файлах; при 3+ — третья колонка на широких экранах */
const previewGridCols = computed(() =>
  props.payload.item.files.length >= 3 ? '1 s:2 l:3' : '1 s:2',
)

function fileRowKey(f: ExactDuplicateFileEntry, idx: number): string {
  return f.file_id?.trim() || `idx-${idx}`
}

function isSelected(f: ExactDuplicateFileEntry): boolean {
  const id = f.file_id?.trim()
  return !!id && id === selectedKeepFileId.value
}

function previewBlobUrl(f: ExactDuplicateFileEntry): string | undefined {
  const id = f.file_id?.trim()
  if (!id) return undefined
  return props.previewUrls[id]
}

function pathCopiedFor(fileId: string | undefined): boolean {
  const id = fileId?.trim()
  return !!id && id === props.pathCopiedFileId
}

function groupIdentity(p: FirstNotProcessedExactGroupResponse): string {
  return p.item.uid ?? p.item.sha256 ?? p.item.files.map((f) => f.file_id).join('|')
}

watch(
  () => groupIdentity(props.payload),
  () => {
    selectedKeepFileId.value = null
    resolveError.value = null
  },
)

async function submitResolution(
  body: Parameters<typeof submitResolveExactDuplicateChoice>[0],
): Promise<void> {
  const uid = props.payload.item.uid?.trim()
  if (!uid) {
    resolveError.value =
      'У группы нет uid — пересобери duplicates-list.json (analyze_duplicates.py).'
    return
  }

  resolveError.value = null
  submitting.value = true
  try {
    await submitResolveExactDuplicateChoice(body)
    message.success('Решение сохранено')
    emit('resolved')
  } catch (e) {
    const text =
      e instanceof NearDuplicatesRequestError
        ? e.message
        : e instanceof Error
          ? e.message
          : 'Не удалось сохранить решение'
    resolveError.value = text
    message.error(text)
  } finally {
    submitting.value = false
  }
}

async function onDeleteOthers(): Promise<void> {
  const uid = props.payload.item.uid?.trim()
  const keepId = selectedKeepFileId.value?.trim()
  if (!uid || !keepId) return
  await submitResolution({
    group_uid: uid,
    key: 'exact_duplicates',
    keep_file_id: keepId,
  })
}

async function onKeepAll(): Promise<void> {
  const uid = props.payload.item.uid?.trim()
  if (!uid) return
  await submitResolution({
    group_uid: uid,
    key: 'exact_duplicates',
    keep_all: true,
  })
}
</script>
