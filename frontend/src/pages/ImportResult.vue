<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showLoadingToast, closeToast, showToast } from 'vant'
import { useBankStore } from '@/stores/bank'
import { classifyImportQuestion, importStats, questionTypeLabel } from '@/utils'
import type { ImportFilter } from '@/types'

const route = useRoute()
const router = useRouter()
const bankStore = useBankStore()
const filter = ref<ImportFilter>('abnormal')
const confirming = ref(false)

const jobId = computed(() => Number(route.params.id))

onMounted(async () => {
  try {
    await bankStore.loadImport(jobId.value)
  } catch (e) {
    showToast((e as Error).message || '加载失败')
  }
})

const stats = computed(() => importStats(bankStore.currentImport?.questions || []))

const filtered = computed(() => {
  const list = bankStore.currentImport?.questions || []
  if (filter.value === 'all') return list.map((q, i) => ({ q, i }))
  return list
    .map((q, i) => ({ q, i }))
    .filter(({ q }) => classifyImportQuestion(q) === filter.value)
})

async function confirm() {
  if (!bankStore.currentImport) return
  try {
    await showConfirmDialog({
      title: '确认入库',
      message: `将导入 ${bankStore.currentImport.questions.length} 道题到「${bankStore.currentImport.bank_name}」`,
    })
  } catch {
    return
  }
  confirming.value = true
  showLoadingToast({ message: '入库中...', forbidClick: true, duration: 0 })
  try {
    await bankStore.confirmImport(bankStore.currentImport.questions)
    closeToast()
    showToast('导入成功')
    await bankStore.fetchBanks()
    router.replace('/')
  } catch (e) {
    closeToast()
    showToast((e as Error).message || '确认失败')
  } finally {
    confirming.value = false
  }
}
</script>

<template>
  <div class="page page-with-footer">
    <van-nav-bar title="导入校对" left-arrow @click-left="router.push('/')" />

    <div v-if="bankStore.currentImport" class="page-body">
      <h2 class="bank-name">{{ bankStore.currentImport.bank_name }}</h2>
      <p class="muted">{{ bankStore.currentImport.source_filename }}</p>

      <div class="stats">
        <div><strong>{{ stats.total }}</strong><span>总计</span></div>
        <div><strong class="success-text">{{ stats.normal }}</strong><span>正常</span></div>
        <div><strong class="danger-text">{{ stats.abnormal }}</strong><span>异常</span></div>
        <div><strong>{{ stats.failed }}</strong><span>失败</span></div>
        <div><strong>{{ stats.duplicate }}</strong><span>重复</span></div>
      </div>

      <van-tabs v-model:active="filter" shrink>
        <van-tab title="异常" name="abnormal" />
        <van-tab title="全部" name="all" />
        <van-tab title="正常" name="normal" />
        <van-tab title="失败" name="failed" />
        <van-tab title="重复" name="duplicate" />
      </van-tabs>

      <van-empty v-if="!filtered.length" description="该分类下没有题目" />

      <div v-for="{ q, i } in filtered" :key="i" class="q-card" @click="router.push(`/import/${jobId}/edit/${i}`)">
        <div class="q-meta">
          <van-tag plain type="primary">{{ questionTypeLabel(q.question_type) }}</van-tag>
          <van-tag v-if="classifyImportQuestion(q) === 'abnormal'" type="danger">异常</van-tag>
          <van-tag v-else-if="classifyImportQuestion(q) === 'failed'" type="warning">失败</van-tag>
          <van-tag v-else-if="classifyImportQuestion(q) === 'duplicate'" type="primary">重复</van-tag>
          <span class="muted">#{{ i + 1 }}</span>
        </div>
        <p class="stem">{{ q.stem || '（空题干）' }}</p>
        <p v-if="q.issues?.length" class="issues">{{ q.issues.join('；') }}</p>
      </div>
    </div>

    <div class="footer-bar">
      <van-button block type="primary" round :loading="confirming" @click="confirm">确认入库</van-button>
    </div>
  </div>
</template>

<style scoped>
.bank-name {
  margin: 0 0 4px;
  font-size: 20px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  margin: 16px 0;
  text-align: center;
}
.stats strong {
  display: block;
  font-size: 18px;
}
.stats span {
  font-size: 12px;
  color: var(--color-muted);
}
.q-card {
  margin-top: 12px;
  padding: 14px;
  border-bottom: 1px solid var(--color-border);
}
.q-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.stem {
  margin: 0;
  font-size: 16px;
  line-height: 1.55;
}
.issues {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--color-danger);
}
.footer-bar {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0;
  width: 100%;
  max-width: 430px;
  padding: 12px 16px calc(12px + var(--safe-bottom));
  background: #fff;
  border-top: 1px solid var(--color-border);
  z-index: 30;
}
</style>
