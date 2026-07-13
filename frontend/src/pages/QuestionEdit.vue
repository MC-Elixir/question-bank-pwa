<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useBankStore } from '@/stores/bank'
import type { OptionItem, QuestionType } from '@/types'

const route = useRoute()
const router = useRouter()
const bankStore = useBankStore()

const jobId = computed(() => Number(route.params.id))
const qIndex = computed(() => Number(route.params.index))
const loaded = ref(false)

const form = reactive({
  chapter: '',
  question_type: 'single_choice' as QuestionType,
  stem: '',
  answerText: '',
  explanation: '',
  optionsText: '',
  needs_review: false,
})

onMounted(async () => {
  if (!bankStore.currentImport || bankStore.currentImport.id !== jobId.value) {
    await bankStore.loadImport(jobId.value)
  }
  const q = bankStore.currentImport?.questions[qIndex.value]
  if (!q) {
    showToast('题目不存在')
    router.back()
    return
  }
  form.chapter = q.chapter || ''
  form.question_type = q.question_type
  form.stem = q.stem
  form.answerText = (q.answer || []).join('')
  form.explanation = q.explanation || ''
  form.optionsText = (q.options || []).map((o) => `${o.label}. ${o.content}`).join('\n')
  form.needs_review = !!q.needs_review
  loaded.value = true
})

function parseOptions(text: string): OptionItem[] {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
  return lines.map((line, idx) => {
    const m = line.match(/^([A-Za-z])[.、．\s]+(.*)$/)
    if (m) return { label: m[1].toUpperCase(), content: m[2].trim(), sort_order: idx }
    return { label: String.fromCharCode(65 + idx), content: line, sort_order: idx }
  })
}

function save() {
  if (!bankStore.currentImport) return
  const questions = [...bankStore.currentImport.questions]
  const prev = questions[qIndex.value]
  const options = parseOptions(form.optionsText)
  let finalAnswer: string[]
  if (form.question_type === 'judgment') {
    const t = form.answerText.trim()
    finalAnswer = t ? [t] : []
  } else {
    finalAnswer = form.answerText
      .toUpperCase()
      .replace(/[^A-Z]/g, '')
      .split('')
  }
  questions[qIndex.value] = {
    ...prev,
    chapter: form.chapter || null,
    question_type: form.question_type,
    stem: form.stem,
    options,
    answer: finalAnswer,
    explanation: form.explanation || null,
    needs_review: form.needs_review,
    issues: form.needs_review ? prev.issues || [] : [],
  }
  bankStore.updateImportQuestions(questions)
  showToast('已保存')
  router.back()
}
</script>

<template>
  <div class="page page-with-footer">
    <van-nav-bar title="编辑题目" left-arrow @click-left="router.back()" />
    <div v-if="loaded" class="page-body">
      <van-field v-model="form.chapter" label="章节" placeholder="可选" />
      <van-field label="题型">
        <template #input>
          <van-radio-group v-model="form.question_type" direction="horizontal">
            <van-radio name="single_choice">单选</van-radio>
            <van-radio name="multiple_choice">多选</van-radio>
            <van-radio name="judgment">判断</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-model="form.stem" rows="4" autosize label="题干" type="textarea" required />
      <van-field
        v-model="form.optionsText"
        rows="5"
        autosize
        label="选项"
        type="textarea"
        placeholder="每行一个，如 A. 内容"
      />
      <van-field v-model="form.answerText" label="答案" placeholder="如 A 或 ABD / 对" />
      <van-field v-model="form.explanation" rows="3" autosize label="解析" type="textarea" />
      <van-cell title="仍需复核">
        <template #right-icon>
          <van-switch v-model="form.needs_review" size="20px" />
        </template>
      </van-cell>
    </div>
    <div class="footer-bar">
      <van-button block type="primary" round @click="save">保存</van-button>
    </div>
  </div>
</template>

<style scoped>
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
}
.page-body :deep(.van-radio) {
  margin-right: 10px;
}
</style>
