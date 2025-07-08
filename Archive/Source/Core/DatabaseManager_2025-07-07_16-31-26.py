# File: DatabaseManager.py
# Path: Source/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:20PM
"""
Description: Database manager for AndyWeb - handles SQLite operations for book library
Provides connection management, query execution, and data access for web application.
Designed for eventual MySQL migration without SQLAlchemy dependency.
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
            SELECT b.Id, b.Title, b.Author, b.FilePath, b.ThumbnailImage,
                   b.Rating, b.Notes, b.FileSize, b.PageCount, b.LastOpened,
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
        
        # Recent activity
        RecentBooks = self.ExecuteQuery("""
            SELECT Title, LastOpened 
            FROM Books 
            WHERE LastOpened IS NOT NULL 
            ORDER BY LastOpened DESC 
            LIMIT 5
        """)
        Stats['RecentBooks'] = RecentBooks
        
        return Stats
        
    def UpdateBookLastOpened(self, BookId: int) -> bool:
        """Update last opened timestamp for a book."""
        from datetime import datetime
        
        Query = "UPDATE Books SET LastOpened = ? WHERE Id = ?"
        CurrentTime = datetime.now().isoformat()
        
        return self.ExecuteUpdate(Query, (CurrentTime, BookId))
        
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