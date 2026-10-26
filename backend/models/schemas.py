"""
Pydantic data schemas for NyayBot request and response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentTypeSchema(BaseModel):
    type: str = Field(..., description="Detected category of the legal document")
    confidence: str = Field("medium", description="Confidence level: high, medium, or low")


class HighlightsSchema(BaseModel):
    dates: List[str] = Field(default_factory=list, description="Extracted dates and timeline deadlines")
    obligations: List[str] = Field(default_factory=list, description="Key obligations and duties")
    risks: List[str] = Field(default_factory=list, description="Potential risks, penalties, and liabilities")


class ActionItemSchema(BaseModel):
    text: str = Field(..., description="Actionable checklist instruction for the user")
    deadline: Optional[str] = Field(None, description="Specific deadline date or timeframe from document")


class ProcessResponseSchema(BaseModel):
    summary: str
    short_summary: str
    detailed_summary: str
    content: str
    document_type: DocumentTypeSchema
    highlights: HighlightsSchema
    actions: List[ActionItemSchema]


class ChatRequestSchema(BaseModel):
    message: str = Field(..., description="User query about the uploaded legal document")
    document_text: Optional[str] = Field("", description="Full or simplified document text")
    language: Optional[str] = Field("English", description="Target response language")


class ChatResponseSchema(BaseModel):
    reply: str = Field(..., description="AI response grounded in document context")
    citations: Optional[List[str]] = Field(default_factory=list, description="Retrieved clause citations")
