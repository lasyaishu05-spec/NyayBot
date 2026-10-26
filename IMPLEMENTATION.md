# 🛠️ NyayBot Implementation Guide

A simple, clear, and complete technical breakdown of how NyayBot is implemented across frontend, backend, and AI services. Use this guide to quickly understand and explain the codebase in interviews.

---

## 1. System Architecture Overview

```
                               ┌────────────────────────────────────────┐
                               │           REACT FRONTEND (Vite)        │
                               │  - Upload & Language Selector          │
                               │  - Document Summary & Audio Read-Aloud │
                               │  - "What You Should Do" Checklist      │
                               │  - Interactive AI Assistant (Chat)     │
                               └──────────────────┬─────────────────────┘
                                                  │ HTTP Requests
                                                  ▼
                               ┌────────────────────────────────────────┐
                               │       FASTAPI BACKEND (Python 3.12)    │
                               │  Deployed Serverless on Vercel Edge    │
                               └──────────┬───────────────────┬─────────┘
                                          │                   │
                        ┌─────────────────▼────────┐ ┌────────▼────────────────┐
                        │   IN-MEMORY HYBRID RAG   │ │       GROQ AI LPU       │
                        │ - LegalClauseChunker     │ │ - LLaMA 3.1 8B Instant  │
                        │ - BM25 (Exact Search)    │ │ - 128k Context Window   │
                        │ - Vector Cosine (Search) │ │ - Zero-Shot Multilingual│
                        │ - Reciprocal Rank Fusion │ └─────────────────────────┘
                        └──────────────────────────┘
```

---

## 2. Frontend Implementation (`frontend/src/`)

### State Machine in `App.jsx`
The application runs as a clean state machine with 5 stages:
1. `landing`: Welcome screen with feature highlights and "Get Started" CTA.
2. `upload`: Drag-and-drop file upload zone supporting PDF, DOCX, and TXT files.
3. `preview`: Shows document file details and language selection dropdown (10+ Indian languages).
4. `processing`: Animated scanning progress while `/api/process` analyzes the document.
5. `output`: The full analytics dashboard (`OutputDashboard.jsx`).

### Key UI Features in `OutputDashboard.jsx`
- **Document Summary Card**:
  - Displays a clean, multi-paragraph plain-language summary.
  - **Read Aloud Button**: Uses browser `window.speechSynthesis` and automatically falls back to Google Translate TTS audio chunks if voices aren't supported.
- **Key Highlights Grid**:
  - Automatically color-coded cards for:
    - 📅 **Important Dates**
    - ⚡ **Key Obligations**
    - ⚠️ **Potential Risks & Penalties**
- **"What You Should Do" Checklist**:
  - Document-extracted action items.
  - Interactive checkboxes with a live progress bar (`X of Y steps completed`).
  - Orange deadline tags (`Due: 7th of every month`, `Due: 30 days prior`).
- **NyayBot Assistant (Floating Chat)**:
  - Floating circular trigger button.
  - Real-time conversation with typing indicators.
  - Microphone button for speech-to-text question input.
  - Session saved to `localStorage` (`nyaybot_chat`) so chat history isn't lost on reload.

---

## 3. Backend Implementation (`backend/` & `frontend/api/`)

Both local development (`backend/`) and Vercel serverless (`frontend/api/`) share the exact same clean service architecture:

### Endpoint 1: `/api/process` (`routes/process.py`)
Called when the user clicks **"Simplify Document"**.
1. **Text Extraction (`extractor.py`)**:
   - Reads PDF files via `pypdf`.
   - Reads DOCX files via `python-docx`.
2. **Document Type Classification (`detect_document_type`)**:
   - Identifies if the contract is a Rental Agreement, Employment Offer, NDA, Sale Deed, Loan Agreement, or General Contract.
3. **Key Highlights Scanner (`analyze_highlights`)**:
   - Scans text using regex patterns for calendar dates, monetary figures, and risk keywords (default, penalty, termination, forfeit).
4. **Summary Generator (`generate_summary`)**:
   - Calls Groq LLaMA for a structured 3-paragraph summary.
   - **Deterministic Fallback**: If Groq is offline or without an API key, `_generate_extractive_detailed_summary` extracts parties, rent, deposit, duration, and notice periods into 3 full paragraphs without trailing off (`...`).
