import os
import re
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

    # Fallback: extract highlights via regex from the document
    return _extract_regex_highlights(text)


def _extract_regex_highlights(text):
    """Regex fallback to extract dates, obligations, and risks when AI is unavailable."""
    if not text:
        return {"dates": [], "obligations": [], "risks": []}

    dates = []
    # Dates & Deadlines patterns
    date_patterns = [
        r'(?:due\s+(?:on|by)|payable\s+(?:on|by)|on\s+or\s+before|valid\s+until|expires?\s+on|within\s+\d+\s+(?:days|months)|prior\s+written\s+notice\s+of\s+\d+\s+days)[^\n\.\;]{3,50}',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{2,4}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    ]
    for pat in date_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            clean = match.group(0).strip()
            if clean not in dates and len(clean) > 4:
                dates.append(clean)
            if len(dates) >= 5:
                break
        if len(dates) >= 5:
            break

    # Obligations patterns (shall, must, agreed to)
    obligations = []
    ob_patterns = [
        r'(?:tenant|landlord|borrower|lender|employee|employer|party|purchaser)\s+(?:shall|agrees?\s+to|must|undertakes?\s+to)\s+[^\n\.\;]{10,80}',
    ]
    for pat in ob_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            clean = match.group(0).strip()
            if clean not in obligations:
                obligations.append(clean)
            if len(obligations) >= 4:
                break

    # Risks patterns (penalty, default, breach, forfeit)
    risks = []
    risk_patterns = [
        r'(?:penalty|interest|default|breach|forfeit|liquidated\s+damages|evict|termination)[^\n\.\;]{10,80}',
    ]
    for pat in risk_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            clean = match.group(0).strip()
            if clean not in risks:
                risks.append(clean)
            if len(risks) >= 4:
                break

    return {
        "dates": dates[:5],
        "obligations": obligations[:5],
        "risks": risks[:5],
    }


# ─── ACTION ITEMS GENERATION ("WHAT YOU SHOULD DO") ──────────────────────────

def generate_action_items(text, highlights=None, doc_type="Legal Document"):
    """
    Generate tailored, document-grounded action items for "What You Should Do".
    Extracts dates, deadlines, payments, and key obligations from the document.
    Returns a list of dicts: [{"text": str, "deadline": Optional[str]}].
    """
    snippet = text[:4000] if text else ""
    dates_context = json.dumps(highlights.get("dates", [])) if highlights else "[]"
    obligations_context = json.dumps(highlights.get("obligations", [])) if highlights else "[]"
    risks_context = json.dumps(highlights.get("risks", [])) if highlights else "[]"

    system_prompt = (
        "You are a legal assistant for Indian citizens. "
        "Extract actionable steps for the 'What You Should Do' checklist from this legal document. "
        "Focus on critical deadlines, dates, payments, renewals, notices, and compliance obligations. "
        "Respond with ONLY a JSON array of objects (no markdown, no extra text), like:\n"
        '[\n'
        '  {"text": "Pay monthly rent of Rs. 25,000 to the landlord", "deadline": "5th of every month"},\n'
        '  {"text": "Serve written termination notice if planning to vacate", "deadline": "30 days prior"},\n'
        '  {"text": "Inspect premises and report minor damages", "deadline": "Within 7 days of move-in"},\n'
        '  {"text": "Ensure full security deposit refund upon lease end", "deadline": "31 March 2025"},\n'
        '  {"text": "Keep a signed and stamped copy of this agreement", "deadline": null}\n'
        ']\n\n'
        "Rules:\n"
        "- Generate between 4 and 6 concrete, practical steps\n"
        "- 'deadline' MUST contain the specific date, day, month, notice period, or timeline if found in the document, or null if none\n"
        "- Each 'text' must start with an active imperative verb (Pay, Submit, Verify, Notify, Keep, File, Check)\n"
        "- Do NOT use vague generic steps if specific details exist in the document"
    )

    user_prompt = (
        f"Document Type: {doc_type}\n"
        f"Extracted Dates: {dates_context}\n"
        f"Extracted Obligations: {obligations_context}\n"
        f"Extracted Risks: {risks_context}\n\n"
        f"Document Content Snippet:\n{snippet}"
    )

    result = _groq_call(system_prompt, user_prompt, temperature=0.2, max_tokens=600)

    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                normalized = []
                for item in parsed[:6]:
                    if isinstance(item, dict) and "text" in item:
                        normalized.append({
                            "text": str(item["text"]).strip(),
                            "deadline": str(item["deadline"]).strip() if item.get("deadline") else None
                        })
                    elif isinstance(item, str):
                        normalized.append({"text": item.strip(), "deadline": None})
                if normalized:
                    return normalized
        except Exception as e:
            print(f"[NyayBot] Action items parse error: {e}, raw: {result}")

    # Fallback: Build action items from extracted highlights and regex
    return _build_fallback_actions(text, highlights, doc_type)


