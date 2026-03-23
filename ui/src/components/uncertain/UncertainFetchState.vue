<template>
  <n-space vertical :size="20" class="uncertain-state" role="region" aria-live="polite">
    <n-space
      v-if="loading"
      vertical
      :size="12"
      align="center"
      justify="center"
      class="uncertain-state__loading"
    >
      <n-spin size="large" />
      <n-text depth="3">{{ loadingHint }}</n-text>
    </n-space>

    <n-alert
      v-else-if="errorMessage"
      type="warning"
      title="Не удалось получить данные"
      :show-icon="true"
      :bordered="true"
      role="alert"
    >
      {{ errorMessage }}
      <n-button
        type="warning"
        secondary
        size="small"
        class="uncertain-state__retry"
        @click="emit('retry')"
      >
        Повторить
      </n-button>
    </n-alert>

    <slot v-else />
  </n-space>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    loading: boolean
    errorMessage: string | null
    /** Текст под спиннером при первой загрузке */
    loadingHint?: string
  }>(),
  {
    loadingHint: 'Загрузка первой необработанной пары…',
  },
)

const emit = defineEmits<{
  retry: []
}>()
</script>
