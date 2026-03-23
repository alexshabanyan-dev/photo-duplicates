<template>
  <n-card v-if="!embedded" size="small" bordered class="uncertain-file-card">
    <n-space vertical :size="10">
      <n-tag size="small" type="warning" :bordered="false" round>{{ label }}</n-tag>
      <n-text strong class="uncertain-file__name">{{ file.filename ?? '—' }}</n-text>
      <n-space vertical :size="4" class="uncertain-file__id-stack">
        <n-text depth="3" class="uncertain-file__id-label">file_id</n-text>
        <n-code v-if="file.file_id" class="uncertain-file__code uncertain-file__code--block">{{ file.file_id }}</n-code>
        <n-text v-else depth="3" italic>—</n-text>
      </n-space>
      <n-space align="flex-start" :size="8" wrap class="uncertain-file__path-row">
        <n-text depth="3" class="uncertain-file__path">{{ file.path }}</n-text>
        <n-button
          size="tiny"
          type="warning"
          secondary
          :disabled="!file.path"
          title="Скопировать путь в буфер обмена"
          :aria-label="`Скопировать путь к файлу (${label})`"
          @click="emit('copy-path', file.path)"
        >
          {{ pathCopied ? 'Скопировано' : 'Копировать путь' }}
        </n-button>
      </n-space>
    </n-space>
  </n-card>
  <div v-else class="exact-file-detail--embedded uncertain-file-card">
    <n-space vertical :size="10">
      <n-tag size="small" type="warning" :bordered="false" round>{{ label }}</n-tag>
      <n-text strong class="uncertain-file__name">{{ file.filename ?? '—' }}</n-text>
      <n-space vertical :size="4" class="uncertain-file__id-stack">
        <n-text depth="3" class="uncertain-file__id-label">file_id</n-text>
        <n-code v-if="file.file_id" class="uncertain-file__code uncertain-file__code--block">{{ file.file_id }}</n-code>
        <n-text v-else depth="3" italic>—</n-text>
      </n-space>
      <n-space align="flex-start" :size="8" wrap class="uncertain-file__path-row">
        <n-text depth="3" class="uncertain-file__path">{{ file.path }}</n-text>
        <n-button
          size="tiny"
          type="warning"
          secondary
          :disabled="!file.path"
          title="Скопировать путь в буфер обмена"
          :aria-label="`Скопировать путь к файлу (${label})`"
          @click="emit('copy-path', file.path)"
        >
          {{ pathCopied ? 'Скопировано' : 'Копировать путь' }}
        </n-button>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import type { ExactDuplicateFileEntry } from '../../types/exactDuplicates'

defineProps<{
  label: string
  file: ExactDuplicateFileEntry
  pathCopied: boolean
  /** true — без своей карточки: блок для вставки под превью внутри родительской карточки */
  embedded?: boolean
}>()

const emit = defineEmits<{
  'copy-path': [path: string | undefined]
}>()
</script>