def _build_fallback_actions(text, highlights=None, doc_type="Legal Document"):
    """Dynamically build action items from extracted dates, obligations, and text patterns."""
    actions = []
    seen_texts = set()

    # 1. Dates / Deadlines from highlights
    if highlights and highlights.get("dates"):
        for date_item in highlights["dates"][:3]:
            # Look for explicit timing phrases or date expressions
            timing_match = re.search(
                r'(?:due\s+(?:by|on)|on\s+or\s+before|before|by|within|until|expires?\s+on)\s+([^\,\.]+)',
                date_item,
                re.IGNORECASE
            )
            date_match = re.search(
                r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{2,4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                date_item,
                re.IGNORECASE
            )
            deadline = timing_match.group(0).strip() if timing_match else (date_match.group(0).strip() if date_match else None)
            clean_text = f"Keep track of key deadline: {date_item}"
            if clean_text not in seen_texts:
                actions.append({"text": clean_text, "deadline": deadline})
                seen_texts.add(clean_text)

    # 2. Obligations from highlights
    if highlights and highlights.get("obligations"):
        for ob in highlights["obligations"][:3]:
            clean_text = f"Ensure compliance with obligation: {ob}"
            if clean_text not in seen_texts:
                deadline_match = re.search(r'(?:by|before|on|within)\s+([^\,\.]+)', ob, re.IGNORECASE)
                deadline = deadline_match.group(0).strip() if deadline_match else None
                actions.append({"text": clean_text, "deadline": deadline})
                seen_texts.add(clean_text)

    # 3. Direct regex search for dates/deadlines in text if none found yet
    if not actions and text:
        date_matches = re.findall(
            r'(?:(?:pay|due|terminated?|renewed?|expires?|effective)\s+(?:on|by|before|within)\s+[^\n\.\;]{3,40})',
            text,
            re.IGNORECASE
        )
        for dm in date_matches[:3]:
            clean_text = f"Comply with timeline: {dm.strip()}"
            if clean_text not in seen_texts:
                actions.append({"text": clean_text, "deadline": "As per document"})
                seen_texts.add(clean_text)

    # 4. Standard legal due-diligence steps for this document type to reach 4-6 items
    defaults = [
        {"text": f"Verify all personal details, names, and addresses in this {doc_type}", "deadline": None},
        {"text": f"Keep a signed copy of the original {doc_type} safely stored", "deadline": None},
        {"text": "Consult a legal expert if any penalty, liability, or clause seems unfair", "deadline": None},
    ]

    for d in defaults:
        if len(actions) >= 5:
            break
        if d["text"] not in seen_texts:
            actions.append(d)
            seen_texts.add(d["text"])

    return actions


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

    # Fallback: extract real key sentences from the uploaded document text
    if mode == "short":
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 15]
        bullets = [f"• {l[:160]}" for l in lines[:4]]
        return "\n".join(bullets) if bullets else "• Document uploaded and processed successfully."
    else:
        return text[:600] + "..." if len(text) > 600 else text


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

    # Use RAG pipeline to retrieve relevant clauses and citations
    from services.rag_service import rag_pipeline

    if len(document_content) > 3000:
        doc_context, retrieved_chunks = rag_pipeline.build_augmented_context(
            document_text=document_content,
            query=question,
            top_k=5,
        )
        context_header = "=== RELEVANT DOCUMENT CLAUSES (RETRIEVED VIA RAG) ==="
    else:
        doc_context = document_content
        context_header = "=== DOCUMENT CONTENT ==="

    messages = [
        {
            "role": "system",
            "content": (
                "You are NyayBot, a helpful legal document assistant for Indian citizens. "
                "You have been given context retrieved from a legal document uploaded by the user. "
                "Answer the user's questions about the document in simple, clear language. "
                "Be specific and refer to details from the document. "
                "Whenever stating any specific term, rule, amount, deadline, or obligation, "
                "cite the relevant source clause/section (e.g., [Clause 2 / Section 3]). "
                "If the document doesn't contain information to answer the question, say so honestly. "
                "Keep answers concise but thorough. Do NOT provide formal legal advice — "
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
                f"{context_header}\n{doc_context}\n=== END CONTEXT ==="
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