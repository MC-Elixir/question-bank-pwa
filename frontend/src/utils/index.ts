import type { ParsedQuestion, QuestionType } from '@/types'

export function questionTypeLabel(type: QuestionType | string): string {
  const map: Record<string, string> = {
    single_choice: '单选',
    multiple_choice: '多选',
    judgment: '判断',
    unknown: '未知',
  }
  return map[type] || type
}

export function classifyImportQuestion(q: ParsedQuestion): 'duplicate' | 'failed' | 'abnormal' | 'normal' {
  if (q.duplicate_of != null) return 'duplicate'
  if (!q.stem?.trim() || q.question_type === 'unknown') return 'failed'
  if (q.needs_review || (q.issues && q.issues.length > 0)) return 'abnormal'
  return 'normal'
}

export function importStats(questions: ParsedQuestion[]) {
  const stats = { normal: 0, abnormal: 0, failed: 0, duplicate: 0, total: questions.length }
  for (const q of questions) {
    stats[classifyImportQuestion(q)] += 1
  }
  return stats
}

export function formatAnswer(answer?: string[] | null): string {
  if (!answer || answer.length === 0) return '—'
  return answer.join('')
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
