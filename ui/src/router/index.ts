import { createRouter, createWebHistory } from 'vue-router'
import DuplicatesHubView from '../views/DuplicatesHubView.vue'
import ExactMatchView from '../views/ExactMatchView.vue'
import FileDistributionView from '../views/FileDistributionView.vue'
import HomeView from '../views/HomeView.vue'
import UncertainMatchView from '../views/UncertainMatchView.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Главная' },
    },
    {
      path: '/duplicates',
      name: 'duplicates',
      component: DuplicatesHubView,
      meta: { title: 'Обработка дублей' },
    },
    {
      path: '/exact',
      name: 'exact',
      component: ExactMatchView,
      meta: { title: 'Точное совпадение' },
    },
    {
      path: '/uncertain',
      name: 'uncertain',
      component: UncertainMatchView,
      meta: { title: 'Совпадение под вопросом' },
    },
    {
      path: '/file-distribution',
      name: 'file-distribution',
      component: FileDistributionView,
      meta: { title: 'Распределение файлов' },
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const suffix = to.meta.title ? ` — ${to.meta.title}` : ''
  document.title = `Photo Duplicates${suffix}`
})
