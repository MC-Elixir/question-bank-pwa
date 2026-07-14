import mammoth from 'mammoth'
import type { AnswerResponse, ImportJob, ParsedQuestion, PracticeMode, Question, QuestionBank } from '@/types'

type StoredBank = QuestionBank & { questions: Question[] }
const DB = 'offline-question-bank'
const STORE = 'banks'

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: 'id' })
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}
async function allBanks(): Promise<StoredBank[]> {
  const db = await openDb()
  return new Promise((resolve, reject) => { const r = db.transaction(STORE).objectStore(STORE).getAll(); r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error) })
}
async function saveBank(bank: StoredBank) {
  const db = await openDb()
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    const r = tx.objectStore(STORE).put(bank)
    let settled = false
    const fail = (error: unknown) => { if (!settled) { settled = true; reject(error instanceof Error ? error : new Error('IndexedDB 写入失败')) } }
    r.onsuccess = () => { if (!settled) { settled = true; resolve() } }
    r.onerror = () => fail(r.error)
    tx.onerror = () => fail(tx.error)
    tx.onabort = () => fail(tx.error || new Error('IndexedDB 事务被中止'))
  })
}
function parseText(text: string): ParsedQuestion[] {
  const lines = text.split(/\r?\n/).map(x => x.replace(/\s+$/,'').trim()).filter(Boolean)
  const result: ParsedQuestion[] = []; let current: ParsedQuestion | null = null; let section = ''
  const push = () => { if (current) { if (!current.answer?.length) current.needs_review = true; result.push(current) }; current = null }
  for (const line of lines) {
    if (/^(第\s*\d+\s*[章节]|[一二三四五六七八九十]+、)/.test(line) && !/^\d+[.、]/.test(line)) { section = line; continue }
    const q = line.match(/^(\d+)[.、．)]\s*(.*)$/)
    if (q) { push(); current = { chapter: section || null, question_type: 'single_choice', stem: q[2], options: [], answer: [], explanation: null, source_order: result.length + 1 }; continue }
    if (!current) continue
    const opt = line.match(/^([A-H])[.、．)\s]+(.+)$/i)
    if (opt) { current.options.push({ label: opt[1].toUpperCase(), content: opt[2], sort_order: current.options.length }); continue }
    const ans = line.match(/^(?:答案|正确答案)\s*[:：]?\s*(.+)$/i)
    if (ans) { const a = ans[1].trim(); current.answer = /^(对|错|正确|错误|√|×)$/.test(a) ? [a] : a.toUpperCase().match(/[A-H]/g) || []; current.question_type = current.answer.length > 1 ? 'multiple_choice' : 'single_choice'; continue }
    const exp = line.match(/^(?:解析|答案解析)\s*[:：]?\s*(.*)$/i)
    if (exp) { current.explanation = exp[1] || null; continue }
    if (!current.options.length) current.stem += line
  }
  push(); return result.map(q => ({ ...q, issues: q.needs_review ? ['未识别到答案，请人工确认'] : [] }))
}
let importCache = new Map<number, ImportJob>()
const IMPORT_SESSION_KEY = 'question-bank-pending-import'
function persistImport(job: ImportJob) {
  importCache.set(job.id, job)
  sessionStorage.setItem(`${IMPORT_SESSION_KEY}:${job.id}`, JSON.stringify(job))
}
function readPersistedImport(id: number): ImportJob | null {
  const raw = sessionStorage.getItem(`${IMPORT_SESSION_KEY}:${id}`)
  if (!raw) return null
  try { return JSON.parse(raw) as ImportJob } catch { return null }
}
export const api = {
  async listBanks(): Promise<QuestionBank[]> { return (await allBanks()).map(({ questions, ...b }) => b).sort((a,b) => b.updated_at.localeCompare(a.updated_at)) },
  async listQuestions(bankId: number, mode: Exclude<PracticeMode,'memorize'> = 'sequence') { const b = (await allBanks()).find(x => x.id === bankId); let q = [...(b?.questions || [])]; if (mode === 'random') q.sort(() => Math.random() - .5); if (mode === 'wrong') q = q.filter(x => x.is_wrong); if (mode === 'favorite') q = q.filter(x => x.is_favorite); if (mode === 'unanswered') q = q.filter(x => !x.answered); return q },
  async previewImport(file: File, bankName: string) {
    if (!file || !file.name.toLowerCase().endsWith('.docx')) throw new Error('仅支持 .docx 文件，不支持 .doc 文件')
    if (!file.size) throw new Error('文件为空，请重新选择 .docx 文件')
    console.info('[题库导入] 开始本地解析', { name: file.name, size: file.size, type: file.type })
    try {
      const arrayBuffer = await file.arrayBuffer()
      const { value } = await mammoth.extractRawText({ arrayBuffer })
      if (!value.trim()) throw new Error('Word 中没有可读取的文本内容')
      const questions = parseText(value)
      if (!questions.length) throw new Error('未识别到题目，请检查题目是否以“1.”、“1、”等格式开头')
      console.info('[题库导入] 文本提取完成', { characters: value.length, questions: questions.length })
      const job: ImportJob = { id: Date.now(), bank_name: bankName, status: 'preview', source_filename: file.name, question_count: questions.length, error_count: questions.filter(x => x.needs_review).length, questions, created_at: new Date().toISOString() }
      persistImport(job)
      return job
    } catch (error) {
      console.error('[题库导入] 本地解析失败', error)
      if (error instanceof Error && (error.message.includes('Word') || error.message.includes('题目'))) throw error
      throw new Error('无法读取该 Word 文件，可能已损坏或格式不受支持')
    }
  },
  async getImport(id: number) {
    const j = importCache.get(id) || readPersistedImport(id)
    if (!j) throw new Error('导入任务不存在，请返回重新选择 Word 文件')
    importCache.set(id, j)
    return j
  },
  async confirmImport(id: number, questions?: ParsedQuestion[]) {
    const j = await this.getImport(id)
    const qs = questions || j.questions
    if (!qs.length) throw new Error('没有可入库的题目')
    const now = new Date().toISOString(); const bankId = Date.now()
    const bank: StoredBank = { id: bankId, name: j.bank_name, description: j.source_filename, question_count: qs.length, created_at: now, updated_at: now, questions: qs.map((q, i) => ({ ...q, id: bankId + i, bank_id: bankId, source_order: i + 1, needs_review: !!q.needs_review, is_favorite: false, is_wrong: false, answered: false })) }
    console.info('[题库导入] 开始写入 IndexedDB', { bankId, questions: qs.length })
    try {
      await saveBank(bank)
      console.info('[题库导入] IndexedDB 写入完成', { bankId, questions: qs.length })
    } catch (error) {
      console.error('[题库导入] IndexedDB 写入失败', error)
      throw new Error('题库保存失败，请检查浏览器是否允许本地存储后重试')
    }
    const done = { ...j, status: 'confirmed', bank_id: bankId }; importCache.set(id, done); sessionStorage.removeItem(`${IMPORT_SESSION_KEY}:${id}`); return done
  },
  async submitAnswer(id: number, answer: string[]): Promise<AnswerResponse> { const banks = await allBanks(); const b = banks.find(x => x.questions.some(q => q.id === id)); const q = b?.questions.find(x => x.id === id); if (!b || !q) throw new Error('题目不存在'); const correct = JSON.stringify([...(q.answer || [])].sort()) === JSON.stringify([...answer].sort()); q.answered = true; q.is_wrong = !correct; await saveBank({ ...b, updated_at: new Date().toISOString() }); return { is_correct: correct, correct_answer: q.answer, explanation: q.explanation } },
  async setFavorite(id: number, isFavorite: boolean) { const banks = await allBanks(); const b = banks.find(x => x.questions.some(q => q.id === id)); const q = b?.questions.find(x => x.id === id); if (!b || !q) throw new Error('题目不存在'); q.is_favorite = isFavorite; await saveBank(b); return q },
  async exportBackup() { const blob = new Blob([JSON.stringify({ version: 1, exported_at: new Date().toISOString(), banks: await allBanks() }, null, 2)], { type: 'application/json' }); return blob },
  async importBackup(file: File) { const data = JSON.parse(await file.text()); for (const bank of data.banks || []) await saveBank(bank); return { banks: data.banks?.length || 0, questions: (data.banks || []).reduce((n: number,b: StoredBank) => n + b.questions.length, 0), message: '备份已恢复' } },
}
