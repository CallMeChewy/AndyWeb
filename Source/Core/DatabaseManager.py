# File: DatabaseManager.py
# Path: Source/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-1.9
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:52PM
"""
Description: Database manager for AndyWeb - handles SQLite operations for book library
Provides connection management, query execution, and data access for web application.
Designed for eventual MySQL migration without SQLAlchemy dependency.

FIXED: Updated for web database schema compatibility
- Removed references to non-existent LastOpened column
- Uses ModifiedDate for activity tracking instead
- Maintains all original functionality with web-compatible queries
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

class DatabaseManager:
    """Manages database connections and operations for AndyWeb library system."""
    
    def __init__(self, DatabasePath: str = "Data/Databases/MyLibraryWeb.db"):
        """Initialize database manager with connection path."""
        self.DatabasePath = Path(DatabasePath)
        self.Connection = None
        self.Logger = logging.getLogger(__name__)
        
        # Ensure database exists
        if not self.DatabasePath.exists():
            raise FileNotFoundError(f"Database not found: {self.DatabasePath}")
            
    def Connect(self) -> bool:
        """Establish database connection with proper settings."""
        try:
            self.Connection = sqlite3.connect(
                self.DatabasePath,
                check_same_thread=False,  # Allow use across threads
                timeout=30.0
            )
            
            # Configure for better performance and JSON support
            self.Connection.row_factory = sqlite3.Row  # Dict-like access
            self.Connection.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
            self.Connection.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            
            self.Logger.info(f"Connected to database: {self.DatabasePath}")
            return True
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Database connection failed: {Error}")
            return False
            
    def Disconnect(self) -> None:
        """Close database connection safely."""
        if self.Connection:
            try:
                self.Connection.close()
                self.Connection = None
                self.Logger.info("Database connection closed")
            except sqlite3.Error as Error:
                self.Logger.error(f"Error closing database: {Error}")
                
    def ExecuteQuery(self, Query: str, Parameters: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dictionaries."""
        if not self.Connection:
            self.Connect()
            
        try:
            Cursor = self.Connection.cursor()
            Cursor.execute(Query, Parameters)
            
            # Convert Row objects to dictionaries
            Results = []
            for Row in Cursor.fetchall():
                Results.append(dict(Row))
                
            self.Logger.debug(f"Query executed: {Query[:100]}... ({len(Results)} rows)")
            return Results
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Query execution failed: {Error} | Query: {Query}")
            return []
            
    def ExecuteUpdate(self, Query: str, Parameters: Tuple = ()) -> bool:
        """Execute INSERT/UPDATE/DELETE and return success status."""
        if not self.Connection:
            self.Connect()
            
        try:
            Cursor = self.Connection.cursor()
            Cursor.execute(Query, Parameters)
            self.Connection.commit()
            
            RowsAffected = Cursor.rowcount
            self.Logger.debug(f"Update executed: {RowsAffected} rows affected")
            return True
            
        except sqlite3.Error as Error:
            self.Logger.error(f"Update execution failed: {Error} | Query: {Query}")
            self.Connection.rollback()
            return False
            
    def GetBooks(self, Limit: int = 50, Offset: int = 0, 
                SearchTerm: str = "", CategoryId: Optional[int] = None,
                SubjectId: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get books with optional filtering and pagination."""
        
        Query = """
            SELECT b.Id, b.Title, b.Author, b.ThumbnailImage,
                   b.FileSize, b.PageCount, b.ISBN, b.CreatedDate, b.ModifiedDate,
                   c.Category, s.Subject
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE 1=1
        """
        
        Parameters = []
        
        # Add search filter
        if SearchTerm:
            Query += " AND (b.Title LIKE ? OR b.Author LIKE ? OR c.Category LIKE ? OR s.Subject LIKE ?)"
            SearchPattern = f"%{SearchTerm}%"
            Parameters.extend([SearchPattern, SearchPattern, SearchPattern, SearchPattern])
            
        # Add category filter
        if CategoryId:
            Query += " AND b.CategoryId = ?"
            Parameters.append(CategoryId)
            
        # Add subject filter
        if SubjectId:
            Query += " AND b.SubjectId = ?"
            Parameters.append(SubjectId)
            
        # Add ordering and pagination
        Query += " ORDER BY b.Title LIMIT ? OFFSET ?"
        Parameters.extend([Limit, Offset])
        
        return self.ExecuteQuery(Query, tuple(Parameters))
        
    def GetBookById(self, BookId: int) -> Optional[Dict[str, Any]]:
        """Get single book by ID with full details."""
        Query = """
            SELECT b.*, c.Category, s.Subject
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE b.Id = ?
        """
        
        Results = self.ExecuteQuery(Query, (BookId,))
        return Results[0] if Results else None
        
    def GetCategories(self) -> List[Dict[str, Any]]:
        """Get all categories for filtering."""
        Query = """
            SELECT c.Id, c.Category, COUNT(b.Id) as BookCount
            FROM Categories c
            LEFT JOIN Books b ON c.Id = b.CategoryId
            GROUP BY c.Id, c.Category
            ORDER BY c.Category
        """
        return self.ExecuteQuery(Query)
        
    def GetSubjects(self, CategoryId: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get subjects, optionally filtered by category."""
        Query = """
            SELECT s.Id, s.Subject, s.CategoryId, COUNT(b.Id) as BookCount
            FROM Subjects s
            LEFT JOIN Books b ON s.Id = b.SubjectId
        """
        
        Parameters = []
        if CategoryId:
            Query += " WHERE s.CategoryId = ?"
            Parameters.append(CategoryId)
            
        Query += " GROUP BY s.Id, s.Subject, s.CategoryId ORDER BY s.Subject"
        
        return self.ExecuteQuery(Query, tuple(Parameters))
        
    def GetDatabaseStats(self) -> Dict[str, Any]:
        """Get database statistics for dashboard."""
        Stats = {}
        
        # Count books
        BookCount = self.ExecuteQuery("SELECT COUNT(*) as Count FROM Books")
        Stats['TotalBooks'] = BookCount[0]['Count'] if BookCount else 0
        
        # Count categories
        CategoryCount = self.ExecuteQuery("SELECT COUNT(*) as Count FROM Categories")
        Stats['TotalCategories'] = CategoryCount[0]['Count'] if CategoryCount else 0
        
        # Count subjects
        SubjectCount = self.ExecuteQuery("SELECT COUNT(*) as Count FROM Subjects")
        Stats['TotalSubjects'] = SubjectCount[0]['Count'] if SubjectCount else 0
        
        # Recent activity (FIXED: Using ModifiedDate instead of non-existent LastOpened)
        RecentBooks = self.ExecuteQuery("""
            SELECT Title, ModifiedDate as LastActivity
            FROM Books 
            WHERE ModifiedDate IS NOT NULL 
            ORDER BY ModifiedDate DESC 
            LIMIT 5
        """)
        Stats['RecentBooks'] = RecentBooks
        
        return Stats
        
    def UpdateBookLastOpened(self, BookId: int) -> bool:
        """
        Update book activity timestamp (web version compatibility).
        
        Note: Web database schema doesn't have LastOpened column,
        so we update ModifiedDate to track book access activity.
        """
        from datetime import datetime
        
        Query = "UPDATE Books SET ModifiedDate = ? WHERE Id = ?"
        CurrentTime = datetime.now().isoformat()
        
        return self.ExecuteUpdate(Query, (CurrentTime, BookId))
        
    def GetBooksByAuthor(self, Author: str) -> List[Dict[str, Any]]:
        """Get all books by a specific author."""
        Query = """
            SELECT b.Id, b.Title, b.Author, b.ThumbnailImage,
                   c.Category, s.Subject, b.CreatedDate
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE b.Author LIKE ?
            ORDER BY b.Title
        """
        
        AuthorPattern = f"%{Author}%"
        return self.ExecuteQuery(Query, (AuthorPattern,))
        
    def GetBooksByCategory(self, CategoryId: int) -> List[Dict[str, Any]]:
        """Get all books in a specific category."""
        Query = """
            SELECT b.Id, b.Title, b.Author, b.ThumbnailImage,
                   c.Category, s.Subject, b.CreatedDate
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE b.CategoryId = ?
            ORDER BY b.Title
        """
        
        return self.ExecuteQuery(Query, (CategoryId,))
        
    def SearchBooks(self, SearchTerm: str, Limit: int = 50) -> List[Dict[str, Any]]:
        """
        Full-text search across books with relevance scoring.
        Searches Title, Author, Category, and Subject fields.
        """
        Query = """
            SELECT b.Id, b.Title, b.Author, b.ThumbnailImage,
                   c.Category, s.Subject, b.CreatedDate,
                   -- Simple relevance scoring
                   (CASE WHEN b.Title LIKE ? THEN 4 ELSE 0 END +
                    CASE WHEN b.Author LIKE ? THEN 3 ELSE 0 END +
                    CASE WHEN c.Category LIKE ? THEN 2 ELSE 0 END +
                    CASE WHEN s.Subject LIKE ? THEN 1 ELSE 0 END) as Relevance
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE b.Title LIKE ? OR b.Author LIKE ? OR c.Category LIKE ? OR s.Subject LIKE ?
            ORDER BY Relevance DESC, b.Title
            LIMIT ?
        """
        
        SearchPattern = f"%{SearchTerm}%"
        Parameters = [SearchPattern] * 8 + [Limit]  # 8 search patterns + limit
        
        return self.ExecuteQuery(Query, tuple(Parameters))
        
    def GetRecentBooks(self, Days: int = 30, Limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently modified books."""
        Query = """
            SELECT b.Id, b.Title, b.Author, b.ThumbnailImage,
                   c.Category, s.Subject, b.ModifiedDate
            FROM Books b
            LEFT JOIN Categories c ON b.CategoryId = c.Id
            LEFT JOIN Subjects s ON b.SubjectId = s.Id
            WHERE b.ModifiedDate >= datetime('now', '-{} days')
            ORDER BY b.ModifiedDate DESC
            LIMIT ?
        """.format(Days)
        
        return self.ExecuteQuery(Query, (Limit,))
        
    def GetBookStats(self) -> Dict[str, Any]:
        """Get detailed book statistics."""
        Stats = {}
        
        # Books by category
        CategoryStats = self.ExecuteQuery("""
            SELECT c.Category, COUNT(b.Id) as BookCount
            FROM Categories c
            LEFT JOIN Books b ON c.Id = b.CategoryId
            GROUP BY c.Id, c.Category
            ORDER BY BookCount DESC
        """)
        Stats['BooksByCategory'] = CategoryStats
        
        # Books by author (top 10)
        AuthorStats = self.ExecuteQuery("""
            SELECT b.Author, COUNT(b.Id) as BookCount
            FROM Books b
            WHERE b.Author IS NOT NULL AND b.Author != ''
            GROUP BY b.Author
            ORDER BY BookCount DESC
            LIMIT 10
        """)
        Stats['TopAuthors'] = AuthorStats
        
        # Total file size
        SizeStats = self.ExecuteQuery("""
            SELECT 
                SUM(FileSize) as TotalSize,
                AVG(FileSize) as AverageSize,
                MAX(FileSize) as LargestFile,
                MIN(FileSize) as SmallestFile
            FROM Books 
            WHERE FileSize IS NOT NULL AND FileSize > 0
        """)
        Stats['FileSizeStats'] = SizeStats[0] if SizeStats else {}
        
        # Page count statistics
        PageStats = self.ExecuteQuery("""
            SELECT 
                SUM(PageCount) as TotalPages,
                AVG(PageCount) as AveragePages,
                MAX(PageCount) as LongestBook,
                MIN(PageCount) as ShortestBook
            FROM Books 
            WHERE PageCount IS NOT NULL AND PageCount > 0
        """)
        Stats['PageStats'] = PageStats[0] if PageStats else {}
        
        return Stats
        
    def ValidateDatabase(self) -> Dict[str, Any]:
        """Validate database integrity and return status report."""
        ValidationResults = {
            'status': 'healthy',
            'issues': [],
            'statistics': {}
        }
        
        try:
            # Check for books without categories
            OrphanBooks = self.ExecuteQuery("""
                SELECT COUNT(*) as Count 
                FROM Books 
                WHERE CategoryId IS NULL
            """)
            
            if OrphanBooks and OrphanBooks[0]['Count'] > 0:
                ValidationResults['issues'].append(
                    f"{OrphanBooks[0]['Count']} books without categories"
                )
            
            # Check for books without subjects
            SubjectlessBooks = self.ExecuteQuery("""
                SELECT COUNT(*) as Count 
                FROM Books 
                WHERE SubjectId IS NULL
            """)
            
            if SubjectlessBooks and SubjectlessBooks[0]['Count'] > 0:
                ValidationResults['issues'].append(
                    f"{SubjectlessBooks[0]['Count']} books without subjects"
                )
            
            # Check for missing thumbnails
            NoThumbnails = self.ExecuteQuery("""
                SELECT COUNT(*) as Count 
                FROM Books 
                WHERE ThumbnailImage IS NULL
            """)
            
            if NoThumbnails and NoThumbnails[0]['Count'] > 0:
                ValidationResults['issues'].append(
                    f"{NoThumbnails[0]['Count']} books without thumbnails"
                )
            
            # Get basic statistics
            ValidationResults['statistics'] = self.GetDatabaseStats()
            
            if len(ValidationResults['issues']) == 0:
                ValidationResults['status'] = 'excellent'
            elif len(ValidationResults['issues']) < 3:
                ValidationResults['status'] = 'good'
            else:
                ValidationResults['status'] = 'needs_attention'
                
        except Exception as Error:
            ValidationResults['status'] = 'error'
            ValidationResults['issues'].append(f"Validation failed: {Error}")
            
        return ValidationResults
        
    def __enter__(self):
        """Context manager entry."""
        self.Connect()
        return self
        
    def __exit__(self, ExcType, ExcVal, ExcTb):
        """Context manager exit."""
        self.Disconnect()

# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    with DatabaseManager() as Db:
        # Test database connection and basic queries
        Stats = Db.GetDatabaseStats()
        print(f"Database Stats: {json.dumps(Stats, indent=2)}")
        
        # Test book retrieval
        Books = Db.GetBooks(Limit=5)
        print(f"Found {len(Books)} books")
        
        # Test categories
        Categories = Db.GetCategories()
        print(f"Found {len(Categories)} categories")
        
        # Test validation
        Validation = Db.ValidateDatabase()
        print(f"Database validation: {Validation['status']}")
        if Validation['issues']:
            print("Issues found:")
            for Issue in Validation['issues']:
                print(f"  - {Issue}")