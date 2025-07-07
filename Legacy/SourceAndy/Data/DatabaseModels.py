# File: DatabaseModels.py
# Path: Source/Data/DatabaseModels.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-05
# Last Modified: 2025-07-05  07:35PM
"""
Description: Complete Database Models with Full Import Compatibility
Includes all expected import functions for backward compatibility with existing code.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Book:
    """
    Book data model representing a book in the library.
    Compatible with existing lowercase database schema.
    """
    Title: str
    Category: Optional[str] = None
    Subject: Optional[str] = None
    Authors: Optional[str] = None
    Pages: Optional[int] = None
    Rating: Optional[float] = None
    AddedDate: Optional[str] = None
    LastOpened: Optional[str] = None
    FilePath: Optional[str] = None
    FileSize: Optional[int] = None
    
    def __post_init__(self):
        """Validate and clean data after initialization"""
        # Ensure title is not empty
        if not self.Title or not self.Title.strip():
            raise ValueError("Book title cannot be empty")
        
        # Clean whitespace
        self.Title = self.Title.strip()
        if self.Category:
            self.Category = self.Category.strip()
        if self.Subject:
            self.Subject = self.Subject.strip()
        if self.Authors:
            self.Authors = self.Authors.strip()
    
    def GetDisplayTitle(self) -> str:
        """Get title for display purposes"""
        return self.Title
    
    def GetDisplayAuthors(self) -> str:
        """Get authors for display purposes"""
        return self.Authors if self.Authors else "Unknown Author"
    
    def HasValidPath(self) -> bool:
        """Check if book has valid file path"""
        return bool(self.FilePath and self.FilePath.strip())


@dataclass
class SearchCriteria:
    """
    Search criteria for filtering books.
    Now includes all necessary attributes for proper functionality.
    """
    SearchTerm: Optional[str] = None  # ✅ FIXED: Added missing SearchTerm attribute
    Categories: Optional[List[str]] = None
    Subjects: Optional[List[str]] = None
    Authors: Optional[List[str]] = None
    MinRating: Optional[float] = None
    MaxRating: Optional[float] = None
    SortBy: str = "Title"  # Title, Authors, Category, Subject, Rating, AddedDate
    SortOrder: str = "ASC"  # ASC or DESC
    Limit: Optional[int] = None
    Offset: int = 0
    
    def __post_init__(self):
        """Initialize default values and validate"""
        if self.Categories is None:
            self.Categories = []
        if self.Subjects is None:
            self.Subjects = []
        if self.Authors is None:
            self.Authors = []
        
        # Validate sort order
        if self.SortOrder.upper() not in ["ASC", "DESC"]:
            self.SortOrder = "ASC"
        
        # Clean search term
        if self.SearchTerm:
            self.SearchTerm = self.SearchTerm.strip()
            if not self.SearchTerm:
                self.SearchTerm = None
    
    def IsEmpty(self) -> bool:
        """Check if criteria has any active filters"""
        return (
            not self.SearchTerm
            and not self.Categories
            and not self.Subjects  
            and not self.Authors
            and self.MinRating is None
            and self.MaxRating is None
        )
    
    def GetDescription(self) -> str:
        """Get human-readable description of criteria"""
        parts = []
        
        if self.SearchTerm:
            parts.append(f"Search: '{self.SearchTerm}'")
        
        if self.Categories:
            parts.append(f"Categories: {', '.join(self.Categories)}")
        
        if self.Subjects:
            parts.append(f"Subjects: {', '.join(self.Subjects)}")
        
        if self.Authors:
            parts.append(f"Authors: {', '.join(self.Authors)}")
        
        if self.MinRating is not None:
            parts.append(f"Min Rating: {self.MinRating}")
        
        if not parts:
            return "No filters applied"
        
        return " | ".join(parts)


@dataclass
class SearchResult:
    """
    Result container for search operations.
    """
    Books: List[Book]
    Success: bool = True
    ErrorMessage: Optional[str] = None
    TotalCount: Optional[int] = None
    SearchCriteria: Optional[SearchCriteria] = None
    ExecutionTime: Optional[float] = None
    
    def __post_init__(self):
        """Set total count if not provided"""
        if self.TotalCount is None:
            self.TotalCount = len(self.Books)
    
    def GetBookCount(self) -> int:
        """Get number of books in result"""
        return len(self.Books)
    
    def HasBooks(self) -> bool:
        """Check if result contains any books"""
        return len(self.Books) > 0
    
    def GetSuccessMessage(self) -> str:
        """Get success message for display"""
        if not self.Success:
            return f"Error: {self.ErrorMessage or 'Unknown error'}"
        
        count = len(self.Books)
        if count == 0:
            return "No books found"
        elif count == 1:
            return "Found 1 book"
        else:
            return f"Found {count} books"


@dataclass  
class Category:
    """Category information"""
    Name: str
    BookCount: int = 0
    
    def __post_init__(self):
        """Clean category name"""
        if self.Name:
            self.Name = self.Name.strip()


@dataclass
class Subject:
    """Subject information"""
    Name: str
    CategoryName: Optional[str] = None
    BookCount: int = 0
    
    def __post_init__(self):
        """Clean subject and category names"""
        if self.Name:
            self.Name = self.Name.strip()
        if self.CategoryName:
            self.CategoryName = self.CategoryName.strip()


@dataclass
class LibraryStatistics:
    """Library statistics container"""
    TotalBooks: int = 0
    TotalCategories: int = 0
    TotalSubjects: int = 0
    TotalAuthors: int = 0
    AverageRating: float = 0.0
    TopCategories: Optional[Dict[str, int]] = None
    TopSubjects: Optional[Dict[str, int]] = None
    TopAuthors: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """Initialize empty dicts if None"""
        if self.TopCategories is None:
            self.TopCategories = {}
        if self.TopSubjects is None:
            self.TopSubjects = {}
        if self.TopAuthors is None:
            self.TopAuthors = {}


# Helper functions for data conversion and compatibility

def CreateBookFromDatabaseRow(row: tuple) -> Book:
    """
    Create Book object from database row.
    Compatible with existing lowercase schema.
    
    Args:
        row: Database row tuple (id, title, author, category_id, subject_id, filepath, etc.)
        
    Returns:
        Book object
    """
    # Handle different row formats from existing database
    try:
        if len(row) >= 7:
            # Full row with joins: (id, title, author, category_id, subject_id, filepath, thumbnailpath, category, subject)
            return Book(
                Title=row[1] or "",
                Authors=row[2] or "Unknown Author", 
                Category=row[7] if len(row) > 7 else None,
                Subject=row[8] if len(row) > 8 else None,
                FilePath=row[5] if len(row) > 5 else None
            )
        else:
            # Basic row: (id, title, author, category_id, subject_id)
            return Book(
                Title=row[1] or "",
                Authors=row[2] if len(row) > 2 else "Unknown Author",
                FilePath=None
            )
    except (IndexError, TypeError) as e:
        # Fallback for malformed rows
        return Book(
            Title=str(row[1]) if len(row) > 1 else "Unknown Title",
            Authors="Unknown Author"
        )


def CreateCategoryFromRow(row: tuple) -> Category:
    """
    Create Category object from database row.
    
    Args:
        row: Database row tuple (id, category, book_count)
        
    Returns:
        Category object
    """
    try:
        if len(row) >= 2:
            return Category(
                Name=row[1] or "Unknown Category",
                BookCount=row[2] if len(row) > 2 else 0
            )
        else:
            return Category(
                Name=str(row[0]) if len(row) > 0 else "Unknown Category",
                BookCount=0
            )
    except (IndexError, TypeError):
        return Category(Name="Unknown Category", BookCount=0)


def CreateSubjectFromRow(row: tuple) -> Subject:
    """
    Create Subject object from database row.
    
    Args:
        row: Database row tuple (id, subject, category_name, book_count)
        
    Returns:
        Subject object
    """
    try:
        if len(row) >= 2:
            return Subject(
                Name=row[1] or "Unknown Subject",
                CategoryName=row[2] if len(row) > 2 else None,
                BookCount=row[3] if len(row) > 3 else 0
            )
        else:
            return Subject(
                Name=str(row[0]) if len(row) > 0 else "Unknown Subject",
                BookCount=0
            )
    except (IndexError, TypeError):
        return Subject(Name="Unknown Subject", BookCount=0)


def CreateSearchCriteriaFromDict(criteria_dict: dict) -> SearchCriteria:
    """
    Create SearchCriteria from dictionary.
    
    Args:
        criteria_dict: Dictionary with search parameters
        
    Returns:
        SearchCriteria object
    """
    return SearchCriteria(
        SearchTerm=criteria_dict.get('SearchTerm'),
        Categories=criteria_dict.get('Categories', []),
        Subjects=criteria_dict.get('Subjects', []),
        Authors=criteria_dict.get('Authors', []),
        MinRating=criteria_dict.get('MinRating'),
        MaxRating=criteria_dict.get('MaxRating'),
        SortBy=criteria_dict.get('SortBy', 'Title'),
        SortOrder=criteria_dict.get('SortOrder', 'ASC'),
        Limit=criteria_dict.get('Limit'),
        Offset=criteria_dict.get('Offset', 0)
    )


# ✅ FIXED: Add all expected import aliases for backward compatibility
CreateBookFromRow = CreateBookFromDatabaseRow  # Alias for backward compatibility
CreateCategoryFromRow = CreateCategoryFromRow  # Already defined above
CreateSubjectFromRow = CreateSubjectFromRow    # Already defined above


def CreateSearchCriteriaForText(search_text: str) -> SearchCriteria:
    """
    Create SearchCriteria for simple text search.
    
    Args:
        search_text: Text to search for
        
    Returns:
        SearchCriteria object with SearchTerm set
    """
    return SearchCriteria(SearchTerm=search_text)


def CreateSearchCriteriaForFilters(categories: List[str] = None, subjects: List[str] = None) -> SearchCriteria:
    """
    Create SearchCriteria for category/subject filters.
    
    Args:
        categories: List of category names
        subjects: List of subject names
        
    Returns:
        SearchCriteria object with filters set
    """
    return SearchCriteria(
        Categories=categories or [],
        Subjects=subjects or []
    )


# Legacy compatibility exports - add any other functions that might be imported
__all__ = [
    'Book', 'SearchCriteria', 'SearchResult', 'Category', 'Subject', 'LibraryStatistics',
    'CreateBookFromDatabaseRow', 'CreateBookFromRow', 
    'CreateCategoryFromRow', 'CreateSubjectFromRow',
    'CreateSearchCriteriaForText', 'CreateSearchCriteriaForFilters',
    'CreateSearchCriteriaFromDict'
]