<template>
  <n-space vertical :size="10">
  <n-space :size="8" align="center" wrap class="uncertain-meta-row">
    <n-text depth="3" class="uncertain-meta__label">Ключ</n-text>
    <n-code class="uncertain-meta__code">{{ pairKey }}</n-code>
    <template v-if="item.uid">
      <n-text depth="3" class="uncertain-meta__label">ID пары</n-text>
      <n-code class="uncertain-meta__code">{{ item.uid }}</n-code>
    </template>
  </n-space>

  <n-space :size="8" align="center" wrap class="uncertain-meta-row">
    <n-text depth="3" class="uncertain-meta__label">distance</n-text>
    <n-text>{{ item.distance }}</n-text>
    <n-text depth="3" class="uncertain-meta__label">threshold</n-text>
    <n-text>{{ item.threshold_used }}</n-text>
    <n-text depth="3" class="uncertain-meta__label">processed</n-text>
    <n-text>{{ item.processed }}</n-text>
    <n-text depth="3" class="uncertain-meta__label">осталось пар</n-text>
    <n-text strong>{{ unprocessedPairCount }}</n-text>
    <n-text depth="3" class="uncertain-meta__label">файлов (2×пара)</n-text>
    <n-text strong>{{ filesInQueue }}</n-text>
  </n-space>
  </n-space>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NearDuplicatePairItem } from '../../types/nearDuplicates'

const props = defineProps<{
  pairKey: string
  item: NearDuplicatePairItem
  /** Сколько пар ещё не обработано (включая текущую) */
  unprocessedPairCount: number
}>()

/** В необработанных парах по два файла; один и тот же путь может встречаться в разных парах — это верхняя оценка. */
const filesInQueue = computed(() => props.unprocessedPairCount * 2)
</script>
