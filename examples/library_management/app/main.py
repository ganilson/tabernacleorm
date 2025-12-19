"""
Main FastAPI Application
Library Management System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, close_db
from app.config import settings

# Import controllers
from app.controllers import auth_controller, book_controller, loan_controller, stats_controller

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Complete Library Management System with TabernacleORM"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(book_controller.router, prefix="/api/books", tags=["Books"])
app.include_router(loan_controller.router, prefix="/api/loans", tags=["Loans"])
app.include_router(stats_controller.router, prefix="/api/stats", tags=["Statistics"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database on shutdown"""
    await close_db()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Library Management System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
