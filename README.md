# 🎓 Sunmarke School AI Voice Agent

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> A full-stack AI Voice Agent for Sunmarke School — built with RAG pipeline, real-time streaming LLM responses, voice input, and clickable source links.

---

## 📸 Screenshots

> Replace the placeholders below with actual screenshots from your running app.

| Home Page | Voice Recording | Streaming Response |
|-----------|----------------|-------------------|
| ![Home](docs/screenshots/home.png) | ![Recording](docs/screenshots/recording.png) | ![Response](docs/screenshots/response.png) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
│              🎤 Voice / ⌨️  Text Input                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  NEXT.JS FRONTEND                            │
│                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────┐    │
│  │  VoiceRecorder  │    │       ResponseCard x2        │    │
│  │  Web Speech API │    │  Streaming tokens word by    │    │
│  │  Resume support │    │  word + clickable links      │    │
│  └────────┬────────┘    └──────────────────────────────┘    │
└───────────┼─────────────────────────────────────────────────┘
            │  POST /api/query/stream (SSE)
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                            │
│                                                              │
│  ┌──────────────┐   ┌─────────────┐   ┌─────────────────┐  │
│  │  RAG Service │   │  Embeddings │   │   LLM Service   │  │
│  │              │   │             │   │                 │  │
│  │ retrieve top │   │ sentence-   │   │ Groq Llama 3.3  │  │
│  │ 8 chunks by  │──▶│ transformers│   │ 70B  (stream)   │  │
│  │ cosine sim   │   │ all-MiniLM  │   │                 │  │
│  └──────────────┘   └─────────────┘   │ Groq Gemma2 9B  │  │
│                                        │ (stream)        │  │
│                                        └─────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  SQLite Database                      │   │
│  │   Documents (47) │ Chunks (211) │ Query Logs         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│              GROQ API  (free tier)                           │
│   llama-3.3-70b-versatile  +  gemma2-9b-it                  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- 🎤 **Voice Input** — Web Speech API with resume support (stop & continue without losing transcript)
- ⚡ **Streaming Responses** — Words appear token by token in real time from both models simultaneously
- 🔍 **RAG Pipeline** — Scraped 47 Sunmarke School pages, chunked into 211 segments, semantic search with cosine similarity
- 🔗 **Clickable Source Links** — Every answer includes the source URL from the school website
- 🔊 **Text-to-Speech** — Listen to responses, URLs are automatically skipped during playback
- 📊 **Stats Dashboard** — Live count of documents, chunks, and queries processed
- 🆓 **Fully Free** — sentence-transformers for embeddings (local), Groq for LLMs (free tier)

---

## 🗂️ Project Structure

```
AI Voice Agent/
├── backend/
│   ├── main.py              # FastAPI app, REST + streaming endpoints
│   ├── rag_service.py       # RAG pipeline, embeddings, retrieval
│   ├── llm_service.py       # Groq LLM integration
│   ├── database.py          # SQLAlchemy models, SQLite/PostgreSQL
│   ├── requirements.txt
│   └── .env                 # API keys (not committed)
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main page with streaming state
│   │   └── layout.tsx
│   ├── components/
│   │   ├── VoiceRecorder.tsx  # Mic input with resume support
│   │   └── ResponseCard.tsx   # Streaming display + TTS + links
│   └── utils/
│       └── api.ts           # streamQuery(), healthCheck(), getStats()
│
├── render.yaml              # Render deployment config
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env`:
```env
GROQ_API_KEY=your_groq_key_here
DATABASE_URL=sqlite:///./sunmarke_ai.db
PORT=8000
ENV=development
```

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 🧠 How the RAG Pipeline Works

```
1. SCRAPE    →  47 pages scraped from sunmarke.com
                                │
2. CHUNK     →  211 overlapping text chunks (1000 chars, 200 overlap)
                                │
3. EMBED     →  sentence-transformers all-MiniLM-L6-v2 (384-dim, local, free)
                                │
4. STORE     →  SQLite with JSON-serialized embeddings
                                │
5. QUERY     →  User question → embed → cosine similarity → top 8 chunks
                                │
6. PROMPT    →  Chunks + source URLs injected into LLM prompt
                                │
7. STREAM    →  Groq streams tokens back → frontend renders word by word
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check |
| POST | `/api/query` | Full response (non-streaming) |
| POST | `/api/query/stream` | **Streaming SSE response** |
| GET | `/api/stats` | Document/chunk/query counts |
| POST | `/api/initialize` | Re-index documents |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Search | Cosine similarity (NumPy) |
| Database | SQLite (dev) / PostgreSQL + pgvector (prod) |
| LLMs | Groq — LLaMA 3.3 70B + Gemma2 9B |
| Streaming | Server-Sent Events (SSE) |
| Voice | Web Speech API |

---

## 👤 Author

**Imran Rafique**
GitHub: [@imranrafique9898-stack](https://github.com/imranrafique9898-stack)

---

*Built as part of XPLServices AI Engineer Technical Assessment*