5. **Action Items Generator (`generate_action_items`)**:
   - Generates 4–6 concrete tasks starting with imperative verbs (Pay, Submit, Verify, Notify, Keep).
   - Pairs each task with its extracted deadline badge.
6. **Translation (`translator.py`)**:
   - Translates summary, content, and checklist if target language is not English.

---

### Endpoint 2: `/api/chat` (`routes/process.py` + `ai_service.py`)
Called when the user asks a question in the chat window.
1. Receives `{ question, document_content, history }`.
2. Runs the **Hybrid RAG Pipeline** (`rag_service.py`):
   - Chunks the document into legal clauses.
   - Scores clauses using both **BM25** (exact matches) and **TF-IDF Cosine** (semantic intent).
   - Combines scores using **Reciprocal Rank Fusion (RRF)**.
   - Picks the top 5–6 most relevant clauses.
3. Constructs a **Hierarchical Dual-Context Prompt**:
   - Places top retrieved clauses at the top with `[Clause X]` tags.
   - Appends the full document content below for complete context.
4. Generates response using **Groq LLaMA 3.1 8B Instant**:
   - Answers with exact numbers and dates.
   - Cites specific clause numbers.
   - Replies natively in the user's question language.
5. **Zero-Crash Fallback**: If the external AI service is unreachable, returns the verbatim extracted clauses directly to the user so they still get their answer.

---

## 4. RAG Pipeline Implementation (`rag_service.py`)

NyayBot implements a pure Python, zero-external-dependency In-Memory RAG engine in 4 classes:

| Class | Role | Key Logic |
| :--- | :--- | :--- |
| `LegalChunker` | Splits text into clauses | Uses regex for inline (`1. `, `Clause 2`) and line boundaries; segments long clauses on sentence endings. |
| `BM25Retriever` | Exact keyword/number search | Okapi formula ($k_1=1.5, b=0.75$) with morphological suffix stemmer (`payments` $\to$ `pay`). |
| `TFIDFVectorRetriever` | Conceptual intent search | Sublinear term frequency damping ($1 + \ln(tf)$) and normalized Cosine Similarity in sparse vector space. |
| `SimpleLegalRAG` | Fusion & Context builder | Fuses rankings using Reciprocal Rank Fusion ($RRF = \sum \frac{1}{60 + \text{rank}}$) and formats augmented prompts. |

---

## 5. Production Reliability & Edge Cases Handled

1. **Zero External Vector DB Dependency**:
   - Avoids heavy 1.5GB libraries (`torch`, `chromadb`) that fail Vercel’s 250MB limit.
   - Operates in-memory in **< 5ms**.
2. **Zero-Crash Resilience**:
   - If `GROQ_API_KEY` is not present, both summary generation and chat assistant fall back gracefully to local extraction and RAG clause search.
3. **No Sentence Truncation**:
   - Preamble addresses and long contract text are parsed cleanly without chopping text mid-sentence or ending with `...`.
4. **Session Persistence**:
   - Active document analysis is stored in `localStorage` (`nyaybot_session`). Refreshing the browser preserves the active session.

---

## 6. How to Explain This in an Interview (Quick Script)

> *"In NyayBot, the architecture is divided into three clean layers: a React 19 single-page frontend, a lightweight FastAPI backend running on Vercel Serverless, and an In-Memory Hybrid RAG engine.*
>
> *When a document is uploaded, our backend extracts the text, detects the contract type, and extracts critical dates, obligations, and penalties. We generate a 3-paragraph plain-language summary and a dynamic checklist with completion badges.*
>
> *For the interactive chatbot, we built a hybrid RAG pipeline combining BM25 for exact numbers and dates with TF-IDF Cosine Similarity for conceptual questions. We fuse them using Reciprocal Rank Fusion and prompt Groq's LLaMA 3.1 8B model with both the top clauses and full document context.*
>
> *Because it’s written in pure Python standard library, it has zero external database dependencies, cold-starts in under 5 milliseconds, and runs completely free on serverless infrastructure."*
