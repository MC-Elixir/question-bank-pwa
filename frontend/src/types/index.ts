export type QuestionType = 'single_choice' | 'multiple_choice' | 'judgment' | 'unknown'
export type PracticeMode = 'sequence' | 'random' | 'wrong' | 'favorite' | 'unanswered' | 'memorize'

export interface OptionItem {
  label: string
  content: string
  sort_order?: number
}

export interface ParsedQuestion {
  chapter?: string | null
  question_type: QuestionType
  stem: string
  options: OptionItem[]
  answer?: string[] | null
  explanation?: string | null
  source_order?: number
  needs_review?: boolean
  issues?: string[]
  content_hash?: string | null
  duplicate_of?: number | null
}

export interface ImportJob {
  id: number
  bank_name: string
  status: string
  source_filename?: string | null
  question_count: number
  error_count: number
  questions: ParsedQuestion[]
  created_at: string
  bank_id?: number | null
}

export interface QuestionBank {
  id: number
  name: string
  description?: string | null
  question_count: number
  created_at: string
  updated_at: string
}

export interface BankWithStats extends QuestionBank {
  answered: number
  wrong: number
  favorite: number
  accuracy: number
  progress: number
}

export interface Question {
  id: number
  bank_id: number
  chapter?: string | null
  question_type: QuestionType
  stem: string
  options: OptionItem[]
  answer?: string[] | null
  explanation?: string | null
  source_order: number
  needs_review: boolean
  is_favorite: boolean
  is_wrong: boolean
  answered: boolean
}

export interface AnswerResponse {
  is_correct: boolean
  correct_answer?: string[] | null
  explanation?: string | null
}

export type ImportFilter = 'all' | 'normal' | 'abnormal' | 'failed' | 'duplicate'
