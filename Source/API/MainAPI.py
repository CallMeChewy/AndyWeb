# File: MainAPI.py
# Path: /home/herb/Desktop/AndyWeb/Source/API/MainAPI.py
# Standard: AIDEV-PascalCase-2.1
# Ecosystem Requirement: Backend Python uses PascalCase per project standards
# Framework: FastAPI with Design Standard v2.1 compliance
# API Endpoints: REST conventions (lowercase paths) with PascalCase backend functions
# Database: Raw SQL with PascalCase elements (no SQLAlchemy)
# Created: 2025-07-07
# Last Modified: 2025-07-25 08:25AM
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

from fastapi import FastAPI, HTTPException, Query, Path as FastAPIPath, Request, Depends, Form, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
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
    from Core.RateLimiter import get_rate_limiter
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
    
    @field_validator('query')
    @classmethod
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
    subject_count: Optional[int] = 0

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

# ==================== USER AUTHENTICATION MODELS ====================

class UserRegistrationRequest(BaseModel):
    """Request model for user registration"""
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$', description="Valid email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (8-100 characters)")
    username: Optional[str] = Field(default=None, min_length=3, max_length=30, description="Username (optional)")
    subscription_tier: str = Field(default='free', pattern=r'^(free|scholar|researcher|institution)$', description="Subscription tier")
    
    @field_validator('email')
    @classmethod
    def ValidateEmail(cls, Value):
        """Validate email format"""
        return Value.lower().strip()
    
    @field_validator('password')
    @classmethod
    def ValidatePassword(cls, Value):
        """Basic password validation"""
        if len(Value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return Value

class UserLoginRequest(BaseModel):
    """Request model for user login"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    @field_validator('email')
    @classmethod
    def ValidateEmail(cls, Value):
        return Value.lower().strip()

class UserResponse(BaseModel):
    """Response model for user information"""
    id: int
    email: str
    username: Optional[str] = None
    subscription_tier: str
    is_active: bool
    email_verified: bool
    last_login_date: Optional[str] = None
    created_date: str
    
class AuthResponse(BaseModel):
    """Response model for authentication"""
    user: UserResponse
    session_token: str
    refresh_token: str
    expires_at: str
    message: str

class LoginResponse(BaseModel):
    """Response model for successful login"""
    user: UserResponse
    session_token: str
    refresh_token: str
    expires_at: str
    message: str = "Login successful"

class RegisterResponse(BaseModel):
    """Response model for successful registration"""
    user: UserResponse
    message: str = "Registration successful"
    email_verification_required: bool = True

class UserStatsResponse(BaseModel):
    """Response model for user statistics"""
    total_users: int
    users_by_tier: Dict[str, int]
    new_users_today: int
    active_sessions: int

# ==================== FASTAPI APPLICATION ====================

# Initialize FastAPI application
App = FastAPI(
    title="BowersWorld.com API",
    description="REST API for BowersWorld.com Educational Library Platform - Design Standard v2.1",
    version="2.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
)

# Security scheme for JWT authentication
Security = HTTPBearer(auto_error=False)

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

# Authentication dependency
async def GetCurrentUser(credentials: HTTPAuthorizationCredentials = Depends(Security)) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current authenticated user from session token
    Returns user info or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        DatabaseManager = GetDatabase()
        if not DatabaseManager.Connect():
            return None
        
        # Validate session token
        SessionData = DatabaseManager.ValidateSession(credentials.credentials)
        if SessionData:
            return {
                'Id': SessionData['UserId'],
                'Email': SessionData['Email'],
                'Username': SessionData['Username'],
                'SubscriptionTier': SessionData['SubscriptionTier']
            }
        
        return None
        
    except Exception as Error:
        Logger.error(f"Authentication error: {Error}")
        return None

# Protected route dependency
async def RequireAuth(current_user: Dict[str, Any] = Depends(GetCurrentUser)) -> Dict[str, Any]:
    """
    Dependency that requires authentication
    Raises 401 if user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# Rate limiting dependency
async def CheckRateLimit(request: Request):
    """
    Check rate limits for API endpoints
    Educational mission: Protect from abuse while preserving access
    """
    try:
        rate_limiter = get_rate_limiter()
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        
        # Check rate limit
        allowed, rate_info = rate_limiter.is_allowed(client_ip, endpoint)
        
        if not allowed:
            headers = {
                "X-RateLimit-Limit": str(rate_info.get('limit', 0)),
                "X-RateLimit-Remaining": str(rate_info.get('remaining', 0)),
                "X-RateLimit-Reset": str(rate_info.get('reset_time', 0)),
                "Retry-After": str(rate_info.get('retry_after', 60))
            }
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers=headers
            )
        
        # Add rate limit headers to successful responses
        request.state.rate_limit_info = rate_info
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Rate limiting error: {Error}")
        # Don't block requests if rate limiter fails

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

