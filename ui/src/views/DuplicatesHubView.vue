<template>
  <n-space vertical :size="28">
    <n-card class="home-hero" :bordered="false" embedded>
      <n-space vertical :size="14">
        <n-h1 class="home-view__heading">Обработка дублей</n-h1>
        <n-p depth="2" class="home-view__lead">
          Результаты сканера разделены на два типа: где дубликат очевиден, и где совпадение только предполагается. Перейдите
          в нужный раздел — там будет список групп и действия с файлами.
        </n-p>
      </n-space>
    </n-card>

    <n-grid cols="1 s:2" :x-gap="18" :y-gap="18" responsive="screen">
      <n-gi v-for="c in cards" :key="c.to">
        <router-link :to="c.to" custom v-slot="{ href, navigate }">
          <n-a :href="href" class="home-card-link" :class="`home-card-link--${c.name}`" @click.prevent="() => navigate()">
            <n-card hoverable :bordered="true" class="home-card">
              <n-space vertical :size="16" align="stretch">
                <n-space justify="space-between" align="flex-start" :wrap="false">
                  <n-space align="center" :size="12" :wrap="false">
                    <n-avatar
                      round
                      :size="22"
                      :class="c.name === 'exact' ? 'home-card__mark--exact' : 'home-card__mark--uncertain'"
                    />
                    <n-text strong class="home-card__title">{{ c.title }}</n-text>
                  </n-space>
                  <n-tag
                    size="small"
                    :bordered="false"
                    round
                    class="home-card__tag-pill"
                    :type="c.name === 'exact' ? 'primary' : 'warning'"
                  >
                    {{ c.name === 'exact' ? 'точно' : 'вопрос' }}
                  </n-tag>
                </n-space>

                <n-text depth="3" class="home-card__description">{{ c.description }}</n-text>

                <n-ul align-text class="home-card__list">
                  <n-li v-for="(p, i) in c.points" :key="i" class="home-card__list-item">
                    <n-text depth="3">{{ p }}</n-text>
                  </n-li>
                </n-ul>

                <n-divider class="home-card__divider" />

                <n-text
                  :type="c.name === 'exact' ? 'primary' : 'warning'"
                  strong
                  class="home-card__cta"
                >
                  Открыть раздел →
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
const cards = [
  {
    to: '/exact',
    name: 'exact' as const,
    title: 'Точное совпадение',
    description:
      'Файлы, которые совпадают побайтово или по криптографическому хэшу. Такие дубликаты можно удалять уверенно — это одно и то же изображение.',
    points: ['Одинаковое содержимое файла', 'Нет риска перепутать с «похожим» кадром'],
  },
  {
    to: '/uncertain',
    name: 'uncertain' as const,
    title: 'Совпадение под вопросом',
    description:
      'Картинки, похожие визуально или по метаданным, но без гарантии идентичности: ресайз, пережатие, чуть другой кадр, скриншот.',
    points: ['Нужен просмотр и решение вручную', 'Подходит для похожих серий и near-duplicates'],
  },
]
</script>
