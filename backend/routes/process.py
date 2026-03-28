from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.extractor import extract_text
from services.chunker import chunk_text
from services.ai_service import (
    simplify_text,
    chat_with_document,
    detect_document_type,
    analyze_highlights,
    generate_summary,
)
from services.translator import translate_text

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    question: str
    document_content: str
    language: str = "English"
    history: Optional[List[ChatMessage]] = []


@router.post("/chat")
async def chat_about_document(req: ChatRequest):
    """Chat with AI about the uploaded document."""
    try:
        ai_answer = chat_with_document(
            question=req.question,
            document_content=req.document_content,
            history=req.history or [],
        )
        # AI now replies in the same language as the question automatically
        return {"answer": ai_answer}

    except Exception as e:
        print(f"[NyayBot] Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat: {str(e)}"
        )


@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
    language: str = Form(default="English")
):
    try:
        # 1. Extract text from the document
        text = await extract_text(file)

        if not text or not text.strip():
            return {
                "summary": "Could not extract any text from the document.",
                "short_summary": "• Could not extract text from this document.",
                "detailed_summary": "Could not extract any text from the document.",
                "content": "No readable text found in the uploaded file. Please try a different file.",
                "document_type": {"type": "Unknown", "confidence": "low"},
                "highlights": {"dates": [], "obligations": [], "risks": []},
                "actions": [
                    "Try uploading a text-based PDF (not scanned)",
                    "Ensure the document is clear and readable",
                    "Try a different file format (PDF, JPG, PNG)"
                ]
            }

        # Check if extraction returned an error message
        if text.startswith("["):
            return {
                "summary": text,
                "short_summary": f"• {text}",
                "detailed_summary": text,
                "content": text,
                "document_type": {"type": "Unknown", "confidence": "low"},
                "highlights": {"dates": [], "obligations": [], "risks": []},
                "actions": [
                    "Try uploading a text-based PDF (not scanned)",
                    "Ensure the document is clear and readable",
                    "Try a different file format"
                ]
            }

        # 2. Detect document type (runs on raw text for best accuracy)
        document_type = detect_document_type(text)
        print(f"[NyayBot] Detected document type: {document_type}")

        # 3. Analyze key highlights (dates, obligations, risks)
        highlights = analyze_highlights(text)
        print(f"[NyayBot] Extracted highlights: {len(highlights.get('dates', []))} dates, "
              f"{len(highlights.get('obligations', []))} obligations, "
              f"{len(highlights.get('risks', []))} risks")

        # 4. Generate both short and detailed summaries
        short_summary = generate_summary(text, mode="short")
        detailed_summary = generate_summary(text, mode="detailed")

        # 5. Chunk the text into manageable pieces
        chunks = chunk_text(text)

        # 6. Simplify each chunk using AI (or fallback)
        simplified_chunks = []
        for chunk in chunks:
            simplified = simplify_text(chunk)
            simplified_chunks.append(simplified)

        # 7. Join simplified text
        simplified_text = "\n\n".join(simplified_chunks)

        # 8. Translate if not English
        if language.lower() != "english":
            translated = translate_text(simplified_text, language)
            short_summary_translated = translate_text(short_summary, language)
            detailed_summary_translated = translate_text(detailed_summary, language)

            # Translate highlights
            translated_highlights = {
                "dates": [translate_text(d, language) for d in highlights.get("dates", [])],
                "obligations": [translate_text(o, language) for o in highlights.get("obligations", [])],
                "risks": [translate_text(r, language) for r in highlights.get("risks", [])],
            }
        else:
            translated = simplified_text
            short_summary_translated = short_summary
            detailed_summary_translated = detailed_summary
            translated_highlights = highlights

        # 9. Generate action items (and translate if needed)
        actions = _generate_actions(language)

        return {
            "summary": short_summary_translated,
            "short_summary": short_summary_translated,
            "detailed_summary": detailed_summary_translated,
            "content": translated,
            "document_type": document_type,
            "highlights": translated_highlights,
            "actions": actions,
        }

    except Exception as e:
        print(f"[NyayBot] Error in process_document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


def _generate_actions(language):
    """Generate action items for the user, translated if needed."""
    actions = [
        "Read through the simplified document carefully",
        "Note down any dates, deadlines, or amounts mentioned",
        "Consult a lawyer if any clause seems unfair or unclear",
        "Keep a signed copy of the original document",
        "Set reminders for important deadlines mentioned",
        "Verify all personal details are correct in the document"
    ]

    if language.lower() != "english":
        translated_actions = []
        for action in actions:
            try:
                translated = translate_text(action, language)
                translated_actions.append(translated)
            except Exception:
                translated_actions.append(action)
        return translated_actions

    return actions