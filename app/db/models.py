from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    documents = relationship("Document", back_populates="owner")


class Document(Base):
    """Document model for storing uploaded files and AI analysis"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_text = Column(Text, nullable=True)  # Extracted text from document
    ai_analysis = Column(Text, nullable=True)   # Gemini AI analysis result
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship
    owner = relationship("User", back_populates="documents")