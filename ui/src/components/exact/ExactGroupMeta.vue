<template>
  <n-space vertical :size="10">
    <n-space :size="8" align="center" wrap class="uncertain-meta-row">
      <n-text depth="3" class="uncertain-meta__label">Ключ</n-text>
      <n-code class="uncertain-meta__code">{{ groupKey }}</n-code>
      <template v-if="item.uid">
        <n-text depth="3" class="uncertain-meta__label">ID группы</n-text>
        <n-code class="uncertain-meta__code">{{ item.uid }}</n-code>
      </template>
    </n-space>

    <n-space :size="8" align="center" wrap class="uncertain-meta-row">
      <n-text depth="3" class="uncertain-meta__label">SHA256</n-text>
      <n-code class="uncertain-meta__code uncertain-meta__code--sha">{{ item.sha256 }}</n-code>
      <n-text depth="3" class="uncertain-meta__label">файлов в группе</n-text>
      <n-text strong>{{ item.files?.length ?? item.count }}</n-text>
      <n-text depth="3" class="uncertain-meta__label">processed</n-text>
      <n-text>{{ item.processed }}</n-text>
      <n-text depth="3" class="uncertain-meta__label">осталось групп</n-text>
      <n-text strong>{{ unprocessedGroupCount }}</n-text>
    </n-space>
  </n-space>
</template>

<script setup lang="ts">
import type { ExactDuplicateGroupItem } from '../../types/exactDuplicates'

defineProps<{
  groupKey: string
  item: ExactDuplicateGroupItem
  unprocessedGroupCount: number
}>()
</script>
