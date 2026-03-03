from google import genai
from google.genai import types
from app.core.config import settings
from typing import Dict, Optional
import json


class GeminiService:
    """Service for Google Gemini AI integration"""
    
    def __init__(self):
        """Initialize Gemini with API key"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    def analyze_document(self, text: str, prompt: str = None) -> Dict[str, str]:
        """
        Analyze document text using Gemini AI and return structured analysis
        
        Args:
            text: Document text content
            prompt: Custom analysis prompt (optional)
            
        Returns:
            Dictionary with structured analysis (summary, insights, topics)
        """
        
        # Use more of the text for better analysis (increase to 10000 chars)
        document_content = text[:10000]
        
        # Structured analysis prompt
        analysis_prompt = """Analyze this document and provide a structured response in the following format:

1. **Summary:** Provide a concise 2-3 sentence summary of the document.

2. **Key Topics:** List 3-5 main topics or themes covered in the document, separated by commas.

3. **Insights:** Provide 2-3 key insights or important points from the document.

Document Content:
{document_content}

Please format your response clearly with the sections labeled as shown above."""
        
        # Use custom prompt if provided
        if prompt:
            analysis_prompt = f"{prompt}\n\nDocument Content:\n{document_content}"
        
        # Generate response
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=analysis_prompt
            )
            
            response_text = response.text
            
            # Parse the structured response
            summary = ""
            insights = ""
            topics = ""
            
            # Try to extract structured sections
            if "**Summary:**" in response_text or "Summary:" in response_text:
                parts = response_text.split("**Summary:**" if "**Summary:**" in response_text else "Summary:")
                if len(parts) > 1:
                    summary_part = parts[1].split("**Key Topics:**" if "**Key Topics:**" in parts[1] else "Key Topics:")[0].strip()
                    summary = summary_part.split("**Insights:**" if "**Insights:**" in summary_part else "Insights:")[0].strip()
            
            if "**Key Topics:**" in response_text or "Key Topics:" in response_text:
                parts = response_text.split("**Key Topics:**" if "**Key Topics:**" in response_text else "Key Topics:")
                if len(parts) > 1:
                    topics_part = parts[1].split("**Insights:**" if "**Insights:**" in parts[1] else "Insights:")[0].strip()
                    topics = topics_part.split("\n\n")[0].strip()
            
            if "**Insights:**" in response_text or "Insights:" in response_text:
                parts = response_text.split("**Insights:**" if "**Insights:**" in response_text else "Insights:")
                if len(parts) > 1:
                    insights = parts[1].strip()
            
            # Fallback: if parsing failed, use full response as summary
            if not summary:
                summary = response_text[:500] if len(response_text) > 500 else response_text
                insights = response_text[500:1000] if len(response_text) > 500 else ""
                topics = "General document analysis"
            
            return {
                "ai_summary": summary,
                "ai_insights": insights,
                "key_topics": topics,
                "full_analysis": response_text
            }
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def ask_question(self, document_text: str, question: str, document_context: Optional[Dict] = None) -> str:
        """
        Ask a specific question about the document with optional context
        
        Args:
            document_text: The document content
            question: User's question
            document_context: Optional document metadata (filename, summary, etc.)
            
        Returns:
            AI answer as string
        """
        
        # Build context-aware prompt
        context_info = ""
        if document_context:
            context_info = f"Document: {document_context.get('filename', 'Unknown')}\n"
            if document_context.get('summary'):
                context_info += f"Summary: {document_context.get('summary', '')}\n"
        
        # Normalize to string (DB can contain NULL)
        safe_document_text = document_text or ""
        # Use more text (up to 15000 chars) for better context
        doc_content = safe_document_text[:15000]
        
        prompt = f"""You are an intelligent document assistant. Answer the user's question based on the provided document content.

{context_info}

Document Content:
{doc_content}

Question: {question}

Provide a clear, detailed answer based on the document. If the answer cannot be found in the document, say so explicitly."""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def chat(self, message: str, document_context: Optional[Dict] = None) -> str:
        """
        General chat with optional document context
        
        Args:
            message: User's message
            document_context: Optional document context dictionary with filename, summary, content_text
            
        Returns:
            AI response as string
        """
        
        if document_context:
            # Include document context in the conversation
            raw_doc = document_context.get('extracted_text')
            if raw_doc is None:
                raw_doc = document_context.get('content_text')
            if raw_doc is None:
                raw_doc = ""
            doc_content = str(raw_doc)[:15000]
            filename = document_context.get('filename', 'Unknown')
            summary = document_context.get('summary', '')
            
            prompt = f"""You are an AI assistant helping with document analysis. The user has uploaded a document and may ask questions about it.

Document: {filename}
Summary: {summary}

Document Content (for reference):
{doc_content[:15000]}

User Question: {message}

Answer the user's question. If it relates to the document, use the document content. If it's a general question, answer normally."""
        else:
            # General chat without document context
            prompt = f"""You are a helpful AI assistant. Answer the user's question in a friendly and informative way.

User Question: {message}"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")