# File: MainAPI.py
# Path: Source/API/MainAPI.py
# Standard: AIDEV-PascalCase-2.0
# Ecosystem Requirement: Backend Python uses PascalCase per project standards
# Framework: FastAPI with Design Standard v2.0 compliance
# API Endpoints: REST conventions (lowercase paths) with PascalCase backend functions
# Database: Raw SQL with PascalCase elements (no SQLAlchemy)
# Created: 2025-07-07
# Last Modified: 2025-07-07  09:16PM
"""
Description: Anderson's Library FastAPI Backend - Design Standard v2.0
Enhanced API supporting both desktop web twin and mobile app interfaces
Maintains exact desktop functionality while following web ecosystem requirements
"""

import sys
import logging
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
Logger = logging.getLogger(__name__)

# ==================== PATH CONFIGURATION ====================

def GetProjectPaths() -> Dict[str, Path]:
    """
    Get all important project paths using Design Standard v2.0 structure
    Maintains compatibility with both development and production environments
    """
    # Get the directory containing this MainAPI.py file
    CurrentFile = Path(__file__).resolve()
    APIDirectory = CurrentFile.parent
    SourceDirectory = APIDirectory.parent
    ProjectRoot = SourceDirectory.parent
    
    # Define all important paths following Design Standard v2.0
    Paths = {
        'project_root': ProjectRoot,
        'source_dir': SourceDirectory,
        'api_dir': APIDirectory,
        'webpages_dir': ProjectRoot / 'WebPages',
        'database_path': ProjectRoot / 'Data' / 'Databases' / 'MyLibraryWeb.db',
        'assets_dir': ProjectRoot / 'Assets',
        'thumbnails_dir': ProjectRoot / 'Data' / 'Thumbs'
    }
    
    Logger.info(f"Project root detected: {Paths['project_root']}")
    Logger.info(f"WebPages directory: {Paths['webpages_dir']}")
    Logger.info(f"Database path: {Paths['database_path']}")
    
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

# ==================== PYDANTIC MODELS ====================

