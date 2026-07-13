<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import { useBankStore } from '@/stores/bank'
import { sleep } from '@/utils'

const router = useRouter()
const bankStore = useBankStore()
const bankName = ref('')
const file = ref<File | null>(null)
const uploading = ref(false)

function onAfterRead(item: UploaderFileListItem | UploaderFileListItem[]) {
  const one = Array.isArray(item) ? item[0] : item
  const f = one?.file
  if (!f) return
  file.value = f
  if (!bankName.value) {
    bankName.value = f.name.replace(/\.docx?$/i, '')
  }
}

async function pollImport(id: number) {
  for (let i = 0; i < 40; i++) {
    const job = await bankStore.loadImport(id)
    if (job.status === 'preview' || job.status === 'confirmed' || (job.questions && job.questions.length >= 0)) {
      return job
    }
    await sleep(500)
  }
  return bankStore.currentImport
}

async function submit() {
  if (!file.value) {
    showToast('请选择 Word 文件')
    return
  }
  if (!bankName.value.trim()) {
    showToast('请填写题库名称')
    return
  }
  uploading.value = true
  showLoadingToast({ message: '解析中...', forbidClick: true, duration: 0 })
  try {
    const job = await bankStore.previewImport(file.value, bankName.value.trim())
    await pollImport(job.id)
    closeToast()
    router.replace(`/import/${job.id}`)
  } catch (e) {
    closeToast()
    showToast((e as Error).message || '上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="导入 Word" left-arrow @click-left="router.back()" />
    <div class="page-body">
      <p class="hint">支持 .docx。上传后会解析题目，进入校对页确认后再入库。</p>

      <van-field v-model="bankName" label="题库名" placeholder="例如：民法总则" clearable />

      <div class="uploader-wrap">
        <van-uploader
          :max-count="1"
          accept=".doc,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          :after-read="onAfterRead"
          @delete="file = null"
        >
          <van-button icon="description" type="primary" plain>选择 Word 文件</van-button>
        </van-uploader>
        <p v-if="file" class="file-name">{{ file.name }}</p>
      </div>

      <van-button block type="primary" round :loading="uploading" @click="submit">
        开始解析
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.hint {
  margin: 0 0 16px;
  color: var(--color-muted);
  font-size: 14px;
  line-height: 1.5;
}
.uploader-wrap {
  margin: 20px 0 28px;
}
.file-name {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-primary);
}
</style>
