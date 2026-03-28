# ⚖️ NyayBot: Legal Document Simplifier

NyayBot is an AI-powered legal assistant designed to decode complex legal jargon into plain, understandable language. It supports **12+ Indian languages**, making legal clarity accessible to every citizen.

## 🚀 Features

- **Document Simplification**: Upload Rent Agreements, Court Notices, and more to get instant summaries.
- **Multilingual Support**: Analysis and chat available in Hindi, Telugu, Tamil, Kannada, and more.
- **AI Chat Assistant**: Ask follow-up questions about your specific legal document.
- **Key Highlights**: Automatic extraction of important dates, obligations, and risks.
- **Privacy First**: All analyses are session-based (anonymous) and processed securely.

## 🛠️ Project Structure

- `/frontend`: React + Vite application with a premium, responsive UI.
- `/backend`: FastAPI server integrated with the Groq LLaMA 3.1-8b-instant LLM.

## ⚙️ Setup & Installation

### 1. Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- Firebase Account (for app configuration)
- Groq API Key (for LLM processing)

### 2. Frontend Setup
```bash
cd frontend
npm install
```
Create a `.env` file in the `frontend` directory with your Firebase config:
```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

### 3. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```
Create a `.env` file in the `backend` directory:
```env
GROQ_API_KEY=your_groq_api_key
```

### 4. Running the App
- **Backend**: `python -m uvicorn app:app --reload`
- **Frontend**: `npm run dev`

## 🛡️ Security Note
This repository includes a `.gitignore` to protect your sensitive API keys. **Never** commit your `.env` files to GitHub.

## ⚖️ Disclaimer
NyayBot provides AI-generated legal analysis for informational purposes only. It is **not** a substitute for professional legal advice. Always consult with a qualified legal professional.
