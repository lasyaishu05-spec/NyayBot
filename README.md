# ⚖️ NyayBot: Legal Clarity for Every Citizen

**NyayBot** is an AI-powered legal document simplifier designed to bridge the gap between complex legal jargon and common understanding. Created for the Hackathon, it empowers citizens to understand what they are signing, in their own language.

## 🚀 Vision
Legal documents in India are often dense, overwhelming, and written in English, which can lead to exploitation and confusion. NyayBot simplifies these documents into plain language and translates them into **10+ Indian regional languages**, complete with AI-driven insights and voice assistance.

## ✨ Key Features
- **📄 AI Document Simplification**: Breaks down complex clauses into easy-to-read paragraphs.
- **🌍 Multi-Lingual Support**: Supports 10+ Indian languages (Hindi, Telugu, Tamil, Marathi, etc.).
- **💬 Interactive AI Chat**: Ask questions directly about your uploaded document (e.g., "What is the notice period?").
- **📅 Key Highlights**: Automatically extracts important dates, obligations, and risks.
- **🔊 Voice Assistance (TTS)**: Listen to the simplified document in your native language.
- **🎙️ Voice Input**: Ask your questions using your voice.
- **📋 Action Checklist**: A clear list of what you should do next after reading the document.

## 🛠️ Tech Stack
- **Frontend**: React, Vite, CSS3 (Glassmorphism & Professional UI)
- **Backend**: FastAPI (Python), Groq API (LLaMA 3.1-8b-instant)
- **PDF Extraction**: PyMuPDF
- **Cloud Hosting**: Vercel (Frontend), Render (Backend)

## 🏗️ Architecture
1. **Upload**: User uploads a legal document (PDF/Image).
2. **Extraction**: Backend extracts raw text and detects the document type.
3. **AI Analysis**: Groq-powered AI generates summaries, highlights, and simplifications.
4. **Translation**: If a regional language is selected, the analysis is translated.
5. **Interactive UI**: Result is displayed with an integrated chat for deep-diving into clauses.

---

### 👨‍💻 Developed for [Hackathon Name]
Helping bring Legal Literacy to Bharat.
