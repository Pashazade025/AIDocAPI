from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
from app.core.deps import get_db, get_current_user_from_token
from app.core.config import settings
from app.db.models import User, Document
from app.schemas.document import (
    DocumentUploadResponse, 
    DocumentResponse, 
    DocumentAnalysisRequest,
    DocumentAnalysisResponse
)
from app.services.gemini_service import GeminiService

router = APIRouter()
gemini_service = GeminiService()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Upload a document"""
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Extract text content
    content_text = None
    if file_ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content_text = f.read()
        except:
            content_text = None
    elif file_ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                content_text = text.strip() if text.strip() else None
        except Exception as e:
            print(f"PDF extraction error: {e}")
            content_text = None
    
    # Create database record
    new_document = Document(
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        content_text=content_text,
        user_id=current_user.id
    )
    
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    return new_document


@router.get("/", response_model=List[DocumentResponse])
def get_user_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all documents for current user"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.post("/{document_id}/analyze", response_model=DocumentAnalysisResponse)
def analyze_document(
    document_id: int,
    request: DocumentAnalysisRequest = DocumentAnalysisRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Analyze document with Gemini AI"""
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if document has text content
    if not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extractable text content"
        )
    
    # Analyze with Gemini
    try:
        analysis_result = gemini_service.analyze_document(
            document.content_text,
            request.prompt
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )
    
    # Save analysis result (store full analysis text)
    document.ai_analysis = analysis_result.get("full_analysis", analysis_result.get("ai_summary", ""))
    db.commit()
    
    return {
        "document_id": document.id,
        "analysis": analysis_result.get("full_analysis", analysis_result.get("ai_summary", "")),
        "ai_summary": analysis_result.get("ai_summary", ""),
        "ai_insights": analysis_result.get("ai_insights", ""),
        "key_topics": analysis_result.get("key_topics", ""),
        "extracted_text": document.content_text[:5000] if document.content_text else None,
        "timestamp": datetime.utcnow()
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return None


@router.post("/{document_id}/ask")
def ask_question_about_document(
    document_id: int,
    question_data: dict,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Ask a question about a specific document using AI"""
    
    from app.services.gemini_service import GeminiService
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    question = question_data.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        gemini_service = GeminiService()
        answer = gemini_service.ask_question(
            document_text=document.extracted_text,
            question=question
        )
        
        return {
            "document_id": document_id,
            "document_name": document.original_filename,
            "question": question,
            "answer": answer
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")