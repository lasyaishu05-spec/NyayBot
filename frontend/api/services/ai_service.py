import os
import json
from dotenv import load_dotenv

load_dotenv()

_groq_client = None
_groq_available = False


def _init_groq():
    """Try to initialize Groq client. Returns True if successful."""
    global _groq_client, _groq_available

    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key or api_key == "your_groq_api_key_here":
        print("[NyayBot] No valid GROQ_API_KEY found. AI simplification will be skipped.")
        _groq_available = False
        return False

    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        _groq_available = True
        print("[NyayBot] Groq AI client initialized successfully.")
        return True
    except Exception as e:
        print(f"[NyayBot] Failed to initialize Groq client: {e}")
        _groq_available = False
        return False


# Try to initialize on import
_init_groq()


# ─── HELPER ──────────────────────────────────────────────────────────────────

def _groq_call(system_prompt, user_prompt, temperature=0.3, max_tokens=1024):
    """Shared helper for Groq API calls. Returns response text or None on failure."""
    global _groq_available, _groq_client

    if not _groq_available or _groq_client is None:
        return None

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        print(f"[NyayBot] Groq API error: {error_msg}")
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            print("[NyayBot] API key is invalid. Switching to fallback mode.")
            _groq_available = False
        return None


# ─── DOCUMENT TYPE DETECTION ─────────────────────────────────────────────────

def detect_document_type(text):
    """
    Detect the type of legal document from its text.
    Returns dict with 'type' and 'confidence'.
    """
    snippet = text[:2000]

    system_prompt = (
        "You are a document classifier for Indian legal documents. "
        "Analyze the text and identify the document type. "
        "Respond with ONLY a JSON object (no markdown, no extra text), like:\n"
        '{"type": "Rental Agreement", "confidence": "high"}\n\n'
        "Common types: Rental Agreement, Court Notice, Property Deed, "
        "Loan Document, Employment Contract, Power of Attorney, Affidavit, "
        "Sale Agreement, Will/Testament, Legal Notice, FIR Copy, "
        "Partnership Deed, Insurance Policy, Divorce Petition, Bail Application.\n"
        "Confidence can be: high, medium, or low."
    )

    result = _groq_call(system_prompt, f"Classify this document:\n\n{snippet}", temperature=0.1, max_tokens=100)

    if result:
        try:
            # Try to parse JSON from the response
            cleaned = result.strip()
            # Handle cases where AI wraps in markdown code blocks
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(cleaned)
            return {
                "type": parsed.get("type", "Legal Document"),
                "confidence": parsed.get("confidence", "medium"),
            }
        except (json.JSONDecodeError, Exception) as e:
            print(f"[NyayBot] Doc type parse error: {e}, raw: {result}")
            # Try to extract type from plain text
            return {"type": result.strip()[:50], "confidence": "low"}

    return {"type": "Legal Document", "confidence": "low"}


# ─── KEY HIGHLIGHTS / RISK FLAGS ─────────────────────────────────────────────

def analyze_highlights(text):
    """
    Extract key highlights: important dates, obligations, and risks.
    Returns dict with 'dates', 'obligations', 'risks' lists.
    """
    snippet = text[:4000]

    system_prompt = (
        "You are a legal document analyzer for Indian citizens. "
        "Extract key highlights from the document. "
        "Respond with ONLY a JSON object (no markdown, no extra text), like:\n"
        '{"dates": ["Rent due by 5th of every month", "Agreement expires 31 March 2025"], '
        '"obligations": ["Pay monthly rent of Rs. 22,000", "Maintain the property in good condition"], '
        '"risks": ["Late payment penalty of 2% per week", "Agreement auto-renews if not terminated 60 days before"]}\n\n'
        "Rules:\n"
        "- Each item should be a short, clear sentence in plain language\n"
        "- Maximum 5 items per category\n"
        "- If no items found for a category, use an empty list\n"
        "- Be specific with amounts, dates, and names when available\n"
        "- For risks, phrase gently (e.g., 'You may need to...' not 'YOU MUST...')\n"
        "- Always add important disclaimer context"
    )

    result = _groq_call(system_prompt, f"Extract highlights from this document:\n\n{snippet}", temperature=0.2, max_tokens=800)

    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(cleaned)
            return {
                "dates": parsed.get("dates", [])[:5],
                "obligations": parsed.get("obligations", [])[:5],
                "risks": parsed.get("risks", [])[:5],
            }
        except (json.JSONDecodeError, Exception) as e:
            print(f"[NyayBot] Highlights parse error: {e}, raw: {result}")

    return {"dates": [], "obligations": [], "risks": []}


# ─── SUMMARY GENERATION ─────────────────────────────────────────────────────