class BookSearchRequest(BaseModel):
    """Request model for book search operations"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page") 
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")
    
    @validator('query')
    def ValidateQuery(cls, Value):
        """Validate search query"""
        if not Value.strip():
            raise ValueError('Query cannot be empty')
        return Value.strip()

class BookResponse(BaseModel):
    """Response model for individual books"""
    id: int
    title: str
    author: Optional[str] = None
    category: Optional[str] = None
    subject: Optional[str] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

class BooksListResponse(BaseModel):
    """Response model for book lists"""
    books: List[BookResponse]
    total: int
    page: int
    limit: int
    has_more: bool
    message: Optional[str] = None

class CategoryResponse(BaseModel):
    """Response model for categories"""
    name: str
    count: int

class SubjectResponse(BaseModel):
    """Response model for subjects"""
    name: str
    category: Optional[str] = None
    count: int

class LibraryStatsResponse(BaseModel):
    """Response model for library statistics"""
    total_books: int
    total_categories: int
    total_subjects: int
    total_authors: int
    total_file_size: int
    last_updated: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    version: str
    database_connected: bool
    total_books: int

# ==================== FASTAPI APPLICATION ====================

# Initialize FastAPI application
App = FastAPI(
    title="Anderson's Library API",
    description="REST API for Anderson's Book Library - Design Standard v2.0",
    version="2.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
)

# Configure CORS for web development
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

# ==================== UTILITY FUNCTIONS ====================

def ConvertBookToResponse(BookRow: sqlite3.Row) -> BookResponse:
    """
    Convert database row to BookResponse model
    Handles null values and type conversions
    """
    return BookResponse(
        id=BookRow['Id'],
        title=BookRow['Title'] or 'Unknown Title',
        author=BookRow['Author'],
        category=BookRow['Category'],
        subject=BookRow['Subject'],
        page_count=BookRow['PageCount'],
        file_size=BookRow['FileSize'],
        created_date=BookRow['CreatedDate'],
        modified_date=BookRow['ModifiedDate']
    )

def CreatePaginatedResponse(Books: List[BookResponse], Total: int, Page: int, Limit: int, Message: str = None) -> BooksListResponse:
    """
    Create paginated response for book lists
    Calculates has_more flag and formats response
    """
    HasMore = (Page * Limit) < Total
    
    return BooksListResponse(
        books=Books,
        total=Total,
        page=Page,
        limit=Limit,
        has_more=HasMore,
        message=Message
    )

# ==================== API ENDPOINTS ====================

# Root endpoint
@App.get("/")
async def Root():
    """API root endpoint with basic information."""
    return {
        "name": "Anderson's Library API",
        "version": "2.0.0",
        "description": "Design Standard v2.0 compliant library management API",
        "endpoints": {
            "documentation": "/api/docs",
            "health": "/api/health",
            "books": "/api/books",
            "search": "/api/books/search",
            "categories": "/api/categories",
            "subjects": "/api/subjects",
            "stats": "/api/stats"
        },
        "author": "Herb Bowers - Project Himalaya",
        "timestamp": datetime.now().isoformat()
    }

# Health check endpoint
@App.get("/api/health", response_model=HealthResponse)
async def GetHealth():
    """
    Health check endpoint for monitoring and debugging
    Tests database connectivity and returns system status
    """
    try:
        DatabaseManager = GetDatabase()
        
        # Test database connection
        if DatabaseManager.Connect():
            # Get book count for health check
            BookCount = DatabaseManager.GetBookCount()
            DatabaseConnected = True
        else:
            BookCount = 0
            DatabaseConnected = False
        
        return HealthResponse(
            status="healthy" if DatabaseConnected else "degraded",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            database_connected=DatabaseConnected,
            total_books=BookCount
        )
        
    except Exception as Error:
        Logger.error(f"Health check failed: {Error}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            database_connected=False,
            total_books=0
        )

# Get all books with pagination and optional search/filter
@App.get("/api/books", response_model=BooksListResponse)
async def GetBooks(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search query for title/author"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    subject: Optional[str] = Query(default=None, description="Filter by subject")
):
    """
    Get paginated list of books with optional search and filtering
    FIXED: Added search parameter support to match frontend expectations
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Calculate offset for pagination
        Offset = (page - 1) * limit
        
        # FIXED: Use search/filter functionality if parameters provided
        if search or category or subject:
            # Use search functionality
            BooksData = DatabaseManager.SearchBooks(
                SearchQuery=search,
                Category=category,
                Subject=subject,
                Limit=limit,
                Offset=Offset
            )
            
            # Get total count for pagination
            TotalBooks = DatabaseManager.GetSearchResultCount(
                SearchQuery=search,
                Category=category,
                Subject=subject
            )
            
            # Build descriptive message
            FilterParts = []
            if search:
                FilterParts.append(f"Search: '{search}'")
            if category:
                FilterParts.append(f"Category: {category}")
            if subject:
                FilterParts.append(f"Subject: {subject}")
            
            Message = f"Filtered by {', '.join(FilterParts)}" if FilterParts else None
            
        else:
            # Get all books with pagination
            BooksData = DatabaseManager.GetBooksWithPagination(limit, Offset)
            TotalBooks = DatabaseManager.GetBookCount()
            Message = None
        
        # Convert to response models
        Books = [ConvertBookToResponse(BookRow) for BookRow in BooksData]
        
        return CreatePaginatedResponse(Books, TotalBooks, page, limit, Message)
        
    except Exception as Error:
        Logger.error(f"Error getting books: {Error}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve books: {str(Error)}")

# Search books
@App.post("/api/books/search", response_model=BooksListResponse)
async def SearchBooks(SearchRequest: BookSearchRequest):
    """
    Search books with Google-type instant search functionality
    Supports filtering by category, subject, rating
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Calculate offset
        Offset = (SearchRequest.page - 1) * SearchRequest.limit
        
        # Perform search
        BooksData = DatabaseManager.SearchBooks(
            SearchQuery=SearchRequest.query,
            Category=SearchRequest.filters.get('category'),
            Subject=SearchRequest.filters.get('subject'),
            Limit=SearchRequest.limit,
            Offset=Offset
        )
        
        # Get total count for pagination
        TotalCount = DatabaseManager.GetSearchResultCount(
            SearchQuery=SearchRequest.query,
            Category=SearchRequest.filters.get('category'),
            Subject=SearchRequest.filters.get('subject')
        )
        
        # Convert to response models
        Books = [ConvertBookToResponse(BookRow) for BookRow in BooksData]
        
        Message = f"Search results for '{SearchRequest.query}'"
        return CreatePaginatedResponse(Books, TotalCount, SearchRequest.page, SearchRequest.limit, Message)
        
    except Exception as Error:
        Logger.error(f"Error searching books: {Error}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(Error)}")

# Filter books by category/subject/rating
@App.get("/api/books/filter", response_model=BooksListResponse)
async def FilterBooks(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    subject: Optional[str] = Query(default=None, description="Filter by subject"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page")
):
    """
    Filter books by category, subject, and/or rating
    Maintains exact desktop filter functionality
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Calculate offset
        Offset = (page - 1) * limit
        
        # Apply filters
        BooksData = DatabaseManager.GetBooksByFilters(
            Category=category,
            Subject=subject,
            Limit=limit,
            Offset=Offset
        )
        
        # Get total count
        TotalCount = DatabaseManager.GetFilteredBookCount(
            Category=category,
            Subject=subject
        )
        
        # Convert to response models
        Books = [ConvertBookToResponse(BookRow) for BookRow in BooksData]
        
        # Create descriptive message
        FilterParts = []
        if category:
            FilterParts.append(f"Category: {category}")
        if subject:
            FilterParts.append(f"Subject: {subject}")
        if min_rating:
            FilterParts.append(f"Rating: {min_rating}+ stars")
        
        Message = f"Filtered by {', '.join(FilterParts)}" if FilterParts else "All books"
        
        return CreatePaginatedResponse(Books, TotalCount, page, limit, Message)
        
    except Exception as Error:
        Logger.error(f"Error filtering books: {Error}")
        raise HTTPException(status_code=500, detail=f"Filter failed: {str(Error)}")

