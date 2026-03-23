<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="naiveThemeOverrides">
    <n-message-provider>
    <n-layout class="app-layout" position="absolute">
      <n-layout-header bordered embedded class="app-header-glass">
        <n-space justify="space-between" align="center" wrap class="app-header-row">
          <router-link to="/" custom v-slot="{ href, navigate }">
            <n-a :href="href" @click.prevent="() => navigate()">
              <n-space align="center" :size="14">
                <n-avatar round :size="36" class="app-brand-mark app-brand-avatar" />
                <n-space vertical :size="4" class="app-brand-stack">
                  <n-gradient-text
                    class="app-brand-title"
                    gradient="linear-gradient(105deg, #e8eaef 0%, #b8f0e8 35%, #c9d6ff 70%, #f5e0b8 100%)"
                    :size="18"
                  >
                    Photo Duplicates
                  </n-gradient-text>
                  <n-text depth="3" class="app-brand-tagline">Дубликаты и файлы</n-text>
                </n-space>
              </n-space>
            </n-a>
          </router-link>

          <n-menu
            class="app-nav-menu"
            mode="horizontal"
            :value="menuValue"
            :options="menuOptions"
            responsive
            @update:value="onMenuUpdate"
          />
        </n-space>
      </n-layout-header>

      <n-layout-content :native-scrollbar="false" content-class="app-main-scroll">
        <RouterView />
      </n-layout-content>
    </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import type { MenuOption } from 'naive-ui'
import { darkTheme } from 'naive-ui'
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { naiveThemeOverrides } from './theme/naive-overrides'

const route = useRoute()
const router = useRouter()

const menuOptions: MenuOption[] = [
  { label: 'Главная', key: '/' },
  { label: 'Обработка дублей', key: '/duplicates' },
  { label: 'Точное совпадение', key: '/exact' },
  { label: 'Под вопросом', key: '/uncertain' },
  { label: 'Распределение файлов', key: '/file-distribution' },
]

const menuValue = computed(() => {
  const p = route.path
  if (p === '/exact' || p === '/uncertain' || p === '/duplicates') return p
  if (p === '/file-distribution') return '/file-distribution'
  return '/'
})

function onMenuUpdate(key: string | number) {
  void router.push(String(key))
}
</script>
