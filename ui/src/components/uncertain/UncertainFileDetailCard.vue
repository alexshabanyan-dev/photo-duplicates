<template>
  <n-card size="small" :bordered="true" class="uncertain-file-card">
    <n-space vertical :size="10">
      <n-tag size="small" type="warning" :bordered="false" round>{{ side }}</n-tag>
      <n-text strong class="uncertain-file__name">{{ file.filename }}</n-text>
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
          :aria-label="`Скопировать путь к файлу (${side})`"
          @click="emit('copy-path', file.path)"
        >
          {{ pathCopied ? 'Скопировано' : 'Копировать путь' }}
        </n-button>
      </n-space>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import type { PathCopySide } from '../../composables/usePathCopy'
import type { NearDuplicateSide } from '../../types/nearDuplicates'

defineProps<{
  side: PathCopySide
  file: NearDuplicateSide
  pathCopied: boolean
}>()

const emit = defineEmits<{
  'copy-path': [path: string | undefined]
}>()
</script>