# Get single book by ID
@App.get("/api/books/{book_id}", response_model=BookResponse)
async def GetBook(book_id: int = FastAPIPath(..., description="Book ID")):
    """Get detailed information for a specific book"""
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        BookData = DatabaseManager.GetBookById(book_id)
        
        if not BookData:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return ConvertBookToResponse(BookData)
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error getting book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve book: {str(Error)}")

# Get book thumbnail
@App.get("/api/books/{book_id}/thumbnail")
async def GetBookThumbnail(book_id: int = FastAPIPath(..., description="Book ID")):
    """
    Get book thumbnail image from database
    Returns image data or 404 if not found
    FIXED: Now retrieves thumbnails from database BLOB instead of files
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get thumbnail data from database
        ThumbnailData = DatabaseManager.GetBookThumbnail(book_id)
        
        if not ThumbnailData:
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        # Determine media type from image data
        MediaType = "image/jpeg"  # Default to JPEG
        if ThumbnailData.startswith(b'\x89PNG'):
            MediaType = "image/png"
        elif ThumbnailData.startswith(b'GIF87a') or ThumbnailData.startswith(b'GIF89a'):
            MediaType = "image/gif"
        elif ThumbnailData.startswith(b'RIFF') and b'WEBP' in ThumbnailData[:12]:
            MediaType = "image/webp"
        # JPEG detection - check for JPEG markers
        elif ThumbnailData.startswith(b'\xff\xd8'):
            MediaType = "image/jpeg"
        
        return StreamingResponse(
            io.BytesIO(ThumbnailData),
            media_type=MediaType,
            headers={
                "Cache-Control": "max-age=3600",  # Cache for 1 hour
                "Content-Length": str(len(ThumbnailData))
            }
        )
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error getting thumbnail for book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve thumbnail")

# Get categories
@App.get("/api/categories", response_model=List[CategoryResponse])
async def GetCategories():
    """
    Get all categories with book counts
    Used for populating dropdown filters
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        CategoriesData = DatabaseManager.GetCategoriesWithCounts()
        
        Categories = [
            CategoryResponse(name=Row['Category'], count=Row['BookCount'])
            for Row in CategoriesData
            if Row['Category']  # Filter out null categories
        ]
        
        return Categories
        
    except Exception as Error:
        Logger.error(f"Error getting categories: {Error}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(Error)}")

