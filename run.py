"""
Simple runner script for the API
Usage: python run.py
"""

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid subprocess issues
        log_level="info"
    )