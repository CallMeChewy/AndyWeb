# File: MainAPI.py
# Path: Source/API/MainAPI.py
# Standard: AIDEV-PascalCase-1.9
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:48PM
"""
Description: FastAPI main application for AndyWeb book library system
Provides REST API endpoints for book browsing, search, and library management.
Enhanced with robust path handling and proper static file serving.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import logging
import json
from pathlib import Path
import mimetypes
import io
import base64
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
Logger = logging.getLogger(__name__)

# Robust path detection - works regardless of execution context
def GetProjectPaths():
    """Get project paths with robust detection."""
    # Get the directory containing this MainAPI.py file
    CurrentFile = Path(__file__).resolve()
    APIDirectory = CurrentFile.parent
    SourceDirectory = APIDirectory.parent
    ProjectRoot = SourceDirectory.parent
    
    # Define all important paths
    Paths = {
        'project_root': ProjectRoot,
        'source_dir': SourceDirectory,
        'api_dir': APIDirectory,
        'webpages_dir': ProjectRoot / 'WebPages',
        'database_path': ProjectRoot / 'Data' / 'Databases' / 'MyLibraryWeb.db'
    }
    
    Logger.info(f"Project root detected: {Paths['project_root']}")
    Logger.info(f"WebPages directory: {Paths['webpages_dir']}")
    
    return Paths

# Get paths and validate
try:
    PROJECT_PATHS = GetProjectPaths()
    
    # Validate critical paths exist
    if not PROJECT_PATHS['webpages_dir'].exists():
        Logger.error(f"WebPages directory not found: {PROJECT_PATHS['webpages_dir']}")
        raise FileNotFoundError(f"WebPages directory not found: {PROJECT_PATHS['webpages_dir']}")
        
    if not PROJECT_PATHS['database_path'].exists():
        Logger.warning(f"Database not found: {PROJECT_PATHS['database_path']}")
        
    Logger.info("✅ Path validation successful")
    
except Exception as Error:
    Logger.error(f"❌ Path setup failed: {Error}")
    Logger.error("Current working directory: " + str(Path.cwd()))
    Logger.error("__file__ location: " + str(Path(__file__).resolve()))
    raise

# Add Source directory to Python path for imports
SourcePath = str(PROJECT_PATHS['source_dir'])
if SourcePath not in sys.path:
    sys.path.insert(0, SourcePath)
    Logger.info(f"Added to Python path: {SourcePath}")

# Import our custom modules
try:
    from Core.DatabaseManager import DatabaseManager
    Logger.info("✅ DatabaseManager imported successfully")
except ImportError as Error:
    Logger.error(f"❌ Failed to import DatabaseManager: {Error}")
    Logger.error(f"Python path: {sys.path}")
    raise

# Initialize FastAPI application
App = FastAPI(
    title="AndyWeb Library API",
    description="REST API for Anderson's Book Library - Web Edition",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
)

# Configure CORS for frontend development
App.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency with robust path handling
def GetDatabase() -> DatabaseManager:
    """Dependency to get database manager instance."""
    DatabasePath = str(PROJECT_PATHS['database_path'])
    return DatabaseManager(DatabasePath)

# Root endpoint
@App.get("/")
async def Root():
    """API root endpoint with basic information."""
    return {
        "message": "AndyWeb Library API",
        "version": "1.0.0",
        "status": "running",
        "paths": {
            "project_root": str(PROJECT_PATHS['project_root']),
            "webpages_available": PROJECT_PATHS['webpages_dir'].exists(),
            "database_available": PROJECT_PATHS['database_path'].exists()
        },
        "endpoints": {
            "docs": "/api/docs",
            "books": "/api/books",
            "categories": "/api/categories",
            "subjects": "/api/subjects",
            "stats": "/api/stats"
        }
    }

# Health check endpoint
@App.get("/api/health")
async def HealthCheck(Db: DatabaseManager = Depends(GetDatabase)):
    """Health check endpoint for monitoring."""
    try:
        with Db:
            Stats = Db.GetDatabaseStats()
            return {
                "status": "healthy",
                "database": "connected",
                "total_books": Stats.get('TotalBooks', 0),
                "webpages_available": PROJECT_PATHS['webpages_dir'].exists()
            }
    except Exception as Error:
        Logger.error(f"Health check failed: {Error}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Books endpoints
@App.get("/api/books")
async def GetBooks(
    limit: int = Query(50, ge=1, le=200, description="Number of books to return"),
    offset: int = Query(0, ge=0, description="Number of books to skip"),
    search: Optional[str] = Query(None, description="Search term for title/author"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    Db: DatabaseManager = Depends(GetDatabase)
) -> Dict[str, Any]:
    """Get books with optional filtering and pagination."""
    try:
        with Db:
            Books = Db.GetBooks(
                Limit=limit,
                Offset=offset,
                SearchTerm=search or "",
                CategoryId=category_id,
                SubjectId=subject_id
            )
            
            # Convert thumbnail data for JSON response
            for Book in Books:
                if Book.get('ThumbnailImage'):
                    # Convert BLOB to base64 for frontend
                    ThumbnailBytes = Book['ThumbnailImage']
                    if isinstance(ThumbnailBytes, bytes):
                        Book['ThumbnailImage'] = base64.b64encode(ThumbnailBytes).decode('utf-8')
                        Book['HasThumbnail'] = True
                    else:
                        Book['ThumbnailImage'] = None
                        Book['HasThumbnail'] = False
                else:
                    Book['HasThumbnail'] = False
            
            return {
                "books": Books,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(Books),
                    "has_more": len(Books) == limit
                },
                "filters": {
                    "search": search,
                    "category_id": category_id,
                    "subject_id": subject_id
                }
            }
            
    except Exception as Error:
        Logger.error(f"Error getting books: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books")

@App.get("/api/books/{book_id}")
async def GetBookById(book_id: int, Db: DatabaseManager = Depends(GetDatabase)):
    """Get detailed information for a specific book."""
    try:
        with Db:
            Book = Db.GetBookById(book_id)
            
            if not Book:
                raise HTTPException(status_code=404, detail="Book not found")
                
            # Process thumbnail for response
            if Book.get('ThumbnailImage'):
                ThumbnailBytes = Book['ThumbnailImage']
                if isinstance(ThumbnailBytes, bytes):
                    Book['ThumbnailImage'] = base64.b64encode(ThumbnailBytes).decode('utf-8')
                    Book['HasThumbnail'] = True
                else:
                    Book['ThumbnailImage'] = None
                    Book['HasThumbnail'] = False
            else:
                Book['HasThumbnail'] = False
                
            # Update last opened timestamp
            Db.UpdateBookLastOpened(book_id)
            
            return {"book": Book}
            
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error getting book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve book")

# Categories endpoints
@App.get("/api/categories")
async def GetCategories(Db: DatabaseManager = Depends(GetDatabase)):
    """Get all categories with book counts."""
    try:
        with Db:
            Categories = Db.GetCategories()
            return {"categories": Categories}
            
    except Exception as Error:
        Logger.error(f"Error getting categories: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

# Subjects endpoints
@App.get("/api/subjects")
async def GetSubjects(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    Db: DatabaseManager = Depends(GetDatabase)
):
    """Get subjects, optionally filtered by category."""
    try:
        with Db:
            Subjects = Db.GetSubjects(CategoryId=category_id)
            return {"subjects": Subjects}
            
    except Exception as Error:
        Logger.error(f"Error getting subjects: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subjects")

# Statistics endpoint
@App.get("/api/stats")
async def GetStats(Db: DatabaseManager = Depends(GetDatabase)):
    """Get database statistics and recent activity."""
    try:
        with Db:
            Stats = Db.GetDatabaseStats()
            return {"stats": Stats}
            
    except Exception as Error:
        Logger.error(f"Error getting stats: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# File serving endpoint (for PDF files when locally available)
@App.get("/api/books/{book_id}/file")
async def ServeBookFile(book_id: int, Db: DatabaseManager = Depends(GetDatabase)):
    """Serve book file for reading (when available locally)."""
    try:
        with Db:
            Book = Db.GetBookById(book_id)
            
            if not Book:
                raise HTTPException(status_code=404, detail="Book not found")
                
            FilePath = Path(Book.get('FilePath', ''))
            
            # Check if file exists locally
            if not FilePath.exists():
                raise HTTPException(
                    status_code=404, 
                    detail="Book file not found. May require cloud access."
                )
                
            # Determine content type
            ContentType, _ = mimetypes.guess_type(str(FilePath))
            if not ContentType:
                ContentType = 'application/octet-stream'
                
            # Stream file response
            def FileIterator():
                with open(FilePath, 'rb') as FileHandle:
                    while True:
                        Chunk = FileHandle.read(8192)  # 8KB chunks
                        if not Chunk:
                            break
                        yield Chunk
                        
            return StreamingResponse(
                FileIterator(),
                media_type=ContentType,
                headers={
                    "Content-Disposition": f"inline; filename=\"{FilePath.name}\"",
                    "Cache-Control": "public, max-age=3600"
                }
            )
            
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error serving file for book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail="Failed to serve book file")

# Thumbnail endpoint
@App.get("/api/books/{book_id}/thumbnail")
async def GetBookThumbnail(book_id: int, Db: DatabaseManager = Depends(GetDatabase)):
    """Get book thumbnail image."""
    try:
        with Db:
            Book = Db.GetBookById(book_id)
            
            if not Book or not Book.get('ThumbnailImage'):
                raise HTTPException(status_code=404, detail="Thumbnail not found")
                
            ThumbnailBytes = Book['ThumbnailImage']
            if not isinstance(ThumbnailBytes, bytes):
                raise HTTPException(status_code=404, detail="Invalid thumbnail data")
                
            return StreamingResponse(
                io.BytesIO(ThumbnailBytes),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
                }
            )
            
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error getting thumbnail for book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve thumbnail")

# Mount static files with robust path handling
try:
    WebPagesPath = PROJECT_PATHS['webpages_dir']
    if WebPagesPath.exists():
        App.mount("/static", StaticFiles(directory=str(WebPagesPath)), name="static")
        Logger.info(f"✅ Static files mounted: {WebPagesPath}")
    else:
        Logger.warning(f"⚠️ WebPages directory not found, static files not mounted: {WebPagesPath}")
except Exception as Error:
    Logger.error(f"❌ Failed to mount static files: {Error}")

# Serve main frontend page with path validation
@App.get("/app")
async def ServeFrontend():
    """Serve the main frontend application."""
    try:
        IndexPath = PROJECT_PATHS['webpages_dir'] / 'index.html'
        
        if not IndexPath.exists():
            Logger.error(f"Frontend index.html not found: {IndexPath}")
            raise HTTPException(
                status_code=404, 
                detail=f"Frontend not available. Expected: {IndexPath}"
            )
            
        return FileResponse(str(IndexPath))
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error serving frontend: {Error}")
        raise HTTPException(status_code=500, detail="Failed to serve frontend")

# Startup event to validate environment
@App.on_event("startup")
async def StartupEvent():
    """Validate environment on startup."""
    Logger.info("🚀 AndyWeb API starting up...")
    Logger.info(f"📁 Project root: {PROJECT_PATHS['project_root']}")
    Logger.info(f"🌐 WebPages dir: {PROJECT_PATHS['webpages_dir']} (exists: {PROJECT_PATHS['webpages_dir'].exists()})")
    Logger.info(f"🗃️ Database: {PROJECT_PATHS['database_path']} (exists: {PROJECT_PATHS['database_path'].exists()})")
    
    # Test database connection
    try:
        TestDb = DatabaseManager(str(PROJECT_PATHS['database_path']))
        with TestDb:
            Stats = TestDb.GetDatabaseStats()
            Logger.info(f"📚 Database connected: {Stats.get('TotalBooks', 0)} books found")
    except Exception as Error:
        Logger.error(f"❌ Database connection failed: {Error}")

if __name__ == "__main__":
    import uvicorn
    
    Logger.info("Starting AndyWeb API server...")
    uvicorn.run(
        "MainAPI:App",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload during development
        log_level="info"
    )