# Get subjects
@App.get("/api/subjects", response_model=List[SubjectResponse])
async def GetSubjects(category: Optional[str] = Query(default=None, description="Filter by category name")):
    """
    Get all subjects with book counts
    Optionally filtered by category NAME (not ID)
    FIXED: sqlite3.Row access and proper category filtering
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # FIXED: Use category name for filtering, not category_id
        if category:
            SubjectsData = DatabaseManager.GetSubjectsByCategory(category)
        else:
            SubjectsData = DatabaseManager.GetSubjectsWithCounts()
        
        # FIXED: Handle missing columns properly for sqlite3.Row
        Subjects = []
        for Row in SubjectsData:
            try:
                # Handle both possible column names and missing columns
                subject_name = Row['Subject'] if 'Subject' in Row.keys() else ''
                category_name = Row['Category'] if 'Category' in Row.keys() else ''
                book_count = Row['BookCount'] if 'BookCount' in Row.keys() else 0
                
                if subject_name:  # Only add if subject name exists
                    Subjects.append(SubjectResponse(
                        name=subject_name,
                        category=category_name,
                        count=book_count
                    ))
            except Exception as RowError:
                Logger.warning(f"Skipping row due to error: {RowError}")
                continue
        
        Logger.info(f"✅ Retrieved {len(Subjects)} subjects for category: {category or 'All'}")
        return Subjects
        
    except Exception as Error:
        Logger.error(f"Error getting subjects: {Error}")
        Logger.error(f"Error type: {type(Error)}")
        Logger.error(f"Category parameter: {category}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve subjects: {str(Error)}")

# Get library statistics
@App.get("/api/stats", response_model=LibraryStatsResponse)
async def GetLibraryStats():
    """
    Get comprehensive library statistics
    Used for dashboard and status display
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        Stats = DatabaseManager.GetLibraryStatistics()
        
        return LibraryStatsResponse(
            total_books=Stats.get('TotalBooks', 0),
            total_categories=Stats.get('TotalCategories', 0),
            total_subjects=Stats.get('TotalSubjects', 0),
            total_authors=Stats.get('TotalAuthors', 0),
            total_file_size=Stats.get('TotalFileSize', 0),
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as Error:
        Logger.error(f"Error getting library stats: {Error}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(Error)}")

# Server shutdown endpoint
@App.post("/api/shutdown")
async def ShutdownServer():
    """
    Shutdown the server gracefully
    Called when the webpage is closed
    """
    Logger.info("🛑 Server shutdown requested from web interface")
    
    # Use a background task to shutdown after responding
    import asyncio
    import os
    import signal
    
    async def delayed_shutdown():
        await asyncio.sleep(1)  # Give time for response to be sent
        Logger.info("💥 Terminating server process...")
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Start the shutdown task
    asyncio.create_task(delayed_shutdown())
    
    return {"message": "Server shutdown initiated"}

# ==================== STATIC FILE SERVING ====================

# Mount static files for web interface
if PROJECT_PATHS['webpages_dir'].exists():
    App.mount("/app", StaticFiles(directory=str(PROJECT_PATHS['webpages_dir']), html=True), name="webapp")
    Logger.info("✅ Web application mounted at /app")

if PROJECT_PATHS['assets_dir'].exists():
    App.mount("/assets", StaticFiles(directory=str(PROJECT_PATHS['assets_dir'])), name="assets")
    Logger.info("✅ Assets mounted at /assets")

# Serve main application at root
@App.get("/app")
async def ServeApp():
    """Serve the main web application"""
    WebAppPath = PROJECT_PATHS['webpages_dir'] / 'desktop-library.html'
    if WebAppPath.exists():
        return FileResponse(str(WebAppPath))
    else:
        raise HTTPException(status_code=404, detail="Web application not found")

@App.get("/mobile")
async def ServeMobileApp():
    """Serve the mobile web application"""
    MobileAppPath = PROJECT_PATHS['webpages_dir'] / 'mobile-library.html'
    if MobileAppPath.exists():
        return FileResponse(str(MobileAppPath))
    else:
        raise HTTPException(status_code=404, detail="Mobile application not found")

# ==================== ERROR HANDLERS ====================

@App.exception_handler(404)
async def NotFoundHandler(request: Request, exc: HTTPException):
    """Custom 404 handler with helpful information"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "available_endpoints": [
                "/api/docs",
                "/api/books",
                "/api/categories", 
                "/api/subjects",
                "/api/stats",
                "/app",
                "/mobile"
            ]
        }
    )

@App.exception_handler(500)
async def InternalServerErrorHandler(request: Request, exc: Exception):
    """Custom 500 handler with error logging"""
    Logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# ==================== STARTUP EVENTS ====================

@App.on_event("startup")
async def StartupEvent():
    """Application startup tasks"""
    Logger.info("🚀 Anderson's Library API v2.0 starting up...")
    Logger.info("📊 Design Standard v2.0 compliant")
    Logger.info(f"🗄️ Database: {PROJECT_PATHS['database_path']}")
    Logger.info(f"🌐 Web App: {PROJECT_PATHS['webpages_dir']}")
    
    # Test database connection
    try:
        DatabaseManager = GetDatabase()
        if DatabaseManager.Connect():
            BookCount = DatabaseManager.GetBookCount()
            Logger.info(f"✅ Database connected successfully - {BookCount} books loaded")
        else:
            Logger.warning("⚠️ Database connection failed")
    except Exception as Error:
        Logger.error(f"❌ Database startup error: {Error}")

@App.on_event("shutdown")
async def ShutdownEvent():
    """Application shutdown tasks"""
    Logger.info("🛑 Anderson's Library API v2.0 shutting down...")

# ==================== DEVELOPMENT SERVER ====================

def RunDevelopmentServer():
    """
    Run the development server with hot reload
    Design Standard v2.0 compliant configuration
    """
    uvicorn.run(
        "MainAPI:App",
        host="127.0.0.1",
        port=8001,
        reload=True,
        reload_dirs=[str(PROJECT_PATHS['source_dir'])],
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    Logger.info("Starting Anderson's Library API v2.0 - Design Standard v2.0")
    RunDevelopmentServer()