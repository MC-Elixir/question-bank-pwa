import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'banks', component: () => import('@/pages/Banks.vue'), meta: { title: '我的题库' } },
    { path: '/import', name: 'import', component: () => import('@/pages/Import.vue'), meta: { title: '导入 Word' } },
    {
      path: '/import/:id',
      name: 'import-result',
      component: () => import('@/pages/ImportResult.vue'),
      meta: { title: '导入校对' },
    },
    {
      path: '/import/:id/edit/:index',
      name: 'question-edit',
      component: () => import('@/pages/QuestionEdit.vue'),
      meta: { title: '编辑题目' },
    },
    {
      path: '/banks/:id',
      name: 'practice-home',
      component: () => import('@/pages/PracticeHome.vue'),
      meta: { title: '练习' },
    },
    {
      path: '/banks/:id/practice',
      name: 'practice',
      component: () => import('@/pages/Practice.vue'),
      meta: { title: '答题' },
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || '个人题库'
  document.title = `${title} · 个人题库`
})

export default router
