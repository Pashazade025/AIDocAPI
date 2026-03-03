from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api import auth, documents, health, ai



# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI-powered document intelligence API with Google Gemini integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (for frontend if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(ai.router, prefix="/ai", tags=["AI Chat"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Document Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)