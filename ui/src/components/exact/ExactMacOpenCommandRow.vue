<template>
  <n-space v-if="command" vertical :size="6" class="exact-mac-open">
    <n-text depth="3" class="uncertain-file__id-label">Команда для Terminal (macOS)</n-text>
    <n-space align="flex-start" :size="8" wrap class="uncertain-file__path-row exact-mac-open__row">
      <n-code class="uncertain-file__code uncertain-file__code--block exact-mac-open__code">{{ command }}</n-code>
      <n-button
        size="tiny"
        quaternary
        circle
        :disabled="!command"
        :title="copied ? 'Скопировано' : 'Скопировать команду open'"
        :aria-label="ariaCopyLabel"
        @click="onCopy"
      >
        <template #icon>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
            class="exact-mac-open__icon"
          >
            <path
              d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"
            />
          </svg>
        </template>
      </n-button>
    </n-space>
  </n-space>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { macOpenCommand } from '../../utils/macosOpenCommand'

const props = withDefaults(
  defineProps<{
    filePath: string | undefined
    /** Краткая обратная связь после копирования */
    copied?: boolean
    /** Для aria-label */
    label?: string
  }>(),
  { copied: false },
)

const emit = defineEmits<{
  copy: [command: string]
}>()

const command = computed(() => macOpenCommand(props.filePath))

const ariaCopyLabel = computed(() =>
  props.label
    ? `Скопировать команду open (${props.label})`
    : 'Скопировать команду open',
)

function onCopy(): void {
  const c = command.value
  if (c) emit('copy', c)
}
</script>

<style scoped>
.exact-mac-open {
  width: 100%;
  min-width: 0;
}

.exact-mac-open__row {
  width: 100%;
}

.exact-mac-open__code {
  flex: 1 1 12rem;
  min-width: 0;
  max-width: 100%;
  word-break: break-all;
  white-space: pre-wrap;
  font-size: 0.75rem;
}

.exact-mac-open__icon {
  display: block;
}
</style>
