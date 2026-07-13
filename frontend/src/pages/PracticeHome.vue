<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '@/api'
import type { PracticeMode, QuestionBank } from '@/types'

const route = useRoute()
const router = useRouter()
const bankId = computed(() => Number(route.params.id))
const bank = ref<QuestionBank | null>(null)

const modes: { mode: PracticeMode; title: string; desc: string }[] = [
  { mode: 'sequence', title: '顺序练习', desc: '按题目顺序作答' },
  { mode: 'random', title: '随机练习', desc: '打乱顺序挑战' },
  { mode: 'unanswered', title: '未做题目', desc: '只练还没做过的' },
  { mode: 'wrong', title: '错题练习', desc: '巩固答错的题' },
  { mode: 'favorite', title: '收藏练习', desc: '复习已收藏' },
  { mode: 'memorize', title: '背题模式', desc: '直接看答案记忆' },
]

onMounted(async () => {
  try {
    const banks = await api.listBanks()
    bank.value = banks.find((b) => b.id === bankId.value) || null
  } catch (e) {
    showToast((e as Error).message || '加载失败')
  }
})

function go(mode: PracticeMode) {
  router.push(`/banks/${bankId.value}/practice?mode=${mode}`)
}
</script>

<template>
  <div class="page">
    <van-nav-bar :title="bank?.name || '练习'" left-arrow @click-left="router.push('/')" />
    <div class="page-body">
      <p class="muted">共 {{ bank?.question_count ?? '—' }} 题，选择一种练习方式</p>
      <div class="mode-grid">
        <button
          v-for="item in modes"
          :key="item.mode"
          class="mode-btn"
          type="button"
          @click="go(item.mode)"
        >
          <span class="mode-title">{{ item.title }}</span>
          <span class="mode-desc">{{ item.desc }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mode-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  min-height: 96px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  text-align: left;
  font-family: inherit;
}
.mode-btn:active {
  background: var(--color-primary-soft);
}
.mode-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-primary);
}
.mode-desc {
  font-size: 13px;
  color: var(--color-muted);
}
</style>
