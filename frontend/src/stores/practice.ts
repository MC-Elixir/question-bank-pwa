import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/api'
import type { AnswerResponse, PracticeMode, Question } from '@/types'

export const usePracticeStore = defineStore('practice', () => {
  const bankId = ref<number | null>(null)
  const mode = ref<PracticeMode>('sequence')
  const questions = ref<Question[]>([])
  const index = ref(0)
  const selected = ref<string[]>([])
  const submitted = ref(false)
  const result = ref<AnswerResponse | null>(null)
  const memorize = ref(false)
  const correctCount = ref(0)
  const wrongCount = ref(0)
  const loading = ref(false)

  const current = computed(() => questions.value[index.value] || null)
  const total = computed(() => questions.value.length)

  async function start(id: number, practiceMode: PracticeMode) {
    bankId.value = id
    mode.value = practiceMode
    memorize.value = practiceMode === 'memorize'
    loading.value = true
    index.value = 0
    selected.value = []
    submitted.value = false
    result.value = null
    correctCount.value = 0
    wrongCount.value = 0
    try {
      const apiMode = practiceMode === 'memorize' ? 'sequence' : practiceMode
      questions.value = await api.listQuestions(id, apiMode)
      if (memorize.value && questions.value.length) {
        submitted.value = true
        const q = questions.value[0]
        result.value = {
          is_correct: true,
          correct_answer: q.answer,
          explanation: q.explanation,
        }
      }
    } finally {
      loading.value = false
    }
  }

  function resetQuestionState() {
    selected.value = []
    if (memorize.value) {
      submitted.value = true
      const q = current.value
      result.value = q
        ? { is_correct: true, correct_answer: q.answer, explanation: q.explanation }
        : null
    } else {
      submitted.value = false
      result.value = null
    }
  }

  function goTo(i: number) {
    if (i < 0 || i >= questions.value.length) return
    index.value = i
    resetQuestionState()
  }

  function next() {
    goTo(index.value + 1)
  }

  function prev() {
    goTo(index.value - 1)
  }

  function toggleOption(label: string) {
    if (submitted.value && !memorize.value) return
    const q = current.value
    if (!q) return
    if (q.question_type === 'multiple_choice') {
      if (selected.value.includes(label)) {
        selected.value = selected.value.filter((x) => x !== label)
      } else {
        selected.value = [...selected.value, label]
      }
    } else {
      selected.value = [label]
    }
  }

  async function submit() {
    const q = current.value
    if (!q || !selected.value.length) return
    const res = await api.submitAnswer(q.id, selected.value)
    result.value = res
    submitted.value = true
    if (res.is_correct) correctCount.value += 1
    else wrongCount.value += 1
    q.answered = true
    q.is_wrong = !res.is_correct
  }

  async function toggleFavorite() {
    const q = current.value
    if (!q) return
    const updated = await api.setFavorite(q.id, !q.is_favorite)
    q.is_favorite = updated.is_favorite
  }

  function setMemorize(on: boolean) {
    memorize.value = on
    resetQuestionState()
  }

  return {
    bankId,
    mode,
    questions,
    index,
    selected,
    submitted,
    result,
    memorize,
    correctCount,
    wrongCount,
    loading,
    current,
    total,
    start,
    goTo,
    next,
    prev,
    toggleOption,
    submit,
    toggleFavorite,
    setMemorize,
  }
})
