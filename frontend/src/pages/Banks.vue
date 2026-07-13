<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useBankStore } from '@/stores/bank'
import { api } from '@/api'

const router = useRouter()
const bankStore = useBankStore()
const backupInput = ref<HTMLInputElement | null>(null)

onMounted(() => {
  bankStore.fetchBanks()
})

async function onExport() {
  try {
    const blob = await api.exportBackup()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'question_bank_backup.json'
    a.click()
    URL.revokeObjectURL(url)
    showToast('已导出备份')
  } catch (e) {
    showToast((e as Error).message || '导出失败')
  }
}

async function onImportBackup(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const res = await api.importBackup(file)
    showToast(res.message || `已导入 ${res.banks} 个题库`)
    await bankStore.fetchBanks()
  } catch (err) {
    showToast((err as Error).message || '导入失败')
  } finally {
    input.value = ''
  }
}
</script>

<template>
  <div class="page">
    <header class="hero">
      <div>
        <p class="brand">个人题库</p>
        <p class="muted">导入 Word · 刷题 · 背题</p>
      </div>
      <div class="hero-actions">
        <van-button size="small" plain type="primary" @click="onExport">备份</van-button>
        <van-button size="small" plain @click="backupInput?.click()">恢复</van-button>
        <input ref="backupInput" type="file" accept="application/json,.json" hidden @change="onImportBackup" />
      </div>
    </header>

    <div class="page-body">
      <van-button block type="primary" round icon="plus" @click="router.push('/import')">
        导入 Word 题库
      </van-button>

      <van-loading v-if="bankStore.loading" class="loading" vertical>加载中...</van-loading>

      <van-empty v-else-if="!bankStore.banks.length" description="还没有题库，先导入一份 Word 吧" />

      <div v-else class="bank-list">
        <article v-for="bank in bankStore.banks" :key="bank.id" class="bank-item">
          <div class="bank-top" @click="router.push(`/banks/${bank.id}`)">
            <h2>{{ bank.name }}</h2>
            <p class="muted">{{ bank.question_count }} 题 · 进度 {{ bank.progress }}% · 正确率 {{ bank.accuracy }}%</p>
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: `${bank.progress}%` }" />
            </div>
          </div>
          <div class="bank-actions">
            <van-button size="small" type="primary" @click="router.push(`/banks/${bank.id}/practice?mode=sequence`)">
              继续练习
            </van-button>
            <van-button size="small" plain type="primary" @click="router.push(`/banks/${bank.id}`)">
              练习模式
            </van-button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 28px 16px 18px;
  background: linear-gradient(180deg, #eaf2f8 0%, #ffffff 100%);
  border-bottom: 1px solid var(--color-border);
}
.brand {
  margin: 0 0 4px;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 0.02em;
}
.hero-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.loading {
  margin-top: 48px;
}
.bank-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.bank-item {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
}
.bank-top h2 {
  margin: 0 0 6px;
  font-size: 18px;
}
.progress-track {
  margin-top: 10px;
  height: 6px;
  border-radius: 999px;
  background: #eef2f6;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--color-primary);
}
.bank-actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}
</style>
