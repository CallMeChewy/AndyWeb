# File: DatabaseManager.py
# Path: Source/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  08:55AM
"""
Description: NEW SCHEMA - Database Manager for Relational Schema with BLOB Thumbnails
Updated for the new relational schema with category_id/subject_id and BLOB thumbnails.
Perfect for future web/mobile deployment!
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import os


class DatabaseManager:
    """
    NEW SCHEMA - Database manager for relational schema with BLOB thumbnails.
    Optimized for web/mobile deployment with minimal Google Drive interactions.
    """
    
    def __init__(self, DatabasePath: str = "Data/Databases/MyLibrary.db"):
        self.DatabasePath = DatabasePath
        self.Connection = None
        self.Logger = logging.getLogger(self.__class__.__name__)
        self.EnsureDatabaseDirectory()
        self.Connect()
    
    def EnsureDatabaseDirectory(self):
        """Ensure the database directory exists."""
        DatabaseDir = Path(self.DatabasePath).parent
        DatabaseDir.mkdir(parents=True, exist_ok=True)
    
    def Connect(self) -> bool:
        """Connect to the SQLite database."""
        try:
            self.Connection = sqlite3.connect(self.DatabasePath)
            self.Connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Test connection
            Cursor = self.Connection.cursor()
            Cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            Tables = Cursor.fetchall()
            TableCount = len(Tables)
            
            self.Logger.info(f"Database connection successful: {TableCount} tables found")
            return True
            
        except Exception as Error:
            self.Logger.error(f"Database connection failed: {Error}")
            return False
    
    def Close(self):
        """Close the database connection properly."""
        try:
            if self.Connection:
                self.Connection.close()
                self.Connection = None
                self.Logger.info("Database connection closed successfully")
        except Exception as Error:
            self.Logger.error(f"Error closing database connection: {Error}")
    
    def ExecuteQuery(self, Query: str, Parameters: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a SQL query with proper error handling."""
        try:
            if not self.Connection:
                self.Logger.error("No database connection available")
                return []
            
            Cursor = self.Connection.cursor()
            Cursor.execute(Query, Parameters)
            
            # For SELECT queries, return results
            if Query.strip().upper().startswith('SELECT'):
                Results = Cursor.fetchall()
                return Results
            else:
                # For INSERT/UPDATE/DELETE queries, commit changes
                self.Connection.commit()
                return []
                
        except sqlite3.Error as Error:
            self.Logger.error(f"Database error: {Error}")
            self.Logger.error(f"Query execution failed: {Query} - {Error}")
            return []
        except Exception as Error:
            self.Logger.error(f"Unexpected error executing query: {Error}")
            return []
    
    def GetBooks(self, Category: str = "", Subject: str = "", SearchTerm: str = "") -> List[Dict[str, Any]]:
        """
        NEW SCHEMA - Get books using JOINs for relational schema.
        Returns books with category/subject names and BLOB thumbnail data.
        """
        try:
            # NEW SCHEMA: Use JOINs to get category and subject names
            Query = """
                SELECT b.id, b.title, b.author, b.FilePath, b.ThumbnailImage,
                       c.category as Category, s.subject as Subject,
                       b.last_opened, b.Rating, b.Notes
                FROM books b
                LEFT JOIN categories c ON b.category_id = c.id
                LEFT JOIN subjects s ON b.subject_id = s.id
                WHERE 1=1
            """
            Parameters = []
            
            if Category and Category != "All Categories":
                Query += " AND c.category = ?"
                Parameters.append(Category)
            
            if Subject and Subject != "All Subjects":
                Query += " AND s.subject = ?"
                Parameters.append(Subject)
            
            if SearchTerm:
                Query += " AND (b.title LIKE ? OR b.author LIKE ?)"
                SearchPattern = f"%{SearchTerm}%"
                Parameters.extend([SearchPattern, SearchPattern])
            
            Query += " ORDER BY b.title"
            
            Rows = self.ExecuteQuery(Query, tuple(Parameters))
            
            # Convert rows to dictionaries with proper field names
            Books = []
            for Row in Rows:
                BookDict = {
                    'id': Row['id'],
                    'Title': Row['title'],
                    'Author': Row['author'] or 'Unknown Author',  
                    'Category': Row['Category'] or 'General',
                    'Subject': Row['Subject'] or 'General',
                    'FilePath': Row['FilePath'] or '',
                    'ThumbnailData': Row['ThumbnailImage'],  # BLOB data for thumbnail
                    'LastOpened': Row['last_opened'],
                    'Rating': Row['Rating'] or 0,
                    'Notes': Row['Notes'] or ''
                }
                Books.append(BookDict)
            
            self.Logger.info(f"Retrieved {len(Books)} books using new relational schema")
            return Books
            
        except Exception as Error:
            self.Logger.error(f"Failed to get books: {Error}")
            return []
    
    def GetCategories(self) -> List[str]:
        """NEW SCHEMA - Get categories from categories table."""
        try:
            Rows = self.ExecuteQuery("SELECT category FROM categories ORDER BY category")
            Categories = [Row[0] for Row in Rows if Row[0]]
            self.Logger.info(f"Retrieved {len(Categories)} categories from categories table")
            return Categories
        except Exception as Error:
            self.Logger.error(f"Failed to get categories: {Error}")
            return []
    
    def GetSubjects(self, Category: str = "") -> List[str]:
        """NEW SCHEMA - Get subjects using JOIN with categories table."""
        try:
            if Category and Category != "All Categories":
                # Get subjects for specific category
                Query = """
                    SELECT DISTINCT s.subject 
                    FROM subjects s
                    JOIN categories c ON s.category_id = c.id
                    WHERE c.category = ?
                    ORDER BY s.subject
                """
                Parameters = (Category,)
            else:
                # Get all subjects
                Query = "SELECT DISTINCT subject FROM subjects ORDER BY subject"
                Parameters = ()
            
            Rows = self.ExecuteQuery(Query, Parameters)
            Subjects = [Row[0] for Row in Rows if Row[0]]
            self.Logger.info(f"Retrieved {len(Subjects)} subjects for category '{Category}'")
            return Subjects
        except Exception as Error:
            self.Logger.error(f"Failed to get subjects: {Error}")
            return []
    
    def UpdateLastOpened(self, BookTitle: str):
        """Update last opened timestamp for a book."""
        try:
            from datetime import datetime
            Timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update using book title
            self.ExecuteQuery("UPDATE books SET last_opened = ? WHERE title = ?", (Timestamp, BookTitle))
            self.Logger.info(f"Updated last_opened for book: {BookTitle}")
            
        except Exception as Error:
            self.Logger.warning(f"Could not update last opened time: {Error}")
    
    def GetDatabaseStats(self) -> Dict[str, int]:
        """Get database statistics from the new schema."""
        Stats = {}
        
        try:
            # Get category count
            CategoryRows = self.ExecuteQuery("SELECT COUNT(*) FROM categories")
            Stats['Categories'] = CategoryRows[0][0] if CategoryRows else 0
            
            # Get subject count  
            SubjectRows = self.ExecuteQuery("SELECT COUNT(*) FROM subjects")
            Stats['Subjects'] = SubjectRows[0][0] if SubjectRows else 0
            
            # Get book count
            BookRows = self.ExecuteQuery("SELECT COUNT(*) FROM books")
            Stats['Books'] = BookRows[0][0] if BookRows else 0
            
            self.Logger.info(f"Database stats: {Stats['Books']} books, {Stats['Categories']} categories, {Stats['Subjects']} subjects")
            
        except Exception as Error:
            self.Logger.error(f"Failed to get database stats: {Error}")
            Stats = {'Categories': 0, 'Subjects': 0, 'Books': 0}
        
        return Stats
    
    def GetThumbnailBlob(self, BookId: int) -> Optional[bytes]:
        """
        Get thumbnail BLOB data for a specific book.
        
        Args:
            BookId: Database ID of the book
            
        Returns:
            BLOB data as bytes, or None if not found
        """
        try:
            Rows = self.ExecuteQuery("SELECT ThumbnailImage FROM books WHERE id = ?", (BookId,))
            if Rows and Rows[0][0]:
                return Rows[0][0]  # Return BLOB data
            return None
        except Exception as Error:
            self.Logger.error(f"Failed to get thumbnail for book ID {BookId}: {Error}")
            return None