def generate_summary(text, mode="short"):
    """
    Generate a summary of the document.
    mode='short' → 3-5 bullet points
    mode='detailed' → full paragraph explanation
    """
    snippet = text[:4000]

    if mode == "short":
        system_prompt = (
            "You are a legal document simplifier for Indian citizens. "
            "Create a SHORT summary with exactly 3 to 5 bullet points. "
            "Each bullet should be one clear, simple sentence. "
            "Include the most critical information: who, what, when, how much. "
            "Format: Start each bullet with '• ' (bullet character and space). "
            "Do NOT add any intro text, just the bullets."
        )
    else:
        system_prompt = (
            "You are a legal document simplifier for Indian citizens. "
            "Create a DETAILED summary in 2-3 paragraphs. "
            "Explain what the document is about, who the parties are, "
            "what the key terms and conditions are, important dates and amounts, "
            "and what the user should be aware of. "
            "Use simple, clear language that anyone can understand. "
            "Do NOT add legal advice."
        )

    result = _groq_call(system_prompt, f"Summarize this legal document:\n\n{snippet}", temperature=0.3, max_tokens=600)

    if result:
        return result

    # Fallback
    if mode == "short":
        return "• This is a legal document that requires your attention.\n• Please read the simplified content below for details.\n• Consult a lawyer if you have concerns."
    else:
        return text[:500] + "..." if len(text) > 500 else text


# ─── TEXT SIMPLIFICATION ─────────────────────────────────────────────────────

def simplify_text(chunk):
    """
    Simplify legal text into plain, simple language.
    Falls back to basic text cleanup if Groq API is unavailable.
    """
    system_prompt = (
        "You are a legal document simplifier for Indian citizens. "
        "Take complex legal text and rewrite it in simple, clear language "
        "that anyone can understand. Keep important details like dates, "
        "amounts, names, and obligations. Use short sentences and bullet points "
        "where appropriate. Do NOT add legal advice."
    )

    result = _groq_call(system_prompt, f"Simplify this legal text into plain language:\n\n{chunk}")

    return result if result else _basic_simplify(chunk)


def _basic_simplify(text):
    """Basic text cleanup when AI is not available."""
    if not text:
        return ""
    lines = text.strip().split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n\n".join(cleaned_lines)


# ─── DOCUMENT CHAT ───────────────────────────────────────────────────────────

def chat_with_document(question, document_content, history=None):
    """
    Answer a user's question about the document using Groq AI.
    Falls back to a helpful message if AI is not available.
    """
    global _groq_available, _groq_client

    if not _groq_available or _groq_client is None:
        return _basic_chat_fallback(question)

    # Truncate document content if too long
    doc_context = document_content[:6000] if len(document_content) > 6000 else document_content

    messages = [
        {
            "role": "system",
            "content": (
                "You are NyayBot, a helpful legal document assistant for Indian citizens. "
                "You have been given a legal document that was uploaded by the user. "
                "Answer the user's questions about the document in simple, clear language. "
                "Be specific and refer to details from the document when possible. "
                "If the document doesn't contain information to answer the question, say so honestly. "
                "Keep answers concise but thorough. Do NOT provide legal advice — "
                "instead suggest consulting a lawyer for complex legal decisions.\n\n"
                "VERY IMPORTANT LANGUAGE RULE: You MUST detect the language of the user's question "
                "and ALWAYS reply in that SAME language. For example:\n"
                "- If user asks in Hindi, reply entirely in Hindi.\n"
                "- If user asks in Telugu, reply entirely in Telugu.\n"
                "- If user asks in Tamil, reply entirely in Tamil.\n"
                "- If user asks in Kannada, reply entirely in Kannada.\n"
                "- If user asks in Bengali, reply entirely in Bengali.\n"
                "- If user asks in Marathi, reply entirely in Marathi.\n"
                "- If user asks in Gujarati, reply entirely in Gujarati.\n"
                "- If user asks in Malayalam, reply entirely in Malayalam.\n"
                "- If user asks in Punjabi, reply entirely in Punjabi.\n"
                "- If user asks in Urdu, reply entirely in Urdu.\n"
                "- If user asks in Odia, reply entirely in Odia.\n"
                "- If user asks in English, reply in English.\n"
                "- For any other language, reply in that same language.\n"
                "Never mix languages in your response. Match the user's language exactly.\n\n"
                f"=== DOCUMENT CONTENT ===\n{doc_context}\n=== END DOCUMENT ==="
            )
        }
    ]

    # Add conversation history
    if history:
        for msg in history:
            role = "assistant" if msg.role == "ai" else "user"
            messages.append({"role": role, "content": msg.text})

    # Add the current question
    messages.append({"role": "user", "content": question})

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = str(e)
        print(f"[NyayBot] Groq chat API error: {error_msg}")
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            _groq_available = False
        return _basic_chat_fallback(question)


def _basic_chat_fallback(question):
    """Fallback response when AI is not available."""
    return (
        "I'm sorry, the AI service is currently unavailable. "
        "Please review the simplified document above for your answer, "
        "or try again in a moment. For specific legal questions, "
        "we recommend consulting a qualified lawyer."
    )