# ==================== AUTHENTICATION API ENDPOINTS ===================

@App.post("/api/auth/register", response_model=RegisterResponse, dependencies=[Depends(CheckRateLimit)])
async def RegisterUser(registration: UserRegistrationRequest, request: Request):
    """
    Register new user account for BowersWorld.com
    Creates user with specified subscription tier and sends verification email
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get client info for logging
        ClientIp = request.client.host if request.client else None
        UserAgent = request.headers.get("user-agent")
        
        # Create user account
        UserResult = DatabaseManager.CreateUser(
            Email=registration.email,
            Password=registration.password,
            Username=registration.username,
            SubscriptionTier=registration.subscription_tier
        )
        
        if not UserResult:
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Handle specific error cases
        if isinstance(UserResult, dict) and 'error' in UserResult:
            if UserResult['error'] == 'email_exists':
                raise HTTPException(status_code=409, detail="Email address already registered")
            elif UserResult['error'] == 'username_exists':
                raise HTTPException(status_code=409, detail="Username already taken")
            else:
                raise HTTPException(status_code=400, detail="Registration failed")
        
        # Log registration activity
        DatabaseManager.LogUserActivity(
            UserId=UserResult['Id'],
            ActivityType='user_registered',
            ActivityData={
                'email': registration.email,
                'subscription_tier': registration.subscription_tier,
                'registration_method': 'web_form'
            },
            IpAddress=ClientIp,
            UserAgent=UserAgent
        )
        
        UserResponse = ConvertUserToResponse(UserResult)
        
        return RegisterResponse(
            user=UserResponse,
            message=f"Registration successful! Welcome to BowersWorld.com, {registration.subscription_tier} member.",
            email_verification_required=True
        )
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Registration error: {Error}")
        raise HTTPException(status_code=500, detail="Registration failed")

@App.post("/api/auth/login", response_model=LoginResponse, dependencies=[Depends(CheckRateLimit)])
async def LoginUser(login: UserLoginRequest, request: Request):
    """
    Authenticate user login and create session
    Returns user info and session tokens for BowersWorld.com access
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get client info for logging
        ClientIp = request.client.host if request.client else None
        UserAgent = request.headers.get("user-agent")
        
        # Authenticate user
        UserResult = DatabaseManager.AuthenticateUser(login.email, login.password)
        
        if not UserResult:
            # Log failed login attempt
            DatabaseManager.LogUserActivity(
                UserId=None,
                ActivityType='login_failed',
                ActivityData={'email': login.email, 'reason': 'invalid_credentials'},
                IpAddress=ClientIp,
                UserAgent=UserAgent
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Handle specific error cases
        if isinstance(UserResult, dict) and 'error' in UserResult:
            if UserResult['error'] == 'account_locked':
                raise HTTPException(status_code=423, detail="Account temporarily locked due to failed login attempts")
        
        # Create user session
        SessionResult = DatabaseManager.CreateUserSession(
            UserId=UserResult['Id'],
            IpAddress=ClientIp,
            UserAgent=UserAgent
        )
        
        if not SessionResult:
            raise HTTPException(status_code=500, detail="Failed to create user session")
        
        # Log successful login
        DatabaseManager.LogUserActivity(
            UserId=UserResult['Id'],
            ActivityType='user_login',
            ActivityData={
                'email': login.email,
                'subscription_tier': UserResult['SubscriptionTier'],
                'login_method': 'web_form'
            },
            IpAddress=ClientIp,
            UserAgent=UserAgent
        )
        
        UserResponse = ConvertUserToResponse(UserResult)
        
        return LoginResponse(
            user=UserResponse,
            session_token=SessionResult['session_token'],
            refresh_token=SessionResult['refresh_token'],
            expires_at=SessionResult['expires_at'],
            message=f"Welcome back to BowersWorld.com, {UserResult['SubscriptionTier']} member!"
        )
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Login error: {Error}")
        raise HTTPException(status_code=500, detail="Login failed")

@App.post("/api/auth/logout")
async def LogoutUser(current_user: Dict[str, Any] = Depends(RequireAuth), 
                   credentials: HTTPAuthorizationCredentials = Depends(Security)):
    """
    Logout user and deactivate session
    Requires valid authentication token
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Logout user by deactivating session
        Success = DatabaseManager.LogoutUser(credentials.credentials)
        
        if Success:
            # Log logout activity
            DatabaseManager.LogUserActivity(
                UserId=current_user['Id'],
                ActivityType='user_logout',
                ActivityData={'email': current_user['Email']}
            )
            
            return {"message": "Logout successful"}
        else:
            raise HTTPException(status_code=500, detail="Logout failed")
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Logout error: {Error}")
        raise HTTPException(status_code=500, detail="Logout failed")

@App.get("/api/auth/profile", response_model=UserResponse)
async def GetUserProfile(current_user: Dict[str, Any] = Depends(RequireAuth)):
    """
    Get current user profile information
    Requires authentication
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get full user details
        UserData = DatabaseManager.GetUserById(current_user['Id'])
        
        if not UserData:
            raise HTTPException(status_code=404, detail="User not found")
        
        return ConvertUserToResponse(UserData)
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Profile error: {Error}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@App.get("/api/auth/stats", response_model=UserStatsResponse)
async def GetUserStats(current_user: Dict[str, Any] = Depends(RequireAuth)):
    """
    Get BowersWorld.com user registration and subscription statistics
    Requires authentication (admin access would be added later)
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        Stats = DatabaseManager.GetUserStatistics()
        
        return UserStatsResponse(
            total_users=Stats['TotalUsers'],
            users_by_tier=Stats['UsersByTier'],
            new_users_today=Stats['NewUsersToday'],
            active_sessions=Stats['ActiveSessions']
        )
        
    except Exception as Error:
        Logger.error(f"User stats error: {Error}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")

@App.post("/api/auth/cleanup-sessions")
async def CleanupExpiredSessions(current_user: Dict[str, Any] = Depends(RequireAuth)):
    """
    Clean up expired user sessions
    Maintenance endpoint for session management
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        CleanedCount = DatabaseManager.CleanupExpiredSessions()
        
        return {
            "message": f"Cleaned up {CleanedCount} expired sessions",
            "cleaned_count": CleanedCount
        }
        
    except Exception as Error:
        Logger.error(f"Session cleanup error: {Error}")
        raise HTTPException(status_code=500, detail="Session cleanup failed")

# ==================== LIBRARY API ENDPOINTS (PROTECTED) ====================

# Convert database row to response model - defined earlier in the function
def ConvertUserToResponse(UserRow: sqlite3.Row) -> UserResponse:
    """Convert database user row to UserResponse model"""
    return UserResponse(
        id=UserRow['Id'],
        email=UserRow['Email'],
        username=UserRow['Username'],
        subscription_tier=UserRow['SubscriptionTier'],
        is_active=bool(UserRow['IsActive']),
        email_verified=bool(UserRow['EmailVerified']),
        last_login_date=UserRow['LastLoginDate'],
        created_date=UserRow['CreatedDate']
    )

# ==================== ORIGINAL LIBRARY API ENDPOINTS ====================

# Root endpoint - Commented out to allow StaticFiles to serve index.html
# @App.get("/")
# async def Root():
#     """API root endpoint with basic information."""
#     return {
#         "name": "Anderson's Library API",
#         "version": "2.0.0",
#         "description": "Design Standard v2.0 compliant library management API",
#         "endpoints": {
#             "documentation": "/api/docs",
#             "health": "/api/health",
#             "books": "/api/books",
#             "search": "/api/books/search",
#             "categories": "/api/categories",
#             "subjects": "/api/subjects",
#             "stats": "/api/stats"
#         },
#         "author": "Herb Bowers - Project Himalaya",
#         "timestamp": datetime.now().isoformat()
#     }

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
        Logger.info(f"Filtering books: Category='{category}', Subject='{subject}', Limit={limit}, Offset={Offset}")
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

# Get book PDF
@App.get("/api/books/{book_id}/pdf")
async def GetBookPDF(book_id: int = FastAPIPath(..., description="Book ID")):
    """
    Get book PDF for reading
    Returns PDF file or 404 if not found
    Opens PDF in browser for reading
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get book info to get the title for filename
        BookData = DatabaseManager.GetBookById(book_id)
        if not BookData:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Try to get PDF data from database first
        try:
            PDFData = DatabaseManager.GetBookPDF(book_id)
            if PDFData:
                # Clean filename for download
                SafeTitle = "".join(c for c in BookData['Title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                SafeTitle = SafeTitle.replace(' ', '_')
                
                return StreamingResponse(
                    io.BytesIO(PDFData),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"inline; filename={SafeTitle}.pdf",
                        "Content-Length": str(len(PDFData))
                    }
                )
        except Exception as DbError:
            Logger.warning(f"PDF not found in database for book {book_id}: {DbError}")
        
        # If no PDF in database, try file system
        BookTitle = BookData['Title']
        PossiblePaths = [
            PROJECT_PATHS['project_root'] / 'Data' / 'Books' / f"{BookTitle}.pdf",
            PROJECT_PATHS['project_root'] / 'Anderson eBooks' / f"{BookTitle}.pdf",
            PROJECT_PATHS['project_root'] / 'Books' / f"{BookTitle}.pdf"
        ]
        
        for PdfPath in PossiblePaths:
            if PdfPath.exists():
                return FileResponse(
                    path=str(PdfPath),
                    media_type="application/pdf",
                    filename=f"{BookTitle}.pdf",
                    headers={"Content-Disposition": "inline"}
                )
        
        # If no PDF found anywhere, return 404
        raise HTTPException(status_code=404, detail=f"PDF not found for book: {BookTitle}")
        
    except HTTPException:
        raise
    except Exception as Error:
        Logger.error(f"Error getting PDF for book {book_id}: {Error}")
        raise HTTPException(status_code=500, detail="Failed to retrieve PDF")

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
            CategoryResponse(name=Row['Category'], count=Row['BookCount'], subject_count=Row['SubjectCount'] if 'SubjectCount' in Row.keys() else 0)
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
        Logger.info(f"GetSubjects API called with category='{category}'")
        if category:
            Logger.info(f"Calling GetSubjectsByCategory with category='{category}'")
            SubjectsData = DatabaseManager.GetSubjectsByCategory(category)
        else:
            Logger.info("Calling GetSubjectsWithCounts (no category filter)")
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

# Test endpoint for logo
@App.get("/test-logo")
async def test_logo():
    """Test endpoint to check if logo file exists"""
    logo_path = PROJECT_PATHS['webpages_dir'] / 'Assets' / 'BowersWorld.png'
    if logo_path.exists():
        return {"status": "found", "path": str(logo_path), "size": logo_path.stat().st_size}
    else:
        return {"status": "not found", "path": str(logo_path)}

# ==================== STATIC FILE SERVING ====================

# Mount static files for web interface
if PROJECT_PATHS['webpages_dir'].exists():
    from fastapi.responses import FileResponse
    
    # Add root route to serve desktop-library.html
    @App.get("/")
    async def serve_root():
        return FileResponse(str(PROJECT_PATHS['webpages_dir'] / 'desktop-library.html'))
    
    # Add auth page route
    @App.get("/auth.html")
    async def serve_auth():
        return FileResponse(str(PROJECT_PATHS['webpages_dir'] / 'auth.html'))
    
    # Mount WebPages directory to serve JS, CSS, and other static files
    App.mount("/JS", StaticFiles(directory=str(PROJECT_PATHS['webpages_dir'] / 'JS')), name="js")
    App.mount("/CSS", StaticFiles(directory=str(PROJECT_PATHS['webpages_dir'] / 'CSS')), name="css")
    Logger.info("✅ Web application static files mounted")
    Logger.info("✅ Root route configured to serve desktop-library.html")

# Mount WebPages/Assets directory for images
webpages_assets_dir = PROJECT_PATHS['webpages_dir'] / 'Assets'
Logger.info(f"Looking for assets directory at: {webpages_assets_dir}")
if webpages_assets_dir.exists():
    App.mount("/assets", StaticFiles(directory=str(webpages_assets_dir)), name="assets")
    Logger.info("✅ WebPages/Assets mounted at /assets")
    Logger.info(f"Assets directory contents: {list(webpages_assets_dir.iterdir())}")
elif PROJECT_PATHS['assets_dir'].exists():
    App.mount("/assets", StaticFiles(directory=str(PROJECT_PATHS['assets_dir'])), name="assets")
    Logger.info("✅ Assets mounted at /assets")
else:
    Logger.warning("⚠️ No assets directory found")

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
                "/mobile",
                "/api/books/{id}/pdf"
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