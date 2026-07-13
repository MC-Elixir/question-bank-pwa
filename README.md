# 个人题库 PWA

本地优先的个人刷题应用：导入 Word 题库 → 校对入库 → 顺序/随机/错题/收藏练习 → JSON 备份导出。  
技术栈：FastAPI + SQLite（后端）、Vue 3 + Vant 4 + Vite PWA（前端）、Docker Compose 一键部署。

方案文档见根目录：`个人题库PWA产品与技术方案_v1.0.docx`。

---

## 目录结构

```
题库/
├── backend/          # FastAPI API
├── frontend/         # Vue 3 PWA
├── nginx/nginx.conf  # 生产反代：静态页 + /api → backend
├── docker-compose.yml
└── README.md
```

---

## 本地开发启动

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API 文档：http://127.0.0.1:8000/docs  
- 健康检查：http://127.0.0.1:8000/api/health  
- SQLite 数据目录：`backend/data/`

运行测试：

```bash
cd backend
pytest -q
```

### 前端

需要 **Node.js ≥ 20**（推荐 22；Vite 8 不支持 Node 18）。

```bash
cd frontend
npm install
npm run dev
```

- 开发地址：http://localhost:5173  
- Vite 已将 `/api` 代理到 `http://127.0.0.1:8000`  
- 生产构建：`npm run build`

CORS 已允许：`localhost:5173` / `127.0.0.1:5173` / `localhost` / `127.0.0.1`（`allow_credentials=True`）。

---

## Docker 部署

一键构建并启动（前端 Nginx 监听 80，`/api` 反代到 backend:8000）：

```bash
docker compose up --build
```

访问：http://localhost  

停止：

```bash
docker compose down
```

数据卷：`backend-data` 挂载到容器内 `/app/data`（SQLite 与上传文件持久化）。

---

## Word 模板格式

导入仅支持 `.docx`。推荐按下列结构书写（解析器对常见变体有容错）：

```
第一章 某某章节

1. 单选题题干……
A. 选项一
B. 选项二
C. 选项三
D. 选项四
答案：A
解析：……

2. 多选题题干……
A. …
B. …
C. …
答案：AB
解析：……

3. 判断题题干……
答案：对
解析：……
```

约定说明：

| 元素 | 推荐写法 | 备注 |
|------|----------|------|
| 章节 | `第X章 …` 或 `一、…` | 可选，继承到后续题目 |
| 题号 | `1.` / `1、` / `（1）` / `第1题` | 题干可跨多行 |
| 选项 | `A.` / `A、` / `（A）` | 判断题可无选项 |
| 答案 | `答案：A` / `正确答案：AB` / `答案：【对】` | 多选写多个字母 |
| 解析 | `解析：…` / `答案解析：…` | 可选 |

导入流程：上传预览 → 校对异常题 → 确认入库。样例文件：`backend/tests/fixtures/*.docx`。

---

## 主要 API（字段约定）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/imports/preview` | `multipart`: `file` + `bank_name` |
| POST | `/api/imports/{id}/confirm` | 可选 body `{ questions }`；响应含 `bank_id` |
| GET | `/api/question-banks` | 题库列表 |
| GET | `/api/question-banks/{id}/questions?mode=` | `sequence\|random\|wrong\|favorite\|unanswered` |
| POST | `/api/questions/{id}/answer` | body: `{ "answer": ["A"] }` |
| PUT | `/api/questions/{id}/favorite` | body: `{ "is_favorite": true }` |
| GET | `/api/backups/export` | 导出 JSON |
| POST | `/api/backups/import` | 导入备份 JSON |

题目字段：`stem`、`question_type`、`options[{label,content}]`、`answer`、`explanation`、`is_favorite` 等（与后端 `schemas.py` 一致）。

---

## 验收清单（对照方案）

- [x] Word 导入预览 + 异常题校对 + 确认入库（返回 `bank_id`）
- [x] 题库列表与题目拉取（顺序 / 随机 / 未做 / 错题 / 收藏）
- [x] 答题判分、错题标记、收藏切换
- [x] 背题模式（前端展示答案与解析）
- [x] JSON 备份导出 / 导入
- [x] 移动端 PWA 前端（Vant）
- [x] 本地开发前后端可联调（Vite 代理 + CORS）
- [x] Docker Compose 一键部署（Nginx 静态 + `/api` 反代）
- [x] 后端 pytest、前端 `npm run build` 可通过

---

## 许可证

个人学习项目，按需使用。
