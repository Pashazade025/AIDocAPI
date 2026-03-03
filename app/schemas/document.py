from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    id: int
    filename: str
    file_size: int
    uploaded_at: datetime
    message: str = "Document uploaded successfully"
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document details response"""
    id: int
    filename: str
    file_size: int
    content_text: Optional[str] = None
    ai_analysis: Optional[str] = None
    uploaded_at: datetime
    user_id: int
    
    class Config:
        from_attributes = True


class DocumentAnalysisRequest(BaseModel):
    """Schema for AI analysis request"""
    prompt: Optional[str] = Field(
        default="Analyze this document and provide a summary.",
        max_length=500
    )


class DocumentAnalysisResponse(BaseModel):
    """Schema for AI analysis response"""
    document_id: int
    analysis: str  # Keep for backward compatibility
    ai_summary: str
    ai_insights: str
    key_topics: str
    extracted_text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)