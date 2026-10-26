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
        if not _init_groq():
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
    # Dates & Deadlines patterns (statutory, contract dates, deadlines, notice periods)
    date_patterns = [
        r'(?:(?:due|payable|commencing|terminated?|renewed?|expires?|effective|valid)\s+(?:on|by|before|within|from)|on\s+or\s+before|valid\s+(?:up\s+to|until)|expires?\s+on|period\s+of|within\s+\d+\s+(?:days|months|weeks|years)|(?:prior\s+)?written\s+notice\s+of\s+\d+\s+(?:days|months)|\b\d+\s+(?:days?|months?)\s+(?:prior\s+)?(?:written\s+)?notice)[^\n\.\;]{0,50}',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+of\s+(?:every|each)\s+[^\n\.\;]{3,35}',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z]*[\s,]+\d{2,4}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s*(?:to|-)\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?\b',
    ]
    for pat in date_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            clean = match.group(0).strip()
            clean = re.sub(r'^[0-9]+[\.\)\-]\s*', '', clean).strip()
            if clean and clean not in dates and len(clean) >= 4:
                dates.append(clean)
            if len(dates) >= 6:
                break
        if len(dates) >= 6:
            break

    # Obligations patterns (shall, must, agreed to, payable, undertakes)
    obligations = []
    sentences = re.split(r'[\r\n]+|(?<=[.!?])\s+(?=[A-Z0-9])', text)
    ob_verb_regex = re.compile(
        r'\b(shall|must|agrees?\s+to|undertakes?\s+to|required\s+to|responsible\s+for|payable|refund(?:ed)?|deposit|liable)\b',
        re.IGNORECASE
    )
    for sent in sentences:
        s_clean = re.sub(r'^(?:[0-9]+[\.\)\-]|[A-Za-z][\.\)]|[\u2022\-\*])\s*', '', sent).strip()
        if len(s_clean) >= 15 and ob_verb_regex.search(s_clean):
            snippet = s_clean if len(s_clean) <= 130 else s_clean[:127] + '...'
            if snippet not in obligations:
                obligations.append(snippet)
            if len(obligations) >= 6:
                break

    # Risks patterns (penalty, default, breach, forfeit, interest, evict, termination)
    risks = []
    risk_verb_regex = re.compile(
        r'\b(penalty|default|breach|forfeit|liquidated\s+damages|evict(?:ion)?|termination|interest\s+of|late\s+(?:fee|penalty)|liabilit(?:y|ies))\b',
        re.IGNORECASE
    )
    for sent in sentences:
        s_clean = re.sub(r'^(?:[0-9]+[\.\)\-]|[A-Za-z][\.\)]|[\u2022\-\*])\s*', '', sent).strip()
        if len(s_clean) >= 15 and risk_verb_regex.search(s_clean):
            snippet = s_clean if len(s_clean) <= 130 else s_clean[:127] + '...'
            if snippet not in risks:
                risks.append(snippet)
            if len(risks) >= 6:
                break

    return {
        "dates": dates[:6],
        "obligations": obligations[:6],
        "risks": risks[:6],
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
    """
    Dynamically extract actionable steps directly from document text.
    Pulls concrete clauses with dates, payments (Rs/INR), obligations, and deadlines.
    """
    actions = []
    seen_texts = set()

    if not text:
        return [
            {"text": f"Verify all personal details, names, and addresses in this {doc_type}", "deadline": None},
            {"text": f"Keep a signed copy of the original {doc_type} safely stored", "deadline": None},
            {"text": "Consult a legal expert if any penalty, liability, or clause seems unfair", "deadline": None},
        ]

    # Split document into clauses / sentences
    raw_clauses = re.split(r'[\r\n]+|(?<=[.!?])\s+(?=[A-Z0-9])', text)
    clean_clauses = []
    for rc in raw_clauses:
        c = re.sub(r'^(?:[0-9]+[\.\)\-]|[A-Za-z][\.\)]|[\u2022\-\*])\s*', '', rc).strip()
        if len(c) >= 15:
            clean_clauses.append(c)

    # Regex for dates, notice periods, and payment deadlines
    date_regex = re.compile(
        r'(?:(?:on\s+or\s+before|due\s+by|by\s+the|commencing\s+from|valid\s+(?:up\s+to|until)|expires?\s+on|period\s+of|within)\s+[^\,\;\n]{3,40}'
        r'|\b\d{1,2}(?:st|nd|rd|th)?\s+of\s+(?:every|each)\s+[^\,\;\n]{3,25}'
        r'|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z]*[\s,]+\d{2,4}\b'
        r'|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s*(?:to|-)\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?'
        r'|\b\d+\s+(?:days?|months?|weeks?|years?)\s+(?:prior\s+)?(?:written\s+)?notice\b)',
        re.IGNORECASE
    )

    money_regex = re.compile(r'(?:Rs\.?|INR|\u20b9)\s*[\d,]+(?:\s*/-)?(?:\s*\([^\)]+\))?', re.IGNORECASE)

    obligation_regex = re.compile(
        r'\b(shall|must|agrees?\s+to|undertakes?\s+to|required\s+to|payable|paid|refund(?:ed)?|terminate|notice|deposit|due|delay|penalty|liable)\b',
        re.IGNORECASE
    )

    # 1. First priority: Clauses with both obligations and explicit dates/deadlines or monetary amounts
    for clause in clean_clauses:
        has_ob = obligation_regex.search(clause)
        has_date = date_regex.search(clause)
        has_money = money_regex.search(clause)

        if has_ob and (has_date or has_money):
            deadline = has_date.group(0).strip() if has_date else (has_money.group(0).strip() if has_money else None)
            snippet = clause if len(clause) <= 125 else clause[:122] + "..."
            key = snippet.lower()
            if key not in seen_texts:
                actions.append({"text": snippet, "deadline": deadline})
                seen_texts.add(key)
        if len(actions) >= 5:
            break

    # 2. Second priority: Key obligation clauses from text
    if len(actions) < 4:
        for clause in clean_clauses:
            if obligation_regex.search(clause):
                snippet = clause if len(clause) <= 125 else clause[:122] + "..."
                key = snippet.lower()
                if key not in seen_texts:
                    has_date = date_regex.search(clause)
                    deadline = has_date.group(0).strip() if has_date else None
                    actions.append({"text": snippet, "deadline": deadline})
                    seen_texts.add(key)
            if len(actions) >= 5:
                break

    # 3. Third priority: Highlights passed in (dates or obligations)
    if len(actions) < 4 and highlights:
        for d in highlights.get("dates", []):
            if d.lower() not in seen_texts:
                actions.append({"text": f"Review key timeline: {d}", "deadline": d})
                seen_texts.add(d.lower())
            if len(actions) >= 5:
                break

    # 4. Only if document yielded fewer than 3 items, pad with context-aware steps
    defaults = [
        {"text": f"Verify all personal details, names, and addresses in this {doc_type}", "deadline": None},
        {"text": f"Keep a signed copy of the original {doc_type} safely stored", "deadline": None},
        {"text": "Consult a legal expert if any penalty, liability, or clause seems unfair", "deadline": None},
    ]
    for d in defaults:
        if len(actions) >= 4:
            break
        if d["text"].lower() not in seen_texts:
            actions.append(d)
            seen_texts.add(d["text"].lower())

    return actions


def _clean_party_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r'[\(\)\[\]\{\}]', '', name).strip()
    name = re.sub(r'^(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s*', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def _generate_extractive_detailed_summary(text: str) -> str:
    """
    Generate a complete, coherent, multi-paragraph document summary
    by extracting document type, parties, financial values, dates, and covenants.
    Never truncates or ends with ellipses (...).
    """
    clean_text = text.strip() if text else ""
    if not clean_text:
        return (
            "This document was uploaded successfully. "
            "However, sufficient textual content could not be extracted to generate a comprehensive summary. "
            "Please ensure that the document contains selectable text or is a clear, readable document."
        )

    # 1. Detect Document Type
    doc_info = detect_document_type(clean_text)
    doc_type = doc_info.get("type", "Legal Agreement")
    if doc_type == "Unknown" or not doc_type:
        doc_type = "Legal Agreement"

    # 2. Extract Execution / Effective Date
    date_match = re.search(
        r'(?:on\s+this\s+|dated\s+|executed\s+(?:at\s+[^\n,]+)?\s*on\s+(?:this\s+)?)(.*?(?:20\d{2}|19\d{2}|\(?Year\)?))',
        clean_text, re.IGNORECASE
    )
    date_str = date_match.group(1).strip() if date_match else None
    if date_str:
        date_str = date_str.replace("(", "").replace(")", "").strip()
    date_phrase = f"executed on {date_str}" if date_str else "executed between the participating parties"

    # 3. Extract Parties
    party1_match = re.search(
        r'(?:between:?\s*|by\s+and\s+between:?\s*)([A-Za-z0-9\s\.\(\)\/]+?)(?:,\s*S/o|,\s*D/o|,\s*W/o|,\s*residing|having|hereinafter|\n)',
        clean_text, re.IGNORECASE
    )
    party2_match = re.search(
        r'(?:in\s+favour\s+of:?\s*|and\s*:\s*|and\s+([A-Za-z0-9\s\.\(\)\/]+?)(?:,\s*S/o|,\s*D/o|,\s*W/o|,\s*residing|having|hereinafter|\n))',
        clean_text, re.IGNORECASE
    )

    p1_raw = party1_match.group(1).strip() if party1_match else ""
    p2_raw = party2_match.group(1).strip() if (party2_match and party2_match.group(1)) else ""

    p1 = _clean_party_name(p1_raw)
    p2 = _clean_party_name(p2_raw)

    if not p1 or len(p1) > 60 or p1.lower().startswith("hereinafter"):
        if "rental" in doc_type.lower() or "lease" in doc_type.lower():
            p1 = "the Landlord / Owner"
        elif "employment" in doc_type.lower():
            p1 = "the Employer"
        elif "loan" in doc_type.lower():
            p1 = "the Lender"
        else:
            p1 = "the First Party"

    if not p2 or len(p2) > 60 or p2.lower().startswith("hereinafter"):
        if "rental" in doc_type.lower() or "lease" in doc_type.lower():
            p2 = "the Tenant"
        elif "employment" in doc_type.lower():
            p2 = "the Employee"
        elif "loan" in doc_type.lower():
            p2 = "the Borrower"
        else:
            p2 = "the Second Party"

    # 4. Extract Financial Commitments (Rent, Deposit, Consideration, Salary)
    rent_match = re.search(
        r'(?:monthly\s+)?rent\b[^\.\n,;]*?(?:is|of|at|to|amounting\s+to)?\s*(?:Rs\.?|INR|₹|Rupees)\s*([\d,]+(?:\.\d{2})?)',
        clean_text, re.IGNORECASE
    )
    deposit_match = re.search(
        r'(?:security\s+deposit|advance|caution\s+money)\b[^\.\n,;]*?(?:is|of|at|sum\s+of)?\s*(?:Rs\.?|INR|₹|Rupees)\s*([\d,]+(?:\.\d{2})?)',
        clean_text, re.IGNORECASE
    )
    all_amounts = re.findall(r'(?:Rs\.?|INR|₹|Rupees)\s*[\d,]+(?:\.\d{2})?', clean_text, re.IGNORECASE)

    # 5. Extract Due Dates and Payment Schedule
    due_match = re.search(
        r'(?:on or before|by the|within)\s*([^\n\.,;]+(?:day|each month|month|days))',
        clean_text, re.IGNORECASE
    )
    due_str = due_match.group(1).strip() if due_match else None

    # 6. Extract Agreement Duration / Tenure
    duration_match = re.search(
        r'(\b\d+\s*(?:months?|years?|days?)\b)',
        clean_text, re.IGNORECASE
    )
    duration_str = duration_match.group(1) if duration_match else "an agreed tenure"

    # 7. Extract Notice Period
    notice_match = re.search(
        r'(\b\d+\s*(?:months?|days?)\b(?:\s*prior)?\s*notice)',
        clean_text, re.IGNORECASE
    )
    notice_str = notice_match.group(1).strip() if notice_match else "prior written notice as agreed"

    # 8. Extract Governing Jurisdiction / City
    jurisdiction_match = re.search(
        r'(?:jurisdiction\s+of\s+(?:the\s+)?courts?\s+(?:at|in)|courts?\s+(?:at|in))\s+([A-Za-z]+)',
        clean_text, re.IGNORECASE
    )
    city = jurisdiction_match.group(1).strip() if jurisdiction_match else None

    # BUILD COMPLETE 3-PARAGRAPH SUMMARY
    para1 = (
        f"This document is a formal {doc_type} {date_phrase}. "
        f"It establishes legally binding covenants, obligations, and relationship terms between {p1} and {p2}. "
        f"The agreement serves to legally govern the mutual rights, permitted usage, and duties associated with the demised subject matter under applicable Indian law."
    )

    finance_details = []
    if rent_match:
        finance_details.append(f"the primary payment or monthly rent of Rs. {rent_match.group(1)}")
    if deposit_match:
        finance_details.append(f"a security deposit of Rs. {deposit_match.group(1)} (refundable at the end of the term subject to inspection and settlement of dues)")
    elif all_amounts:
        finance_details.append(f"stated financial commitments including {', '.join(all_amounts[:2])}")

    fin_text = ", along with ".join(finance_details) if finance_details else "the financial commitments agreed upon by the parties"
    schedule_text = f", payable {due_str}" if due_str else ""

    para2 = (
        f"Under the governing financial stipulations, the agreement regulates {fin_text}{schedule_text}. "
        f"The valid operational period of this agreement is set for an initial duration of {duration_str}, "
        f"subject to compliance with the terms and mutual agreement for renewal."
    )

    jurisdiction_clause = (
        f" Any legal disputes arising hereunder are subject to the jurisdiction of the courts in {city}."
        if city else
        " Any disputes are subject to the legal remedies and jurisdiction prescribed in the agreement."
    )

    para3 = (
        f"Both parties are obligated to comply with all designated responsibilities, including timely payments, maintenance requirements, and lawful conduct. "
        f"Either party may initiate termination by providing {notice_str}. "
        f"Upon conclusion or termination, all financial settlements, property handovers, and compliance obligations must be formally resolved.{jurisdiction_clause}"
    )

    return f"{para1}\n\n{para2}\n\n{para3}"


def _generate_extractive_short_summary(text: str) -> str:
    """Generate 3-5 concise bullet points from the document text."""
    clean_text = text.strip() if text else ""
    if not clean_text:
        return "• Document uploaded and processed successfully."

    doc_info = detect_document_type(clean_text)
    doc_type = doc_info.get("type", "Legal Document")

    amounts = re.findall(r'(?:Rs\.?|INR|₹|Rupees)\s*[\d,]+(?:\.\d{2})?', clean_text, re.IGNORECASE)
    duration_match = re.search(r'(\b\d+\s*(?:months?|years?|days?)\b)', clean_text, re.IGNORECASE)
    notice_match = re.search(r'(\b\d+\s*(?:months?|days?)\b(?:\s*prior)?\s*notice)', clean_text, re.IGNORECASE)

    bullets = [
        f"• Document Type: Identifies as a legally binding {doc_type}.",
    ]
    if amounts:
        bullets.append(f"• Financial Provisions: Specifies key monetary terms including {', '.join(amounts[:2])}.")
    if duration_match:
        bullets.append(f"• Agreement Tenure: Established for an agreed period of {duration_match.group(1)}.")
    if notice_match:
        bullets.append(f"• Termination Notice: Requires {notice_match.group(1)} for early exit or non-renewal.")
    bullets.append("• Compliance: Both parties must strictly adhere to all listed covenants and dispute terms.")

    return "\n".join(bullets[:5])


# ─── SUMMARY GENERATION ─────────────────────────────────────────────────────

def generate_summary(text, mode="short"):
    """
    Generate a summary of the document.
    mode='short' → 3-5 bullet points
    mode='detailed' → comprehensive, multi-paragraph explanation
    """
    snippet = text[:5000] if text else ""

    if mode == "short":
        system_prompt = (
            "You are an expert legal assistant for Indian citizens. "
            "Create a SHORT summary with exactly 3 to 5 bullet points. "
            "Each bullet should be one clear, complete sentence. "
            "Include the most critical information: who, what, when, how much. "
            "Format: Start each bullet with '• ' (bullet character and space). "
            "Do NOT add any intro text or truncated sentences."
        )
    else:
        system_prompt = (
            "You are an expert legal document clarifier for Indian citizens. "
            "Write a comprehensive, professional, and fully completed 2 to 3 paragraph summary of this legal document. "
            "Do NOT truncate, do NOT use ellipses (...), and ensure every paragraph and sentence is fully finished. "
            "Paragraph 1: State what document this is, who the parties are, the core relationship, and effective date. "
            "Paragraph 2: Detail the financial terms (exact amounts, rent/deposit/salary/consideration), payment schedules, and agreement duration. "
            "Paragraph 3: Explain the critical obligations, maintenance/compliance duties, termination notice requirements, and breach consequences. "
            "Use clear, plain language without legal jargon."
        )

    result = _groq_call(
        system_prompt,
        f"Summarize this legal document completely:\n\n{snippet}",
        temperature=0.2,
        max_tokens=1200
    )

    if result and len(result.strip()) > 80:
        return result.strip()

    # Intelligent document-grounded extractive fallback
    if mode == "short":
        return _generate_extractive_short_summary(text)
    else:
        return _generate_extractive_detailed_summary(text)


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
    Falls back to intelligent local Hybrid RAG document retrieval if AI key is not configured.
    """
    global _groq_available, _groq_client

    if not _groq_available or _groq_client is None:
        if not _init_groq():
            return _basic_chat_fallback(question, document_content)

    # Use RAG pipeline to retrieve top relevant clauses
    from services.rag_service import rag_pipeline

    # For documents up to 40k chars (~8k words), provide BOTH top retrieved clauses AND full document context
    # This prevents the AI from missing any details or giving incomplete answers.
    if len(document_content) <= 40000:
        augmented_clauses, _ = rag_pipeline.build_augmented_context(
            document_text=document_content,
            query=question,
            top_k=6,
        )
        doc_context = (
            f"=== MOST RELEVANT RETRIEVED CLAUSES (START HERE) ===\n{augmented_clauses}\n\n"
            f"=== FULL DOCUMENT CONTENT (FOR COMPLETE CONTEXT) ===\n{document_content}\n"
            f"=== END CONTEXT ==="
        )
    else:
        augmented_clauses, _ = rag_pipeline.build_augmented_context(
            document_text=document_content,
            query=question,
            top_k=10,
        )
        doc_context = f"=== RELEVANT DOCUMENT CLAUSES ===\n{augmented_clauses}\n=== END CONTEXT ==="

    system_content = (
        "You are NyayBot, an expert legal document assistant for Indian citizens. "
        "Your task is to answer the user's question with 100% accuracy, thoroughness, and completeness based on the provided document.\n\n"
        "MANDATORY INSTRUCTIONS FOR ACCURACY AND COMPLETENESS:\n"
        "1. Give a comprehensive, fully finished answer. DO NOT be overly brief, vague, or give one-line answers.\n"
        "2. Include EVERY specific detail, monetary amount (Rs. / INR), due date, percentage, notice timeline, and obligation mentioned in the document for this topic.\n"
        "3. Structure your response with clear, organized bullet points and bold headings so it is effortless to read.\n"
        "4. Always cite the exact clause numbers or section titles from the document (e.g., [Clause 2], [Clause 3]).\n"
        "5. If there are multiple parts (e.g., monthly rent, maintenance fees, electricity/water dues, security deposit), list and explain EACH one distinctly.\n"
        "6. If the document does not mention a specific detail, explicitly state that it is not specified in this document.\n"
        "7. Keep language crystal-clear and plain, avoiding unnecessary legalese.\n\n"
        "LANGUAGE RULE: Detect the language of the user's question and ALWAYS reply in that SAME language (Hindi, Telugu, Tamil, Kannada, Bengali, Marathi, Gujarati, Malayalam, Punjabi, Urdu, Odia, English, etc.). Match the user's language exactly.\n\n"
        f"{doc_context}"
    )

    messages = [
        {
            "role": "system",
            "content": system_content
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
            temperature=0.2,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = str(e)
        print(f"[NyayBot] Groq chat API error: {error_msg}")
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            _groq_available = False
        return _basic_chat_fallback(question, document_content)


def _basic_chat_fallback(question, document_content=""):
    """
    Intelligent document-grounded fallback response when external LLM is not active.
    Uses local Hybrid RAG (BM25 + TF-IDF) to search the document text for the user's question.
    """
    if document_content and document_content.strip():
        try:
            from services.rag_service import rag_pipeline
            matched_chunks = rag_pipeline.index_and_retrieve(
                document_text=document_content,
                query=question,
                top_k=5,
            )
            # Filter chunks with score > 0 or top chunks
            valid_chunks = [ch for ch in matched_chunks if ch.get("score", 0) > 0]
            if not valid_chunks and matched_chunks:
                valid_chunks = matched_chunks[:3]

            if valid_chunks:
                response_lines = [
                    f"Based on your document, here are the complete clauses regarding **\"{question}\"**:\n"
                ]
                for ch in valid_chunks:
                    text = ch.get("text", "").strip()
                    if text:
                        response_lines.append(f"• {text}\n")

                return "\n".join(response_lines).strip()
        except Exception as e:
            print(f"[NyayBot] RAG chat fallback error: {e}")

    return (
        "I'm sorry, the AI service is currently unavailable. "
        "Please review the simplified document above for your answer, "
        "or try again in a moment. For specific legal questions, "
        "we recommend consulting a qualified lawyer."
    )