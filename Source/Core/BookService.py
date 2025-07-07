# File: BookService.py
# Path: Source/Core/BookService.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  09:45AM
"""
Description: COMPLETE FIX - Book Service with All Missing Methods
Added missing GetSubjectsForCategory method and fixed all compatibility issues.
"""

import logging
import subprocess
import platform
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from Source.Core.DatabaseManager import DatabaseManager


class BookService:
    """
    COMPLETE FIX - Business logic service with all required methods for new relational schema.
    """
    
    def __init__(self, DatabaseManager: DatabaseManager):
        """
        Initialize book service with database connection.
        
        Args:
            DatabaseManager: Database connection manager
        """
        self.DatabaseManager = DatabaseManager
        self.Logger = logging.getLogger(__name__)
        
        # Cache for performance
        self._CategoryCache: Optional[List[str]] = None
        self._SubjectCache: Optional[List[str]] = None
        self._CategorySubjectCache: Optional[Dict[str, List[str]]] = None
        
        self.Logger.info("BookService initialized with complete method support")
    
    def GetAllBooks(self) -> List[Dict[str, Any]]:
        """
        Get all books from database using new schema.
        
        Returns:
            List of all Book dictionaries
        """
        try:
            Books = self.DatabaseManager.GetBooks()
            self.Logger.debug(f"Retrieved {len(Books)} books using new schema")
            return Books
            
        except Exception as Error:
            self.Logger.error(f"Failed to get all books: {Error}")
            return []
    
    def SearchBooks(self, SearchTerm: str) -> List[Dict[str, Any]]:
        """
        Search books based on search term using new schema.
        
        Args:
            SearchTerm: Search term to look for
            
        Returns:
            List of matching Book dictionaries
        """
        try:
            Books = self.DatabaseManager.GetBooks(SearchTerm=SearchTerm)
            self.Logger.debug(f"Search for '{SearchTerm}' returned {len(Books)} books")
            return Books
            
        except Exception as Error:
            self.Logger.error(f"Failed to search books: {Error}")
            return []
    
    def GetBooksByFilters(self, Category: str = "", Subject: str = "") -> List[Dict[str, Any]]:
        """
        Get books filtered by category and/or subject using new schema.
        
        Args:
            Category: Category name to filter by
            Subject: Subject name to filter by
            
        Returns:
            List of filtered Book dictionaries
        """
        try:
            Books = self.DatabaseManager.GetBooks(Category=Category, Subject=Subject)
            self.Logger.debug(f"Filter Category='{Category}', Subject='{Subject}' returned {len(Books)} books")
            return Books
            
        except Exception as Error:
            self.Logger.error(f"Failed to filter books: {Error}")
            return []
    
    def GetCategories(self) -> List[str]:
        """
        Get all available categories using new schema.
        
        Returns:
            List of category names
        """
        try:
            if self._CategoryCache is None:
                self._CategoryCache = self.DatabaseManager.GetCategories()
            
            return self._CategoryCache.copy()
            
        except Exception as Error:
            self.Logger.error(f"Failed to get categories: {Error}")
            return []
    
    def GetSubjects(self, Category: str = "") -> List[str]:
        """
        Get subjects for a specific category using new schema.
        
        Args:
            Category: Category name to get subjects for
            
        Returns:
            List of subject names
        """
        try:
            Subjects = self.DatabaseManager.GetSubjects(Category)
            return Subjects
            
        except Exception as Error:
            self.Logger.error(f"Failed to get subjects: {Error}")
            return []
    
    def GetSubjectsForCategory(self, Category: str) -> List[str]:
        """
        ADDED: Missing method that was causing errors.
        Get subjects for a specific category using new schema.
        
        Args:
            Category: Category name to get subjects for
            
        Returns:
            List of subject names for the category
        """
        try:
            # Use the existing GetSubjects method which already handles categories
            Subjects = self.GetSubjects(Category)
            self.Logger.debug(f"Retrieved {len(Subjects)} subjects for category '{Category}'")
            return Subjects
            
        except Exception as Error:
            self.Logger.error(f"Failed to get subjects for category '{Category}': {Error}")
            return []
    
    def OpenBook(self, BookIdentifier) -> bool:
        """
        Open a book PDF using system default application.
        
        Args:
            BookIdentifier: Title (str) or ID (int) of book to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            BookData = None
            
            if isinstance(BookIdentifier, str):
                # Search by title
                Books = self.DatabaseManager.GetBooks(SearchTerm=BookIdentifier)
                
                if not Books:
                    self.Logger.warning(f"Book not found: {BookIdentifier}")
                    return False
                
                # Find exact match by title
                for Book in Books:
                    if Book.get('Title', '') == BookIdentifier:
                        BookData = Book
                        break
                
                if not BookData:
                    # Use first result if no exact match
                    BookData = Books[0]
                    
            elif isinstance(BookIdentifier, int):
                # Search by ID
                Books = self.DatabaseManager.GetBooks()
                
                for Book in Books:
                    if Book.get('ID', 0) == BookIdentifier:
                        BookData = Book
                        break
                
                if not BookData:
                    self.Logger.warning(f"Book not found with ID: {BookIdentifier}")
                    return False
            else:
                self.Logger.error(f"Invalid book identifier type: {type(BookIdentifier)}")
                return False
            
            FilePath = BookData.get('FilePath', '')
            BookTitle = BookData.get('Title', 'Unknown')
            
            if not FilePath:
                self.Logger.warning(f"No file path for book: {BookTitle}")
                return False
            
            if not os.path.exists(FilePath):
                self.Logger.warning(f"File does not exist: {FilePath}")
                return False
            
            # Open PDF with system default application
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', FilePath], check=True)
            elif platform.system() == 'Windows':  # Windows
                os.startfile(FilePath)
            else:  # Linux/Unix
                subprocess.run(['xdg-open', FilePath], check=True)
            
            # Update last opened timestamp
            self.DatabaseManager.UpdateLastOpened(BookTitle)
            
            self.Logger.info(f"Successfully opened book: {BookTitle}")
            return True
            
        except subprocess.CalledProcessError as Error:
            self.Logger.error(f"Failed to open book '{BookIdentifier}': {Error}")
            return False
        except Exception as Error:
            self.Logger.error(f"Error opening book '{BookIdentifier}': {Error}")
            return False
    
    def GetBookDetails(self, BookTitle: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific book.
        
        Args:
            BookTitle: Title of the book
            
        Returns:
            Book dictionary or None if not found
        """
        try:
            Books = self.DatabaseManager.GetBooks(SearchTerm=BookTitle)
            
            # Find exact match
            for Book in Books:
                if Book.get('Title', '') == BookTitle:
                    return Book
            
            # Return first match if no exact match
            return Books[0] if Books else None
            
        except Exception as Error:
            self.Logger.error(f"Failed to get book details: {Error}")
            return None
    
    def GetDatabaseStats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts of categories, subjects, books
        """
        try:
            return self.DatabaseManager.GetDatabaseStats()
        except Exception as Error:
            self.Logger.error(f"Failed to get database stats: {Error}")
            return {'Categories': 0, 'Subjects': 0, 'Books': 0}
    
    def ClearCache(self):
        """Clear internal caches to force refresh from database."""
        self._CategoryCache = None
        self._SubjectCache = None
        self._CategorySubjectCache = None
        self.Logger.info("BookService caches cleared")
    
    # ADDITIONAL COMPATIBILITY METHODS
    def GetBooks(self, Category: str = "", Subject: str = "", SearchTerm: str = "") -> List[Dict[str, Any]]:
        """
        ADDED: Direct compatibility method for legacy calls.
        
        Args:
            Category: Category filter
            Subject: Subject filter
            SearchTerm: Search term filter
            
        Returns:
            List of Book dictionaries
        """
        try:
            return self.DatabaseManager.GetBooks(Category=Category, Subject=Subject, SearchTerm=SearchTerm)
        except Exception as Error:
            self.Logger.error(f"Failed to get books with filters: {Error}")
            return []