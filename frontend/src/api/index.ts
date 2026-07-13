import type {
  AnswerResponse,
  ImportJob,
  ParsedQuestion,
  PracticeMode,
  Question,
  QuestionBank,
} from '@/types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || JSON.stringify(data)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  listBanks() {
    return request<QuestionBank[]>('/api/question-banks')
  },

  listQuestions(bankId: number, mode: Exclude<PracticeMode, 'memorize'> = 'sequence') {
    return request<Question[]>(`/api/question-banks/${bankId}/questions?mode=${mode}`)
  },

  previewImport(file: File, bankName: string) {
    const form = new FormData()
    form.append('file', file)
    form.append('bank_name', bankName)
    return request<ImportJob>('/api/imports/preview', { method: 'POST', body: form })
  },

  getImport(id: number) {
    return request<ImportJob>(`/api/imports/${id}`)
  },

  confirmImport(id: number, questions?: ParsedQuestion[]) {
    return request<ImportJob>(`/api/imports/${id}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(questions ? { questions } : {}),
    })
  },

  submitAnswer(questionId: number, answer: string[]) {
    return request<AnswerResponse>(`/api/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer }),
    })
  },

  setFavorite(questionId: number, isFavorite: boolean) {
    return request<Question>(`/api/questions/${questionId}/favorite`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_favorite: isFavorite }),
    })
  },

  exportBackup() {
    return fetch('/api/backups/export').then(async (res) => {
      if (!res.ok) throw new Error('导出失败')
      return res.blob()
    })
  },

  importBackup(file: File) {
    const form = new FormData()
    form.append('file', file)
    return request<{ banks: number; questions: number; message: string }>('/api/backups/import', {
      method: 'POST',
      body: form,
    })
  },
}
