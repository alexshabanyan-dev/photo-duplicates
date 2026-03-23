<template>
  <n-card
    :bordered="true"
    size="large"
    class="app-page"
    :class="`app-page--${variant}`"
    :segmented="{ content: 'soft' }"
    header-class="app-page-card__header"
    content-class="app-page-card__body"
  >
    <template #header>
      <n-space
        class="app-page-card__header-row"
        justify="space-between"
        align="flex-start"
        wrap
        :size="[14, 12]"
      >
        <n-space align="center" :size="14" class="app-page-card__header-title">
          <n-avatar
            round
            :size="32"
            :class="variant === 'exact' ? 'app-page__avatar--exact' : 'app-page__avatar--uncertain'"
          />
          <n-text tag="h1" strong class="app-page__title">
            {{ title }}
          </n-text>
        </n-space>
        <div v-if="$slots.headerExtra" class="app-page-card__header-extra">
          <slot name="headerExtra" />
        </div>
      </n-space>
    </template>

    <n-space v-if="$slots.intro" vertical :size="14">
      <slot name="intro" />
    </n-space>

    <n-divider v-if="$slots.intro" class="app-page__divider" />

    <slot />
  </n-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  variant: 'exact' | 'uncertain'
}>()
</script>
