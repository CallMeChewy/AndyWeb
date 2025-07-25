# File: DatabaseManager.py
# Path: /home/herb/Desktop/AndyWeb/Source/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-2.1
# Backend Python: Uses PascalCase per project standards
# Database: Raw SQL with PascalCase elements (NO SQLAlchemy per Design Standard v2.1)
# SQL Naming: ALL database elements use PascalCase (tables, columns, indexes, constraints)
# Created: 2025-07-07
# Last Modified: 2025-07-25 08:15AM
"""
Description: Enhanced Database Manager - Design Standard v2.0
Handles all database operations for Anderson's Library web/mobile applications
Supports both desktop twin and mobile app functionality with raw SQL
Maintains exact desktop functionality while optimizing for web performance
"""

import sqlite3
import logging
import os
import hashlib
import secrets
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
import json
from passlib.context import CryptContext
from .AuthConfig import AuthConfig

class DatabaseManager:
    """
    Enhanced Database Manager for Anderson's Library
    Supports web, mobile, and desktop applications with unified functionality
    Uses raw SQL with PascalCase naming per Design Standard v2.0
    """
    
    def __init__(self, DatabasePath: str):
        """
        Initialize database manager with connection pooling and optimization
        
        Args:
            DatabasePath: Path to SQLite database file
        """
        self.DatabasePath = DatabasePath
        self.Connection: Optional[sqlite3.Connection] = None
        self.Logger = logging.getLogger(self.__class__.__name__)
        
        # Password hashing configuration for BowersWorld.com user authentication
        self.PwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Connection configuration for web performance
        self.ConnectionConfig = {
            'timeout': 30.0,
            'check_same_thread': False,  # Allow multi-threaded access
            'isolation_level': None,     # Autocommit mode for better performance
        }
        
        self.Logger.debug(f"DatabaseManager v2.1 initialized for: {DatabasePath}")
        self.InitializeUserTables()

    def Connect(self) -> bool:
        """
        Establish database connection with optimization for web applications
        Includes connection pooling and performance tuning
        """
        try:
            if not os.path.exists(self.DatabasePath):
                self.Logger.error(f"Database file not found: {self.DatabasePath}")
                return False
            
            # Create connection with performance optimizations
            self.Connection = sqlite3.connect(
                self.DatabasePath, 
                **self.ConnectionConfig
            )
            
            # Configure for better web performance
            self.Connection.row_factory = sqlite3.Row  # Enable column access by name
            self.Connection.execute("PRAGMA journal_mode=WAL")     # Better concurrency
            self.Connection.execute("PRAGMA synchronous=NORMAL")   # Faster writes
            self.Connection.execute("PRAGMA cache_size=10000")     # Larger cache
            self.Connection.execute("PRAGMA temp_store=MEMORY")    # Memory temp tables
            self.Connection.execute("PRAGMA mmap_size=268435456")  # Memory mapping
            
            # Test connection
            TestResult = self.Connection.execute("SELECT COUNT(*) FROM Books").fetchone()
            BookCount = TestResult[0] if TestResult else 0
            
            self.Logger.debug(f"✅ Database connected successfully - {BookCount} books available")
            return True
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Database connection failed: {Error}")
            return False
        except Exception as Error:
            self.Logger.error(f"Unexpected error connecting to database: {Error}")
            return False

    def Disconnect(self) -> None:
        """Close database connection gracefully"""
        if self.Connection:
            try:
                self.Connection.close()
                self.Logger.info("Database connection closed")
            except Exception as Error:
                self.Logger.error(f"Error closing database connection: {Error}")
            finally:
                self.Connection = None

    def ExecuteQuery(self, Query: str, Parameters: Tuple = ()) -> List[sqlite3.Row]:
        """
        Execute SELECT query with parameters and error handling
        
        Args:
            Query: SQL query string with PascalCase column names
            Parameters: Query parameters for safe execution
            
        Returns:
            List of database rows or empty list on error
        """
        if not self.Connection:
            self.Logger.error("No database connection available")
            return []
        
        try:
            Cursor = self.Connection.execute(Query, Parameters)
            Results = Cursor.fetchall()
            return Results
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Query execution failed: {Error}")
            self.Logger.error(f"Query: {Query}")
            self.Logger.error(f"Parameters: {Parameters}")
            return []

    def ExecuteNonQuery(self, Query: str, Parameters: Tuple = ()) -> bool:
        """
        Execute INSERT/UPDATE/DELETE query with parameters
        
        Args:
            Query: SQL query string
            Parameters: Query parameters for safe execution
            
        Returns:
            True if successful, False otherwise
        """
        if not self.Connection:
            self.Logger.error("No database connection available")
            return False
        
        try:
            self.Connection.execute(Query, Parameters)
            self.Connection.commit()
            return True
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Non-query execution failed: {Error}")
            self.Logger.error(f"Query: {Query}")
            self.Logger.error(f"Parameters: {Parameters}")
            return False

    # ==================== BOOK RETRIEVAL METHODS ====================

    def GetAllBooks(self) -> List[sqlite3.Row]:
        """
        Get all books from database - maintains desktop functionality
        Optimized for web applications with reasonable limits
        """
        Query = """
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        ORDER BY B.Title ASC
        """
        return self.ExecuteQuery(Query)

    def GetBooksWithPagination(self, Limit: int = 50, Offset: int = 0) -> List[sqlite3.Row]:
        """
        Get books with pagination for web performance
        Essential for mobile and large libraries
        """
        Query = """
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        ORDER BY B.Title ASC
        LIMIT ? OFFSET ?
        """
        return self.ExecuteQuery(Query, (Limit, Offset))

    def GetBookById(self, BookId: int) -> Optional[sqlite3.Row]:
        """
        Get specific book by ID for detailed views
        """
        Query = """
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        WHERE B.Id = ?
        """
        Results = self.ExecuteQuery(Query, (BookId,))
        return Results[0] if Results else None

    def GetBookCount(self) -> int:
        """
        Get total number of books for pagination and statistics
        """
        Query = "SELECT COUNT(*) as BookCount FROM Books"
        Results = self.ExecuteQuery(Query)
        return Results[0]['BookCount'] if Results else 0

    # ==================== SEARCH FUNCTIONALITY ====================

    def SearchBooks(self, SearchQuery: str, Category: Optional[str] = None, 
                   Subject: Optional[str] = None, MinRating: int = 0,
                   Limit: int = 50, Offset: int = 0) -> List[sqlite3.Row]:
        """
        Google-type instant search with filters
        Maintains exact desktop search functionality
        """
        # Build base query with search
        WhereConditions = [
            "(B.Title LIKE ? OR B.Author LIKE ? OR C.Category LIKE ? OR S.Subject LIKE ?)"
        ]
        Parameters = [f"%{SearchQuery}%"] * 4
        
        # Add optional filters
        if Category:
            WhereConditions.append("C.Category = ?")
            Parameters.append(Category)
            
        if Subject:
            WhereConditions.append("S.Subject = ?")
            Parameters.append(Subject)
            
        # Combine conditions
        WhereClause = " AND ".join(WhereConditions)
        
        Query = f"""
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        WHERE {WhereClause}
        ORDER BY 
            CASE 
                WHEN B.Title LIKE ? THEN 1 
                WHEN B.Author LIKE ? THEN 2 
                ELSE 3 
            END,
            B.Title ASC
        LIMIT ? OFFSET ?
        """
        
        # Add parameters for ORDER BY and pagination
        SearchPattern = f"%{SearchQuery}%"
        Parameters.extend([SearchPattern, SearchPattern, Limit, Offset])
        
        return self.ExecuteQuery(Query, tuple(Parameters))

    def GetSearchResultCount(self, SearchQuery: str, Category: Optional[str] = None,
                           Subject: Optional[str] = None, MinRating: int = 0) -> int:
        """
        Get total count of search results for pagination
        """
        WhereConditions = [
            "(B.Title LIKE ? OR B.Author LIKE ? OR C.Category LIKE ? OR S.Subject LIKE ?)"
        ]
        Parameters = [f"%{SearchQuery}%"] * 4
        
        if Category:
            WhereConditions.append("C.Category = ?")
            Parameters.append(Category)
            
        if Subject:
            WhereConditions.append("S.Subject = ?")
            Parameters.append(Subject)
            
        WhereClause = " AND ".join(WhereConditions)
        Query = f"""SELECT COUNT(*) as ResultCount 
                   FROM Books B 
                   LEFT JOIN Categories C ON B.CategoryId = C.Id 
                   LEFT JOIN Subjects S ON B.SubjectId = S.Id 
                   WHERE {WhereClause}"""
        
        Results = self.ExecuteQuery(Query, tuple(Parameters))
        return Results[0]['ResultCount'] if Results else 0

    # ==================== FILTER FUNCTIONALITY ====================

    def GetBooksByFilters(self, Category: Optional[str] = None, Subject: Optional[str] = None,
                         MinRating: int = 0, Limit: int = 50, Offset: int = 0) -> List[sqlite3.Row]:
        """
        Filter books by category, subject, and/or rating
        Maintains exact desktop filter behavior
        """
        self.Logger.info(f"GetBooksByFilters called with Category='{Category}', Subject='{Subject}', MinRating={MinRating}")
        
        WhereConditions = []
        Parameters = []
        
        if Category:
            WhereConditions.append("C.Category = ?")
            Parameters.append(Category)
            self.Logger.info(f"Added category filter: C.Category = '{Category}'")
            
        if Subject:
            WhereConditions.append("S.Subject = ?")
            Parameters.append(Subject)
            self.Logger.info(f"Added subject filter: S.Subject = '{Subject}'")
            
        # Build query with proper JOIN types based on filters
        if Category and Subject:
            # Both filters - use INNER JOIN for both
            JoinClause = """
            INNER JOIN Categories C ON B.CategoryId = C.Id
            INNER JOIN Subjects S ON B.SubjectId = S.Id
            """
        elif Category:
            # Category filter only - use INNER JOIN for Categories
            JoinClause = """
            INNER JOIN Categories C ON B.CategoryId = C.Id
            LEFT JOIN Subjects S ON B.SubjectId = S.Id
            """
        elif Subject:
            # Subject filter only - use INNER JOIN for Subjects
            JoinClause = """
            LEFT JOIN Categories C ON B.CategoryId = C.Id
            INNER JOIN Subjects S ON B.SubjectId = S.Id
            """
        else:
            # No filters - use LEFT JOIN for both
            JoinClause = """
            LEFT JOIN Categories C ON B.CategoryId = C.Id
            LEFT JOIN Subjects S ON B.SubjectId = S.Id
            """
        
        if WhereConditions:
            WhereClause = "WHERE " + " AND ".join(WhereConditions)
        else:
            WhereClause = ""
        
        Query = f"""
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        {JoinClause}
        {WhereClause}
        ORDER BY B.Title ASC
        LIMIT ? OFFSET ?
        """
        
        Parameters.extend([Limit, Offset])
        
        self.Logger.info(f"Final query: {Query}")
        self.Logger.info(f"Query parameters: {tuple(Parameters)}")
        
        Results = self.ExecuteQuery(Query, tuple(Parameters))
        self.Logger.info(f"Query returned {len(Results)} results")
        
        return Results

    def GetFilteredBookCount(self, Category: Optional[str] = None, Subject: Optional[str] = None,
                           MinRating: int = 0) -> int:
        """
        Get count of filtered books for pagination
        """
        WhereConditions = []
        Parameters = []
        
        if Category:
            WhereConditions.append("C.Category = ?")
            Parameters.append(Category)
            
        if Subject:
            WhereConditions.append("S.Subject = ?")
            Parameters.append(Subject)
            
        # Build query with proper JOIN types based on filters
        if Category and Subject:
            # Both filters - use INNER JOIN for both
            JoinClause = """
            INNER JOIN Categories C ON B.CategoryId = C.Id
            INNER JOIN Subjects S ON B.SubjectId = S.Id
            """
        elif Category:
            # Category filter only - use INNER JOIN for Categories
            JoinClause = """
            INNER JOIN Categories C ON B.CategoryId = C.Id
            LEFT JOIN Subjects S ON B.SubjectId = S.Id
            """
        elif Subject:
            # Subject filter only - use INNER JOIN for Subjects
            JoinClause = """
            LEFT JOIN Categories C ON B.CategoryId = C.Id
            INNER JOIN Subjects S ON B.SubjectId = S.Id
            """
        else:
            # No filters - use LEFT JOIN for both
            JoinClause = """
            LEFT JOIN Categories C ON B.CategoryId = C.Id
            LEFT JOIN Subjects S ON B.SubjectId = S.Id
            """
        
        if WhereConditions:
            WhereClause = "WHERE " + " AND ".join(WhereConditions)
        else:
            WhereClause = ""
        
        Query = f"""SELECT COUNT(*) as FilteredCount 
                   FROM Books B
                   {JoinClause}
                   {WhereClause}"""
        
        Results = self.ExecuteQuery(Query, tuple(Parameters))
        return Results[0]['FilteredCount'] if Results else 0

    # ==================== CATEGORY AND SUBJECT METHODS ====================

    def GetCategories(self) -> List[sqlite3.Row]:
        """
        Get all unique categories for dropdown population
        """
        Query = """
        SELECT Category 
        FROM Categories 
        ORDER BY Category ASC
        """
        return self.ExecuteQuery(Query)

    def GetCategoriesWithCounts(self) -> List[sqlite3.Row]:
        """
        Get categories with book counts and subject counts for enhanced UI
        Format: CategoryName (#subjects/#books)
        """
        # Try the complex query first, fallback to simple if tables don't exist
        try:
            Query = """
            SELECT 
                C.Category,
                COUNT(DISTINCT B.Id) as BookCount,
                COUNT(DISTINCT S.Id) as SubjectCount
            FROM Categories C
            LEFT JOIN Books B ON C.Id = B.CategoryId
            LEFT JOIN Subjects S ON C.Id = S.CategoryId
            GROUP BY C.Category
            ORDER BY BookCount DESC, C.Category ASC
            """
            return self.ExecuteQuery(Query)
        except:
            # Fallback to simple query if complex schema doesn't exist
            Query = """
            SELECT 
                C.Category,
                COUNT(DISTINCT B.Id) as BookCount,
                0 as SubjectCount
            FROM Categories C
            LEFT JOIN Books B ON B.CategoryId = C.Id
            GROUP BY C.Category
            ORDER BY BookCount DESC, C.Category ASC
            """
            try:
                return self.ExecuteQuery(Query)
            except:
                # Ultimate fallback - get categories directly from Books table
                Query = """
                SELECT 
                    Category,
                    COUNT(*) as BookCount,
                    0 as SubjectCount
                FROM Books
                WHERE Category IS NOT NULL AND Category != ''
                GROUP BY Category
                ORDER BY BookCount DESC, Category ASC
                """
                return self.ExecuteQuery(Query)

    def GetSubjects(self) -> List[sqlite3.Row]:
        """
        Get all unique subjects for dropdown population
        """
        Query = """
        SELECT Subject 
        FROM Subjects 
        ORDER BY Subject ASC
        """
        return self.ExecuteQuery(Query)

    def GetSubjectsWithCounts(self) -> List[sqlite3.Row]:
        """
        Get subjects with book counts for enhanced UI
        """
        # Try the complex query first, fallback to simple if tables don't exist
        try:
            Query = """
            SELECT S.Subject, COUNT(B.Id) as BookCount
            FROM Subjects S
            JOIN Books B ON S.Id = B.SubjectId
            GROUP BY S.Subject 
            ORDER BY BookCount DESC, S.Subject ASC
            """
            return self.ExecuteQuery(Query)
        except:
            # Fallback - get subjects directly from Books table
            Query = """
            SELECT 
                Subject,
                COUNT(*) as BookCount
            FROM Books
            WHERE Subject IS NOT NULL AND Subject != ''
            GROUP BY Subject
            ORDER BY BookCount DESC, Subject ASC
            """
            return self.ExecuteQuery(Query)

    def GetSubjectsByCategory(self, Category: str) -> List[sqlite3.Row]:
        """
        Get subjects filtered by category for dependent dropdowns
        """
        self.Logger.info(f"GetSubjectsByCategory called with Category='{Category}'")
        
        # Try the complex query first, fallback to simple if tables don't exist
        try:
            Query = """
            SELECT S.Subject, C.Category, COUNT(B.Id) as BookCount
            FROM Subjects S
            JOIN Books B ON S.Id = B.SubjectId
            JOIN Categories C ON S.CategoryId = C.Id
            WHERE C.Category = ?
            GROUP BY S.Subject, C.Category
            ORDER BY S.Subject ASC
            """
            self.Logger.info(f"GetSubjectsByCategory query: {Query}")
            self.Logger.info(f"GetSubjectsByCategory parameters: {(Category,)}")
            Results = self.ExecuteQuery(Query, (Category,))
        except:
            # Fallback - get subjects directly from Books table filtered by category
            Query = """
            SELECT 
                Subject,
                Category,
                COUNT(*) as BookCount
            FROM Books
            WHERE Category = ? AND Subject IS NOT NULL AND Subject != ''
            GROUP BY Subject, Category
            ORDER BY Subject ASC
            """
            self.Logger.info(f"GetSubjectsByCategory fallback query: {Query}")
            Results = self.ExecuteQuery(Query, (Category,))
        
        self.Logger.info(f"GetSubjectsByCategory returned {len(Results)} results")
        
        return Results

    def GetAuthors(self) -> List[sqlite3.Row]:
        """
        Get all unique authors for enhanced search
        """
        Query = """
        SELECT DISTINCT Author, COUNT(*) as BookCount
        FROM Books 
        WHERE Author IS NOT NULL AND Author != ''
        GROUP BY Author 
        ORDER BY BookCount DESC, Author ASC
        """
        return self.ExecuteQuery(Query)

    # ==================== STATISTICS AND ANALYTICS ====================

    def GetLibraryStatistics(self) -> Dict[str, Any]:
        """
        Get comprehensive library statistics for dashboard
        Maintains exact desktop status bar information
        """
        Stats = {}
        
        try:
            # Basic counts
            BookCountQuery = "SELECT COUNT(*) as Total FROM Books"
            BookCountResult = self.ExecuteQuery(BookCountQuery)
            Stats['TotalBooks'] = BookCountResult[0]['Total'] if BookCountResult else 0
            
            # Category count
            CategoryCountQuery = "SELECT COUNT(*) as Total FROM Categories"
            CategoryCountResult = self.ExecuteQuery(CategoryCountQuery)
            Stats['TotalCategories'] = CategoryCountResult[0]['Total'] if CategoryCountResult else 0
            
            # Subject count
            SubjectCountQuery = "SELECT COUNT(*) as Total FROM Subjects"
            SubjectCountResult = self.ExecuteQuery(SubjectCountQuery)
            Stats['TotalSubjects'] = SubjectCountResult[0]['Total'] if SubjectCountResult else 0
            
            # Author count
            AuthorCountQuery = """
            SELECT COUNT(DISTINCT Author) as Total 
            FROM Books 
            WHERE Author IS NOT NULL AND Author != ''
            """
            AuthorCountResult = self.ExecuteQuery(AuthorCountQuery)
            Stats['TotalAuthors'] = AuthorCountResult[0]['Total'] if AuthorCountResult else 0
            
            # File size statistics
            FileSizeQuery = """
            SELECT 
                COALESCE(SUM(FileSize), 0) as TotalSize,
                COALESCE(AVG(FileSize), 0) as AverageSize
            FROM Books 
            WHERE FileSize IS NOT NULL AND FileSize > 0
            """
            FileSizeResult = self.ExecuteQuery(FileSizeQuery)
            if FileSizeResult:
                Stats['TotalFileSize'] = FileSizeResult[0]['TotalSize']
                Stats['AverageFileSize'] = FileSizeResult[0]['AverageSize']
            else:
                Stats['TotalFileSize'] = 0
                Stats['AverageFileSize'] = 0
            
            # Rating statistics (REMOVED as column does not exist)
            Stats['AverageRating'] = 0.0
            Stats['RatedBooks'] = 0
            
            # Page count statistics
            PageQuery = """
            SELECT 
                COALESCE(SUM(PageCount), 0) as TotalPages,
                COALESCE(AVG(PageCount), 0) as AveragePages
            FROM Books 
            WHERE PageCount IS NOT NULL AND PageCount > 0
            """
            PageResult = self.ExecuteQuery(PageQuery)
            if PageResult:
                Stats['TotalPages'] = PageResult[0]['TotalPages']
                Stats['AveragePages'] = round(PageResult[0]['AveragePages'], 1)
            else:
                Stats['TotalPages'] = 0
                Stats['AveragePages'] = 0
            
            self.Logger.debug(f"Retrieved library statistics: {Stats['TotalBooks']} books")
            return Stats
            
        except Exception as Error:
            self.Logger.error(f"Error getting library statistics: {Error}")
            return {
                'TotalBooks': 0,
                'TotalCategories': 0,
                'TotalSubjects': 0,
                'TotalAuthors': 0,
                'TotalFileSize': 0,
                'AverageFileSize': 0,
                'AverageRating': 0.0,
                'RatedBooks': 0,
                'TotalPages': 0,
                'AveragePages': 0
            }

    def GetRecentBooks(self, Limit: int = 10) -> List[sqlite3.Row]:
        """
        Get recently added books for mobile quick access
        """
        Query = """
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, B.CreatedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        WHERE B.CreatedDate IS NOT NULL
        ORDER BY B.CreatedDate DESC
        LIMIT ?
        """
        return self.ExecuteQuery(Query, (Limit,))

    def GetTopRatedBooks(self, Limit: int = 10) -> List[sqlite3.Row]:
        """
        Get highest rated books for featured sections
        """
        Query = """
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject
        FROM Books B 
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        ORDER BY B.Title ASC
        LIMIT ?
        """
        return self.ExecuteQuery(Query, (Limit,))

    # ==================== UTILITY METHODS ====================

    def ValidateDatabase(self) -> Dict[str, Any]:
        """
        Validate database structure and integrity
        Returns status information for health checks
        """
        ValidationResults = {
            'is_valid': False,
            'tables_exist': False,
            'indexes_exist': False,
            'data_integrity': False,
            'errors': []
        }
        
        try:
            # Check if main tables exist
            TableQuery = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('Books', 'Categories', 'Subjects')
            """
            TableResults = self.ExecuteQuery(TableQuery)
            ValidationResults['tables_exist'] = len(TableResults) >= 1  # At least Books table
            
            # Check if indexes exist
            IndexQuery = """
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'IX_%'
            """
            IndexResults = self.ExecuteQuery(IndexQuery)
            ValidationResults['indexes_exist'] = len(IndexResults) > 0
            
            # Basic data integrity check
            IntegrityQuery = "PRAGMA integrity_check"
            IntegrityResults = self.ExecuteQuery(IntegrityQuery)
            ValidationResults['data_integrity'] = (
                IntegrityResults and 
                IntegrityResults[0][0] == 'ok'
            )
            
            # Overall validation
            ValidationResults['is_valid'] = (
                ValidationResults['tables_exist'] and
                ValidationResults['data_integrity']
            )
            
        except Exception as Error:
            ValidationResults['errors'].append(str(Error))
            self.Logger.error(f"Database validation error: {Error}")
        
        return ValidationResults

    def OptimizeDatabase(self) -> bool:
        """
        Optimize database for better web performance
        Runs ANALYZE and VACUUM commands
        """
        try:
            # Update statistics for query optimizer
            self.Connection.execute("ANALYZE")
            
            # Compact database (careful with large databases)
            self.Connection.execute("VACUUM")
            
            self.Logger.info("Database optimization completed")
            return True
            
        except Exception as Error:
            self.Logger.error(f"Database optimization failed: {Error}")
            return False

    def GetDatabaseInfo(self) -> Dict[str, Any]:
        """
        Get database metadata for debugging and monitoring
        """
        Info = {}
        
        try:
            # Database file info
            if os.path.exists(self.DatabasePath):
                FileStats = os.stat(self.DatabasePath)
                Info['file_size'] = FileStats.st_size
                Info['last_modified'] = datetime.fromtimestamp(FileStats.st_mtime).isoformat()
            
            # SQLite version
            VersionQuery = "SELECT sqlite_version() as Version"
            VersionResult = self.ExecuteQuery(VersionQuery)
            Info['sqlite_version'] = VersionResult[0]['Version'] if VersionResult else 'Unknown'
            
            # Page info
            PageInfoQuery = "PRAGMA page_count"
            PageInfoResult = self.ExecuteQuery(PageInfoQuery)
            Info['page_count'] = PageInfoResult[0][0] if PageInfoResult else 0
            
            # Schema version
            SchemaQuery = "PRAGMA schema_version"
            SchemaResult = self.ExecuteQuery(SchemaQuery)
            Info['schema_version'] = SchemaResult[0][0] if SchemaResult else 0
            
        except Exception as Error:
            self.Logger.error(f"Error getting database info: {Error}")
            Info['error'] = str(Error)
        
        return Info

    def GetBookThumbnail(self, BookId: int) -> Optional[bytes]:
        """
        Retrieve thumbnail image data for a specific book
        
        Args:
            BookId: ID of the book to get thumbnail for
            
        Returns:
            bytes: Thumbnail image data or None if not found
        """
        try:
            Query = """
            SELECT ThumbnailImage 
            FROM Books 
            WHERE Id = ?
            """
            
            Result = self.ExecuteQuery(Query, (BookId,))
            
            if Result and Result[0]['ThumbnailImage']:
                return Result[0]['ThumbnailImage']
            else:
                return None
                
        except Exception as Error:
            self.Logger.error(f"Error getting thumbnail for book {BookId}: {Error}")
            return None

    def HasThumbnail(self, BookId: int) -> bool:
        """
        Check if a book has a thumbnail image
        
        Args:
            BookId: ID of the book to check
            
        Returns:
            bool: True if book has thumbnail, False otherwise
        """
        try:
            Query = """
            SELECT ThumbnailImage IS NOT NULL and LENGTH(ThumbnailImage) > 0 as HasThumb
            FROM Books 
            WHERE Id = ?
            """
            
            Result = self.ExecuteQuery(Query, (BookId,))
            
            if Result:
                return bool(Result[0]['HasThumb'])
            else:
                return False
                
        except Exception as Error:
            self.Logger.error(f"Error checking thumbnail for book {BookId}: {Error}")
            return False
    
    def GetBookPDF(self, BookId: int) -> Optional[bytes]:
        """
        Retrieve PDF data for a specific book from database
        
        Args:
            BookId: ID of the book to get PDF for
            
        Returns:
            bytes: PDF data or None if not found
        """
        try:
            # First, check if PDFData column exists
            ColumnsQuery = "PRAGMA table_info(Books)"
            Columns = self.ExecuteQuery(ColumnsQuery, ())
            ColumnNames = [col['name'] for col in Columns]
            
            if 'PDFData' not in ColumnNames:
                self.Logger.info(f"PDFData column not found in Books table")
                return None
            
            Query = """
            SELECT PDFData 
            FROM Books 
            WHERE Id = ?
            """
            
            Result = self.ExecuteQuery(Query, (BookId,))
            
            if Result and Result[0]['PDFData']:
                return Result[0]['PDFData']
            else:
                return None
                
        except Exception as Error:
            self.Logger.error(f"Error getting PDF for book {BookId}: {Error}")
            return None
    
    def HasPDF(self, BookId: int) -> bool:
        """
        Check if a book has PDF data
        
        Args:
            BookId: ID of the book to check
            
        Returns:
            bool: True if book has PDF, False otherwise
        """
        try:
            # First, check if PDFData column exists
            ColumnsQuery = "PRAGMA table_info(Books)"
            Columns = self.ExecuteQuery(ColumnsQuery, ())
            ColumnNames = [col['name'] for col in Columns]
            
            if 'PDFData' not in ColumnNames:
                return False
            
            Query = """
            SELECT PDFData IS NOT NULL and LENGTH(PDFData) > 0 as HasPDF
            FROM Books 
            WHERE Id = ?
            """
            
            Result = self.ExecuteQuery(Query, (BookId,))
            
            if Result:
                return bool(Result[0]['HasPDF'])
            else:
                return False
                
        except Exception as Error:
            self.Logger.error(f"Error checking PDF for book {BookId}: {Error}")
            return False

    # ==================== USER AUTHENTICATION METHODS ====================

    def InitializeUserTables(self) -> bool:
        """
        Create user authentication tables if they don't exist
        BowersWorld.com user registration and subscription management
        """
        try:
            if not self.Connection:
                self.Connect()
            
            # Users table for BowersWorld.com registration
            UsersTableQuery = """
            CREATE TABLE IF NOT EXISTS Users (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Email TEXT UNIQUE NOT NULL,
                Username TEXT UNIQUE,
                PasswordHash TEXT NOT NULL,
                SubscriptionTier TEXT DEFAULT 'free' CHECK(SubscriptionTier IN ('free', 'scholar', 'researcher', 'institution')),
                IsActive BOOLEAN DEFAULT TRUE,
                EmailVerified BOOLEAN DEFAULT FALSE,
                EmailVerificationToken TEXT,
                PasswordResetToken TEXT,
                PasswordResetExpires DATETIME,
                LastLoginDate DATETIME,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                ProfileData TEXT,
                LoginAttempts INTEGER DEFAULT 0,
                AccountLockedUntil DATETIME
            )
            """
            
            # User sessions for secure authentication
            SessionsTableQuery = """
            CREATE TABLE IF NOT EXISTS UserSessions (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                UserId INTEGER NOT NULL,
                SessionToken TEXT UNIQUE NOT NULL,
                RefreshToken TEXT UNIQUE,
                ExpiresAt DATETIME NOT NULL,
                RefreshExpiresAt DATETIME,
                IpAddress TEXT,
                UserAgent TEXT,
                IsActive BOOLEAN DEFAULT TRUE,
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                LastAccessAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
            """
            
            # Subscription history for BowersWorld.com billing
            SubscriptionsTableQuery = """
            CREATE TABLE IF NOT EXISTS UserSubscriptions (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                UserId INTEGER NOT NULL,
                SubscriptionTier TEXT NOT NULL,
                StartDate DATETIME NOT NULL,
                EndDate DATETIME,
                IsActive BOOLEAN DEFAULT TRUE,
                PaymentMethod TEXT,
                TransactionId TEXT,
                Amount DECIMAL(10,2),
                Currency TEXT DEFAULT 'USD',
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
            """
            
            # User activity tracking for analytics
            UserActivityTableQuery = """
            CREATE TABLE IF NOT EXISTS UserActivity (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                UserId INTEGER,
                ActivityType TEXT NOT NULL,
                ActivityData TEXT,
                IpAddress TEXT,
                UserAgent TEXT,
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(UserId) REFERENCES Users(Id) ON DELETE SET NULL
            )
            """
            
            # Execute table creation queries
            self.Connection.execute(UsersTableQuery)
            self.Connection.execute(SessionsTableQuery)
            self.Connection.execute(SubscriptionsTableQuery)
            self.Connection.execute(UserActivityTableQuery)
            
            # Create indexes for performance
            IndexQueries = [
                "CREATE INDEX IF NOT EXISTS IX_Users_Email ON Users(Email)",
                "CREATE INDEX IF NOT EXISTS IX_Users_Username ON Users(Username)",
                "CREATE INDEX IF NOT EXISTS IX_Users_SubscriptionTier ON Users(SubscriptionTier)",
                "CREATE INDEX IF NOT EXISTS IX_UserSessions_Token ON UserSessions(SessionToken)",
                "CREATE INDEX IF NOT EXISTS IX_UserSessions_UserId ON UserSessions(UserId)",
                "CREATE INDEX IF NOT EXISTS IX_UserSessions_ExpiresAt ON UserSessions(ExpiresAt)",
                "CREATE INDEX IF NOT EXISTS IX_UserSubscriptions_UserId ON UserSubscriptions(UserId)",
                "CREATE INDEX IF NOT EXISTS IX_UserActivity_UserId ON UserActivity(UserId)",
                "CREATE INDEX IF NOT EXISTS IX_UserActivity_Type ON UserActivity(ActivityType)"
            ]
            
            for IndexQuery in IndexQueries:
                self.Connection.execute(IndexQuery)
            
            self.Connection.commit()
            self.Logger.info("✅ BowersWorld.com user authentication tables initialized")
            return True
            
        except Exception as Error:
            self.Logger.error(f"Failed to initialize user tables: {Error}")
            return False

    def CreateUser(self, Email: str, Password: str, Username: Optional[str] = None, 
                  SubscriptionTier: str = 'free') -> Optional[Dict[str, Any]]:
        """
        Create new user account for BowersWorld.com registration
        
        Args:
            Email: User's email address (required)
            Password: Plain text password (will be hashed)
            Username: Optional username (defaults to email prefix)
            SubscriptionTier: User's subscription level
            
        Returns:
            Dict with user info or None if creation failed
        """
        try:
            # Generate username from email if not provided
            if not Username:
                Username = Email.split('@')[0]
            
            # Hash password securely
            PasswordHash = self.PwdContext.hash(Password)
            
            # Generate email verification token
            EmailVerificationToken = secrets.token_urlsafe(32)
            
            Query = """
            INSERT INTO Users (Email, Username, PasswordHash, SubscriptionTier, 
                             EmailVerificationToken, CreatedDate, ModifiedDate)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            self.Connection.execute(Query, (Email, Username, PasswordHash, 
                                          SubscriptionTier, EmailVerificationToken))
            self.Connection.commit()
            
            # Get the created user
            NewUser = self.GetUserByEmail(Email)
            if NewUser:
                self.LogUserActivity(NewUser['Id'], 'user_registered', {'email': Email})
                self.Logger.info(f"✅ New user registered: {Email} ({SubscriptionTier})")
                return NewUser
            
            return None
            
        except sqlite3.IntegrityError as Error:
            if "UNIQUE constraint failed: Users.Email" in str(Error):
                self.Logger.warning(f"Registration failed - email already exists: {Email}")
                return {'error': 'email_exists'}
            elif "UNIQUE constraint failed: Users.Username" in str(Error):
                self.Logger.warning(f"Registration failed - username already exists: {Username}")
                return {'error': 'username_exists'}
            else:
                self.Logger.error(f"User creation integrity error: {Error}")
                return {'error': 'integrity_error'}
        except Exception as Error:
            self.Logger.error(f"User creation failed: {Error}")
            return None

    def AuthenticateUser(self, Email: str, Password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user login for BowersWorld.com
        
        Args:
            Email: User's email address
            Password: Plain text password
            
        Returns:
            Dict with user info or None if authentication failed
        """
        try:
            User = self.GetUserByEmail(Email)
            if not User:
                self.Logger.warning(f"Login attempt with unknown email: {Email}")
                return None
            
            # Check if account is locked
            if User['AccountLockedUntil'] and datetime.fromisoformat(User['AccountLockedUntil']) > datetime.now():
                self.Logger.warning(f"Login attempt on locked account: {Email}")
                return {'error': 'account_locked'}
            
            # Verify password
            if self.PwdContext.verify(Password, User['PasswordHash']):
                # Reset login attempts on successful login
                self.ResetLoginAttempts(User['Id'])
                
                # Update last login date
                UpdateQuery = "UPDATE Users SET LastLoginDate = CURRENT_TIMESTAMP WHERE Id = ?"
                self.Connection.execute(UpdateQuery, (User['Id'],))
                self.Connection.commit()
                
                self.LogUserActivity(User['Id'], 'user_login', {'email': Email})
                self.Logger.info(f"✅ User authenticated: {Email}")
                return User
            else:
                # Increment login attempts
                self.IncrementLoginAttempts(User['Id'])
                self.Logger.warning(f"Failed login attempt: {Email}")
                return None
                
        except Exception as Error:
            self.Logger.error(f"Authentication error: {Error}")
            return None

    def GetUserByEmail(self, Email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email address
        """
        Query = "SELECT * FROM Users WHERE Email = ? AND IsActive = TRUE"
        Results = self.ExecuteQuery(Query, (Email,))
        return dict(Results[0]) if Results else None

    def GetUserById(self, UserId: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID
        """
        Query = "SELECT * FROM Users WHERE Id = ? AND IsActive = TRUE"
        Results = self.ExecuteQuery(Query, (UserId,))
        return dict(Results[0]) if Results else None

    def CreateUserSession(self, UserId: int, IpAddress: Optional[str] = None, 
                         UserAgent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create authenticated session for user
        
        Args:
            UserId: User's database ID
            IpAddress: Client IP address
            UserAgent: Client user agent string
            
        Returns:
            Dict with session tokens or None if creation failed
        """
        try:
            # Generate secure tokens
            SessionToken = secrets.token_urlsafe(32)
            RefreshToken = secrets.token_urlsafe(32)
            
            # Set expiration times from configuration
            ExpiresAt = datetime.now() + AuthConfig.SESSION_EXPIRY
            RefreshExpiresAt = datetime.now() + AuthConfig.REFRESH_TOKEN_EXPIRY
            
            Query = """
            INSERT INTO UserSessions (UserId, SessionToken, RefreshToken, ExpiresAt, 
                                    RefreshExpiresAt, IpAddress, UserAgent, CreatedAt, LastAccessAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            self.Connection.execute(Query, (UserId, SessionToken, RefreshToken, 
                                          ExpiresAt.isoformat(), RefreshExpiresAt.isoformat(),
                                          IpAddress, UserAgent))
            self.Connection.commit()
            
            self.Logger.info(f"✅ Session created for user ID: {UserId}")
            
            return {
                'session_token': SessionToken,
                'refresh_token': RefreshToken,
                'expires_at': ExpiresAt.isoformat(),
                'refresh_expires_at': RefreshExpiresAt.isoformat()
            }
            
        except Exception as Error:
            self.Logger.error(f"Session creation failed: {Error}")
            return None

    def ValidateSession(self, SessionToken: str) -> Optional[Dict[str, Any]]:
        """
        Validate user session token
        
        Args:
            SessionToken: Session token to validate
            
        Returns:
            Dict with user info or None if session invalid
        """
        try:
            Query = """
            SELECT s.*, u.Email, u.Username, u.SubscriptionTier
            FROM UserSessions s
            JOIN Users u ON s.UserId = u.Id
            WHERE s.SessionToken = ? AND s.IsActive = TRUE 
                  AND s.ExpiresAt > CURRENT_TIMESTAMP
            """
            
            Results = self.ExecuteQuery(Query, (SessionToken,))
            if Results:
                # Update last access time
                UpdateQuery = "UPDATE UserSessions SET LastAccessAt = CURRENT_TIMESTAMP WHERE SessionToken = ?"
                self.Connection.execute(UpdateQuery, (SessionToken,))
                self.Connection.commit()
                
                return dict(Results[0])
            
            return None
            
        except Exception as Error:
            self.Logger.error(f"Session validation error: {Error}")
            return None

    def LogoutUser(self, SessionToken: str) -> bool:
        """
        Logout user by deactivating session
        """
        try:
            Query = "UPDATE UserSessions SET IsActive = FALSE WHERE SessionToken = ?"
            self.Connection.execute(Query, (SessionToken,))
            self.Connection.commit()
            
            self.Logger.info(f"✅ User logged out: {SessionToken[:8]}...")
            return True
            
        except Exception as Error:
            self.Logger.error(f"Logout error: {Error}")
            return False

    def CleanupExpiredSessions(self) -> int:
        """
        Remove expired sessions from database
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            Query = "DELETE FROM UserSessions WHERE ExpiresAt < CURRENT_TIMESTAMP OR IsActive = FALSE"
            Cursor = self.Connection.execute(Query)
            self.Connection.commit()
            
            CleanedCount = Cursor.rowcount
            self.Logger.info(f"✅ Cleaned up {CleanedCount} expired sessions")
            return CleanedCount
            
        except Exception as Error:
            self.Logger.error(f"Session cleanup error: {Error}")
            return 0

    def IncrementLoginAttempts(self, UserId: int) -> None:
        """
        Increment failed login attempts and lock account if necessary
        """
        try:
            # Get current attempt count
            Query = "SELECT LoginAttempts FROM Users WHERE Id = ?"
            Result = self.ExecuteQuery(Query, (UserId,))
            
            if Result:
                CurrentAttempts = Result[0]['LoginAttempts'] + 1
                
                # Lock account after configured failed attempts
                if CurrentAttempts >= AuthConfig.MAX_LOGIN_ATTEMPTS:
                    LockUntil = datetime.now() + AuthConfig.LOCKOUT_DURATION
                    UpdateQuery = """
                    UPDATE Users 
                    SET LoginAttempts = ?, AccountLockedUntil = ?
                    WHERE Id = ?
                    """
                    self.Connection.execute(UpdateQuery, (CurrentAttempts, LockUntil.isoformat(), UserId))
                    self.Logger.warning(f"Account locked due to failed login attempts: User ID {UserId}")
                else:
                    UpdateQuery = "UPDATE Users SET LoginAttempts = ? WHERE Id = ?"
                    self.Connection.execute(UpdateQuery, (CurrentAttempts, UserId))
                
                self.Connection.commit()
                
        except Exception as Error:
            self.Logger.error(f"Error incrementing login attempts: {Error}")

    def ResetLoginAttempts(self, UserId: int) -> None:
        """
        Reset failed login attempts and unlock account
        """
        try:
            Query = "UPDATE Users SET LoginAttempts = 0, AccountLockedUntil = NULL WHERE Id = ?"
            self.Connection.execute(Query, (UserId,))
            self.Connection.commit()
            
        except Exception as Error:
            self.Logger.error(f"Error resetting login attempts: {Error}")

    def LogUserActivity(self, UserId: Optional[int], ActivityType: str, 
                       ActivityData: Optional[Dict[str, Any]] = None,
                       IpAddress: Optional[str] = None, UserAgent: Optional[str] = None) -> None:
        """
        Log user activity for analytics and security
        """
        try:
            ActivityDataJson = json.dumps(ActivityData) if ActivityData else None
            
            Query = """
            INSERT INTO UserActivity (UserId, ActivityType, ActivityData, IpAddress, UserAgent)
            VALUES (?, ?, ?, ?, ?)
            """
            
            self.Connection.execute(Query, (UserId, ActivityType, ActivityDataJson, IpAddress, UserAgent))
            self.Connection.commit()
            
        except Exception as Error:
            self.Logger.error(f"Error logging user activity: {Error}")

    def GetUserStatistics(self) -> Dict[str, Any]:
        """
        Get BowersWorld.com user registration and subscription statistics
        """
        try:
            Stats = {}
            
            # Total users
            TotalUsersQuery = "SELECT COUNT(*) as Total FROM Users WHERE IsActive = TRUE"
            Result = self.ExecuteQuery(TotalUsersQuery)
            Stats['TotalUsers'] = Result[0]['Total'] if Result else 0
            
            # Users by subscription tier
            TierQuery = """
            SELECT SubscriptionTier, COUNT(*) as Count
            FROM Users 
            WHERE IsActive = TRUE
            GROUP BY SubscriptionTier
            """
            TierResults = self.ExecuteQuery(TierQuery)
            Stats['UsersByTier'] = {row['SubscriptionTier']: row['Count'] for row in TierResults}
            
            # New users today
            TodayQuery = """
            SELECT COUNT(*) as Today
            FROM Users 
            WHERE DATE(CreatedDate) = DATE('now') AND IsActive = TRUE
            """
            TodayResult = self.ExecuteQuery(TodayQuery)
            Stats['NewUsersToday'] = TodayResult[0]['Today'] if TodayResult else 0
            
            # Active sessions
            SessionQuery = """
            SELECT COUNT(*) as Active
            FROM UserSessions 
            WHERE IsActive = TRUE AND ExpiresAt > CURRENT_TIMESTAMP
            """
            SessionResult = self.ExecuteQuery(SessionQuery)
            Stats['ActiveSessions'] = SessionResult[0]['Active'] if SessionResult else 0
            
            return Stats
            
        except Exception as Error:
            self.Logger.error(f"Error getting user statistics: {Error}")
            return {
                'TotalUsers': 0,
                'UsersByTier': {},
                'NewUsersToday': 0,
                'ActiveSessions': 0
            }

    def __enter__(self):
        """Context manager entry"""
        self.Connect()
        return self

    def __exit__(self, ExceptionType, ExceptionValue, Traceback):
        """Context manager exit"""
        self.Disconnect()

    def __del__(self):
        """Destructor to ensure connection cleanup"""
        if hasattr(self, 'Connection') and self.Connection:
            try:
                self.Connection.close()
            except:
                pass  # Ignore errors during cleanup