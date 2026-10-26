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
    generate_action_items,
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
                "detailed_summary": "Could not extract any text from the document.",
                "content": "No readable text found in the uploaded file. Please try a different file.",
                "document_type": {"type": "Unknown", "confidence": "low"},
                "highlights": {"dates": [], "obligations": [], "risks": []},
                "actions": [
                    {"text": "Try uploading a text-based PDF (not scanned)", "deadline": None},
                    {"text": "Ensure the document is clear and readable", "deadline": None},
                    {"text": "Try a different file format (PDF, JPG, PNG)", "deadline": None}
                ]
            }

        # Check if extraction returned an error message
        if text.startswith("["):
            return {
                "summary": text,
                "detailed_summary": text,
                "content": text,
                "document_type": {"type": "Unknown", "confidence": "low"},
                "highlights": {"dates": [], "obligations": [], "risks": []},
                "actions": [
                    {"text": "Try uploading a text-based PDF (not scanned)", "deadline": None},
                    {"text": "Ensure the document is clear and readable", "deadline": None},
                    {"text": "Try a different file format", "deadline": None}
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

        # 4. Generate comprehensive document summary
        summary = generate_summary(text, mode="detailed")

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
            summary_translated = translate_text(summary, language)

            # Translate highlights
            translated_highlights = {
                "dates": [translate_text(d, language) for d in highlights.get("dates", [])],
                "obligations": [translate_text(o, language) for o in highlights.get("obligations", [])],
                "risks": [translate_text(r, language) for r in highlights.get("risks", [])],
            }
        else:
            translated = simplified_text
            summary_translated = summary
            translated_highlights = highlights

        # 9. Generate document-grounded action items with extracted dates and deadlines
        actions = _generate_actions(
            text=text,
            highlights=highlights,
            document_type=document_type.get("type", "Legal Document"),
            language=language
        )

        return {
            "summary": summary_translated,
            "detailed_summary": summary_translated,
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


def _generate_actions(text, highlights, document_type, language):
    """Generate document-grounded action items with extracted dates, translated if needed."""
    raw_actions = generate_action_items(text, highlights=highlights, doc_type=document_type)

    if language.lower() != "english":
        translated_actions = []
        for item in raw_actions:
            try:
                t_text = translate_text(item["text"], language)
                t_deadline = translate_text(item["deadline"], language) if item.get("deadline") else None
                translated_actions.append({"text": t_text, "deadline": t_deadline})
            except Exception:
                translated_actions.append(item)
        return translated_actions

    return raw_actions