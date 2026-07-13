<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { usePracticeStore } from '@/stores/practice'
import { formatAnswer, questionTypeLabel } from '@/utils'
import type { PracticeMode } from '@/types'

const route = useRoute()
const router = useRouter()
const store = usePracticeStore()

const bankId = computed(() => Number(route.params.id))
const mode = computed(() => (route.query.mode as PracticeMode) || 'sequence')

const touchStartX = ref(0)
const touchDeltaX = ref(0)

onMounted(async () => {
  try {
    await store.start(bankId.value, mode.value)
    if (!store.total) {
      showToast('该模式下没有题目')
    }
  } catch (e) {
    showToast((e as Error).message || '加载失败')
  }
})

function onModeSwitch(name: string | number) {
  store.setMemorize(name === 'memorize')
}

async function onSubmit() {
  if (!store.selected.length) {
    showToast('请先选择答案')
    return
  }
  try {
    await store.submit()
  } catch (e) {
    showToast((e as Error).message || '提交失败')
  }
}

async function onFavorite() {
  try {
    await store.toggleFavorite()
  } catch (e) {
    showToast((e as Error).message || '操作失败')
  }
}

function optionClass(label: string) {
  const selected = store.selected.includes(label)
  if (!store.submitted) {
    return selected ? 'opt selected' : 'opt'
  }
  const correct = store.result?.correct_answer || []
  const isCorrectOpt = correct.map((x) => x.toUpperCase()).includes(label.toUpperCase())
  if (isCorrectOpt) return 'opt correct'
  if (selected) return 'opt wrong'
  return 'opt'
}

function onTouchStart(e: TouchEvent) {
  touchStartX.value = e.changedTouches[0]?.clientX || 0
  touchDeltaX.value = 0
}

function onTouchEnd(e: TouchEvent) {
  const x = e.changedTouches[0]?.clientX || 0
  touchDeltaX.value = x - touchStartX.value
  if (touchDeltaX.value > 60) store.prev()
  else if (touchDeltaX.value < -60) store.next()
}
</script>

<template>
  <div class="page page-with-footer practice-page">
    <header class="topbar">
      <button class="icon-btn" type="button" @click="router.back()">返回</button>
      <van-tabs
        :active="store.memorize ? 'memorize' : 'answer'"
        shrink
        @change="onModeSwitch"
      >
        <van-tab title="答题" name="answer" />
        <van-tab title="背题" name="memorize" />
      </van-tabs>
      <span class="spacer" />
    </header>

    <van-loading v-if="store.loading" class="loading" vertical>加载中...</van-loading>

    <van-empty v-else-if="!store.current" description="暂无题目" />

    <main
      v-else
      class="question-area"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <div class="type-row">
        <van-tag type="primary" plain>{{ questionTypeLabel(store.current.question_type) }}</van-tag>
        <span v-if="store.current.chapter" class="muted">{{ store.current.chapter }}</span>
      </div>

      <h2 class="stem">{{ store.current.stem }}</h2>

      <div class="options">
        <button
          v-for="opt in store.current.options"
          :key="opt.label"
          type="button"
          :class="optionClass(opt.label)"
          @click="store.toggleOption(opt.label)"
        >
          <span class="label">{{ opt.label }}</span>
          <span class="content">{{ opt.content }}</span>
        </button>
      </div>

      <section v-if="store.submitted && store.result" class="feedback" :class="store.memorize ? 'memo' : store.result.is_correct ? 'ok' : 'bad'">
        <p v-if="!store.memorize" class="verdict">
          {{ store.result.is_correct ? '回答正确' : '回答错误' }}
        </p>
        <p class="answer-line">正确答案：{{ formatAnswer(store.result.correct_answer) }}</p>
        <p v-if="store.result.explanation" class="explain">{{ store.result.explanation }}</p>
      </section>
    </main>

    <footer class="footer-bar">
      <button class="fav-btn" type="button" @click="onFavorite">
        <van-icon :name="store.current?.is_favorite ? 'star' : 'star-o'" />
        收藏
      </button>
      <div class="counts">
        <span class="success-text">对 {{ store.correctCount }}</span>
        <span class="danger-text">错 {{ store.wrongCount }}</span>
      </div>
      <div class="pager">
        <button type="button" :disabled="store.index <= 0" @click="store.prev()">上一题</button>
        <span>{{ store.index + 1 }}/{{ store.total }}</span>
        <button type="button" :disabled="store.index >= store.total - 1" @click="store.next()">下一题</button>
      </div>
      <van-button
        v-if="!store.memorize && !store.submitted"
        type="primary"
        size="small"
        round
        @click="onSubmit"
      >
        提交
      </van-button>
    </footer>
  </div>
</template>

<style scoped>
.practice-page {
  background: #fff;
}
.topbar {
  display: grid;
  grid-template-columns: 56px 1fr 56px;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  padding: 4px 8px 0;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 20;
}
.icon-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-size: 15px;
  font-family: inherit;
  padding: 8px;
}
.spacer {
  width: 56px;
}
.loading {
  margin-top: 64px;
}
.question-area {
  padding: 16px 16px 24px;
  min-height: 60vh;
}
.type-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.stem {
  margin: 0 0 24px;
  font-size: 19px;
  line-height: 1.6;
  font-weight: 600;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.opt {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  width: 100%;
  padding: 16px;
  border: 1.5px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  text-align: left;
  font-family: inherit;
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text);
}
.opt .label {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eef2f6;
  font-weight: 600;
  font-size: 14px;
}
.opt.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.opt.selected .label {
  background: var(--color-primary);
  color: #fff;
}
.opt.correct {
  border-color: var(--color-success);
  background: #eafaf1;
}
.opt.correct .label {
  background: var(--color-success);
  color: #fff;
}
.opt.wrong {
  border-color: var(--color-danger);
  background: #fdf2f1;
}
.opt.wrong .label {
  background: var(--color-danger);
  color: #fff;
}
.feedback {
  margin-top: 24px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #f7f9fb;
}
.feedback.ok {
  background: #eafaf1;
}
.feedback.bad {
  background: #fdf2f1;
}
.verdict {
  margin: 0 0 8px;
  font-weight: 700;
  font-size: 16px;
}
.answer-line {
  margin: 0 0 8px;
  font-size: 15px;
}
.explain {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}
.footer-bar {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0;
  width: 100%;
  max-width: 430px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px calc(10px + var(--safe-bottom));
  background: #fff;
  border-top: 1px solid var(--color-border);
  z-index: 30;
}
.fav-btn {
  border: none;
  background: transparent;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--color-primary);
  font-family: inherit;
  font-size: 13px;
  padding: 4px;
}
.counts {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  line-height: 1.3;
}
.pager {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
}
.pager button {
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: 999px;
  padding: 4px 10px;
  font-family: inherit;
  font-size: 12px;
}
.pager button:disabled {
  opacity: 0.4;
}
</style>
