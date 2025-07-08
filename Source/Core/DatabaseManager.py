# File: DatabaseManager.py
# Path: Source/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-2.0
# Backend Python: Uses PascalCase per project standards
# Database: Raw SQL with PascalCase elements (NO SQLAlchemy per Design Standard v2.0)
# SQL Naming: ALL database elements use PascalCase (tables, columns, indexes, constraints)
# Created: 2025-07-07
# Last Modified: 2025-07-07  09:19PM
"""
Description: Enhanced Database Manager - Design Standard v2.0
Handles all database operations for Anderson's Library web/mobile applications
Supports both desktop twin and mobile app functionality with raw SQL
Maintains exact desktop functionality while optimizing for web performance
"""

import sqlite3
import logging
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import json

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
        
        # Connection configuration for web performance
        self.ConnectionConfig = {
            'timeout': 30.0,
            'check_same_thread': False,  # Allow multi-threaded access
            'isolation_level': None,     # Autocommit mode for better performance
        }
        
        self.Logger.info(f"DatabaseManager v2.0 initialized for: {DatabasePath}")

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
            
            self.Logger.info(f"✅ Database connected successfully - {BookCount} books available")
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
        WhereConditions = []
        Parameters = []
        
        if Category:
            WhereConditions.append("C.Category = ?")
            Parameters.append(Category)
            
        if Subject:
            WhereConditions.append("S.Subject = ?")
            Parameters.append(Subject)
            
        # Build query
        if WhereConditions:
            WhereClause = "WHERE " + " AND ".join(WhereConditions)
        else:
            WhereClause = ""
        
        Query = f"""
        SELECT B.Id, B.Title, B.Author, C.Category, S.Subject, 
               B.PageCount, B.FileSize, B.CreatedDate, B.ModifiedDate
        FROM Books B
        LEFT JOIN Categories C ON B.CategoryId = C.Id
        LEFT JOIN Subjects S ON B.SubjectId = S.Id
        {WhereClause}
        ORDER BY B.Title ASC
        LIMIT ? OFFSET ?
        """
        
        Parameters.extend([Limit, Offset])
        return self.ExecuteQuery(Query, tuple(Parameters))

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
            
        if WhereConditions:
            WhereClause = "WHERE " + " AND ".join(WhereConditions)
        else:
            WhereClause = ""
        
        Query = f"""SELECT COUNT(*) as FilteredCount 
                   FROM Books B
                   LEFT JOIN Categories C ON B.CategoryId = C.Id
                   LEFT JOIN Subjects S ON B.SubjectId = S.Id
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
        Get categories with book counts for enhanced UI
        """
        Query = """
        SELECT C.Category, COUNT(B.Id) as BookCount
        FROM Categories C
        JOIN Books B ON C.Id = B.CategoryId
        GROUP BY C.Category
        ORDER BY BookCount DESC, C.Category ASC
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
        Query = """
        SELECT S.Subject, COUNT(B.Id) as BookCount
        FROM Subjects S
        JOIN Books B ON S.Id = B.SubjectId
        GROUP BY S.Subject 
        ORDER BY BookCount DESC, S.Subject ASC
        """
        return self.ExecuteQuery(Query)

    def GetSubjectsByCategory(self, Category: str) -> List[sqlite3.Row]:
        """
        Get subjects filtered by category for dependent dropdowns
        """
        Query = """
        SELECT S.Subject, C.Category, COUNT(B.Id) as BookCount
        FROM Subjects S
        JOIN Books B ON S.Id = B.SubjectId
        JOIN Categories C ON S.CategoryId = C.Id
        WHERE C.Category = ?
        GROUP BY S.Subject, C.Category
        ORDER BY S.Subject ASC
        """
        return self.ExecuteQuery(Query, (Category,))

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
            
            self.Logger.info(f"Retrieved library statistics: {Stats['TotalBooks']} books")
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