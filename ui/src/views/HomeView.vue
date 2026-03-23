<template>
  <n-space vertical :size="28">
    <n-card class="home-hero" :bordered="false" embedded>
      <n-space vertical :size="12">
        <n-h1 class="home-view__heading">Главная</n-h1>
        <n-p depth="2" class="home-view__lead">
          Выберите раздел: обработка найденных дублей или распределение файлов (скоро).
        </n-p>
      </n-space>
    </n-card>

    <n-grid cols="1 m:2" :x-gap="22" :y-gap="22" responsive="screen">
      <n-gi v-for="item in modules" :key="item.to">
        <router-link :to="item.to" custom v-slot="{ href, navigate }">
          <n-a
            :href="href"
            class="home-module-link"
            :class="`home-module-link--${item.variant}`"
            @click.prevent="() => navigate()"
          >
            <n-card hoverable :bordered="true" class="home-module-card">
              <n-space vertical :size="20" align="stretch">
                <n-space align="center" :size="16" :wrap="false">
                  <n-avatar round :size="40" :class="`home-module-card__avatar--${item.variant}`" />
                  <n-space vertical :size="4">
                    <n-text strong class="home-module-card__title">{{ item.title }}</n-text>
                    <n-tag size="small" :bordered="false" round :type="item.tagType">
                      {{ item.tag }}
                    </n-tag>
                  </n-space>
                </n-space>

                <n-text depth="3" class="home-module-card__description">
                  {{ item.description }}
                </n-text>

                <n-divider dashed class="home-module-card__divider" />

                <n-text :type="item.ctaType" strong class="home-module-card__cta">
                  Перейти →
                </n-text>
              </n-space>
            </n-card>
          </n-a>
        </router-link>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
type ModuleItem = {
  to: string
  title: string
  description: string
  tag: string
  tagType: 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'
  ctaType: 'primary' | 'warning' | 'default' | 'success' | 'info'
  variant: 'duplicates' | 'distribution'
}

const modules: ModuleItem[] = [
  {
    to: '/duplicates',
    title: 'Обработка дублей',
    description:
      'Точные дубликаты по хэшу и пары «под вопросом»: просмотр, решение, что оставить и что пометить к удалению.',
    tag: 'основной поток',
    tagType: 'primary',
    ctaType: 'primary',
    variant: 'duplicates',
  },
  {
    to: '/file-distribution',
    title: 'Распределение файлов',
    description:
      'Инструменты для раскладки файлов по каталогам и правилам. Раздел подготавливается.',
    tag: 'скоро',
    tagType: 'default',
    ctaType: 'default',
    variant: 'distribution',
  },
]
</script>
