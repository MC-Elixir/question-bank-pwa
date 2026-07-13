import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'
import type { BankWithStats, ImportJob, ParsedQuestion } from '@/types'

export const useBankStore = defineStore('bank', () => {
  const banks = ref<BankWithStats[]>([])
  const loading = ref(false)
  const currentImport = ref<ImportJob | null>(null)

  async function fetchBanks() {
    loading.value = true
    try {
      const list = await api.listBanks()
      const withStats: BankWithStats[] = []
      for (const bank of list) {
        let answered = 0
        let wrong = 0
        let favorite = 0
        let correct = 0
        try {
          const questions = await api.listQuestions(bank.id, 'sequence')
          for (const q of questions) {
            if (q.answered) {
              answered += 1
              if (q.is_wrong) wrong += 1
              else correct += 1
            }
            if (q.is_favorite) favorite += 1
          }
        } catch {
          /* ignore per-bank errors */
        }
        const accuracy = answered ? Math.round((correct / answered) * 100) : 0
        const progress = bank.question_count
          ? Math.round((answered / bank.question_count) * 100)
          : 0
        withStats.push({ ...bank, answered, wrong, favorite, accuracy, progress })
      }
      banks.value = withStats
    } finally {
      loading.value = false
    }
  }

  async function loadImport(id: number) {
    currentImport.value = await api.getImport(id)
    return currentImport.value
  }

  async function previewImport(file: File, bankName: string) {
    currentImport.value = await api.previewImport(file, bankName)
    return currentImport.value
  }

  async function confirmImport(questions?: ParsedQuestion[]) {
    if (!currentImport.value) throw new Error('没有导入任务')
    currentImport.value = await api.confirmImport(currentImport.value.id, questions)
    return currentImport.value
  }

  function updateImportQuestions(questions: ParsedQuestion[]) {
    if (currentImport.value) {
      currentImport.value = { ...currentImport.value, questions }
    }
  }

  return {
    banks,
    loading,
    currentImport,
    fetchBanks,
    loadImport,
    previewImport,
    confirmImport,
    updateImportQuestions,
  }
})
