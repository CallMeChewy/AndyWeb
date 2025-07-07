# File: DatabaseModels.py
# Path: Source/Data/DatabaseModels.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  05:15PM
"""
Description: Data Models for Anderson's Library
Contains all data model classes and structures for managing library books,
including database table representations, search results, and book metadata.
"""

import os
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


@dataclass
class BookRecord:
    """
    Represents a complete book record from the database.
    Contains all metadata and file information for a single book.
    """
    
    # Primary identifiers
    Id: int = 0
    Title: str = ""
    Author: str = ""
    
    # File information
    FileName: str = ""
    FilePath: str = ""
    FileSize: int = 0
    
    # Metadata
    Subject: str = ""
    Publisher: str = ""
    PublishDate: str = ""
    Keywords: str = ""
    Description: str = ""
    
    # File properties
    PageCount: int = 0
    CreationDate: str = ""
    ModificationDate: str = ""
    
    # Library classification
    Category: str = ""
    Subcategory: str = ""
    Language: str = "English"
    
    # Status and tracking
    DateAdded: str = ""
    LastAccessed: str = ""
    Rating: int = 0
    ReadStatus: str = "Unread"
    
    # Technical details
    FileFormat: str = "PDF"
    FileHash: str = ""
    ThumbnailPath: str = ""
    
    # Additional metadata
    ISBN: str = ""
    Edition: str = ""
    Series: str = ""
    Volume: str = ""
    
    def __post_init__(self):
        """Post-initialization validation and cleanup"""
        # Ensure required fields have defaults
        if not self.DateAdded:
            self.DateAdded = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Clean up file paths
        if self.FilePath:
            self.FilePath = os.path.normpath(self.FilePath)
        
        # Validate rating range
        if self.Rating < 0:
            self.Rating = 0
        elif self.Rating > 5:
            self.Rating = 5
    
    def GetDisplayTitle(self) -> str:
        """Get formatted title for display"""
        if len(self.Title) > 50:
            return self.Title[:47] + "..."
        return self.Title
    
    def GetDisplayAuthor(self) -> str:
        """Get formatted author for display"""
        if len(self.Author) > 30:
            return self.Author[:27] + "..."
        return self.Author
    
    def GetFileSizeFormatted(self) -> str:
        """Get human-readable file size"""
        if self.FileSize < 1024:
            return f"{self.FileSize} bytes"
        elif self.FileSize < 1024 * 1024:
            return f"{self.FileSize / 1024:.1f} KB"
        elif self.FileSize < 1024 * 1024 * 1024:
            return f"{self.FileSize / (1024 * 1024):.1f} MB"
        else:
            return f"{self.FileSize / (1024 * 1024 * 1024):.1f} GB"
    
    def FileExists(self) -> bool:
        """Check if the book file actually exists"""
        if not self.FilePath:
            return False
        return os.path.exists(self.FilePath)
    
    def GetFullPath(self, BasePath: str = "") -> str:
        """Get complete file path, optionally with base path"""
        if BasePath and not os.path.isabs(self.FilePath):
            return os.path.join(BasePath, self.FilePath)
        return self.FilePath


@dataclass
class SearchCriteria:
    """
    Represents search and filter criteria for book queries.
    Used by the interface to communicate search parameters to the database layer.
    """
    
    # Text search fields
    SearchText: str = ""
    SearchTitle: bool = True
    SearchAuthor: bool = True
    SearchSubject: bool = True
    SearchKeywords: bool = True
    SearchDescription: bool = False
    
    # Filter criteria
    Categories: List[str] = field(default_factory=list)
    Authors: List[str] = field(default_factory=list)
    Subjects: List[str] = field(default_factory=list)
    Languages: List[str] = field(default_factory=list)
    
    # Date ranges
    DateAddedFrom: Optional[str] = None
    DateAddedTo: Optional[str] = None
    PublishDateFrom: Optional[str] = None
    PublishDateTo: Optional[str] = None
    
    # Numeric filters
    MinPageCount: Optional[int] = None
    MaxPageCount: Optional[int] = None
    MinRating: int = 0
    MaxRating: int = 5
    
    # File properties
    FileFormats: List[str] = field(default_factory=list)
    MinFileSize: Optional[int] = None
    MaxFileSize: Optional[int] = None
    
    # Status filters
    ReadStatuses: List[str] = field(default_factory=list)
    HasThumbnail: Optional[bool] = None
    FileExists: Optional[bool] = None
    
    # Sort options
    SortBy: str = "Title"
    SortOrder: str = "ASC"
    
    # Pagination
    Limit: Optional[int] = None
    Offset: int = 0
    
    def IsEmpty(self) -> bool:
        """Check if search criteria is empty (no filters applied)"""
        return (not self.SearchText and
                not self.Categories and
                not self.Authors and
                not self.Subjects and
                not self.Languages and
                not self.DateAddedFrom and
                not self.DateAddedTo and
                not self.PublishDateFrom and
                not self.PublishDateTo and
                self.MinPageCount is None and
                self.MaxPageCount is None and
                self.MinRating == 0 and
                self.MaxRating == 5 and
                not self.FileFormats and
                self.MinFileSize is None and
                self.MaxFileSize is None and
                not self.ReadStatuses and
                self.HasThumbnail is None and
                self.FileExists is None)
    
    def GetSummary(self) -> str:
        """Get human-readable summary of active filters"""
        Filters = []
        
        if self.SearchText:
            Filters.append(f"Text: '{self.SearchText}'")
        
        if self.Categories:
            Filters.append(f"Categories: {', '.join(self.Categories)}")
        
        if self.Authors:
            Filters.append(f"Authors: {', '.join(self.Authors)}")
        
        if self.Subjects:
            Filters.append(f"Subjects: {', '.join(self.Subjects)}")
        
        if self.MinRating > 0 or self.MaxRating < 5:
            Filters.append(f"Rating: {self.MinRating}-{self.MaxRating}")
        
        if not Filters:
            return "No filters active"
        
        return "; ".join(Filters)


@dataclass 
class SearchResult:
    """
    Represents the result of a database search operation.
    Contains the found books plus metadata about the search.
    """
    
    Books: List[BookRecord] = field(default_factory=list)
    TotalCount: int = 0
    FilteredCount: int = 0
    SearchTime: float = 0.0
    SearchCriteria: Optional[SearchCriteria] = None
    
    # Error handling
    Success: bool = True
    ErrorMessage: str = ""
    
    def __post_init__(self):
        """Post-initialization calculations"""
        if not self.TotalCount:
            self.TotalCount = len(self.Books)
        
        if not self.FilteredCount:
            self.FilteredCount = len(self.Books)
    
    def HasResults(self) -> bool:
        """Check if search returned any results"""
        return len(self.Books) > 0
    
    def GetResultSummary(self) -> str:
        """Get human-readable result summary"""
        if not self.Success:
            return f"Search failed: {self.ErrorMessage}"
        
        if not self.HasResults():
            return "No books found"
        
        if self.FilteredCount == self.TotalCount:
            return f"Found {self.TotalCount} books"
        else:
            return f"Found {self.FilteredCount} of {self.TotalCount} books"


@dataclass
class CategoryInfo:
    """
    Represents category information for filtering and display.
    Used to populate filter dropdowns and category statistics.
    """
    
    Name: str = ""
    BookCount: int = 0
    ParentCategory: str = ""
    Description: str = ""
    DisplayOrder: int = 0
    
    def GetDisplayName(self) -> str:
        """Get formatted display name with count"""
        return f"{self.Name} ({self.BookCount})"


@dataclass
class LibraryStatistics:
    """
    Represents overall library statistics for dashboard display.
    Contains counts, file sizes, and other summary information.
    """
    
    TotalBooks: int = 0
    TotalSize: int = 0
    TotalAuthors: int = 0
    TotalCategories: int = 0
    
    # File type breakdown
    FileTypeCounts: Dict[str, int] = field(default_factory=dict)
    
    # Rating statistics
    AverageRating: float = 0.0
    RatedBooks: int = 0
    
    # Date statistics
    OldestBook: str = ""
    NewestBook: str = ""
    BooksAddedThisMonth: int = 0
    BooksAddedThisYear: int = 0
    
    # File status
    MissingFiles: int = 0
    BooksWithThumbnails: int = 0
    
    def GetFormattedTotalSize(self) -> str:
        """Get human-readable total library size"""
        if self.TotalSize < 1024 * 1024 * 1024:
            return f"{self.TotalSize / (1024 * 1024):.1f} MB"
        else:
            return f"{self.TotalSize / (1024 * 1024 * 1024):.1f} GB"
    
    def GetSummary(self) -> str:
        """Get brief library summary"""
        return (f"{self.TotalBooks} books, {self.TotalAuthors} authors, "
                f"{self.GetFormattedTotalSize()}")


# Legacy compatibility - add aliases for old class names
Book = BookRecord  # Compatibility alias
Category = CategoryInfo  # Compatibility alias  
Subject = CategoryInfo  # Compatibility alias for subjects


def CreateBookRecordFromDict(Data: Dict[str, Any]) -> BookRecord:
    """
    Factory function to create BookRecord from database row dictionary.
    Handles type conversion and missing fields gracefully.
    """
    try:
        # Handle None values and type conversions
        SafeData = {}
        for Key, Value in Data.items():
            if Value is None:
                SafeData[Key] = ""
            else:
                SafeData[Key] = Value
        
        return BookRecord(
            Id=int(SafeData.get('Id', 0)),
            Title=str(SafeData.get('Title', '')),
            Author=str(SafeData.get('Author', '')),
            FileName=str(SafeData.get('FileName', '')),
            FilePath=str(SafeData.get('FilePath', '')),
            FileSize=int(SafeData.get('FileSize', 0)),
            Subject=str(SafeData.get('Subject', '')),
            Publisher=str(SafeData.get('Publisher', '')),
            PublishDate=str(SafeData.get('PublishDate', '')),
            Keywords=str(SafeData.get('Keywords', '')),
            Description=str(SafeData.get('Description', '')),
            PageCount=int(SafeData.get('PageCount', 0)),
            CreationDate=str(SafeData.get('CreationDate', '')),
            ModificationDate=str(SafeData.get('ModificationDate', '')),
            Category=str(SafeData.get('Category', '')),
            Subcategory=str(SafeData.get('Subcategory', '')),
            Language=str(SafeData.get('Language', 'English')),
            DateAdded=str(SafeData.get('DateAdded', '')),
            LastAccessed=str(SafeData.get('LastAccessed', '')),
            Rating=int(SafeData.get('Rating', 0)),
            ReadStatus=str(SafeData.get('ReadStatus', 'Unread')),
            FileFormat=str(SafeData.get('FileFormat', 'PDF')),
            FileHash=str(SafeData.get('FileHash', '')),
            ThumbnailPath=str(SafeData.get('ThumbnailPath', '')),
            ISBN=str(SafeData.get('ISBN', '')),
            Edition=str(SafeData.get('Edition', '')),
            Series=str(SafeData.get('Series', '')),
            Volume=str(SafeData.get('Volume', ''))
        )
        
    except Exception as Error:
        logging.error(f"Error creating BookRecord from data: {Error}")
        logging.error(f"Data: {Data}")
        return BookRecord()


def ValidateBookRecord(Book: BookRecord) -> Tuple[bool, List[str]]:
    """
    Validate a BookRecord for completeness and correctness.
    Returns (IsValid, ErrorMessages).
    """
    Errors = []
    
    # Required fields
    if not Book.Title.strip():
        Errors.append("Title is required")
    
    if not Book.FileName.strip():
        Errors.append("File name is required")
    
    if not Book.FilePath.strip():
        Errors.append("File path is required")
    
    # File existence
    if Book.FilePath and not os.path.exists(Book.FilePath):
        Errors.append(f"File does not exist: {Book.FilePath}")
    
    # Value ranges
    if Book.Rating < 0 or Book.Rating > 5:
        Errors.append("Rating must be between 0 and 5")
    
    if Book.PageCount < 0:
        Errors.append("Page count cannot be negative")
    
    if Book.FileSize < 0:
        Errors.append("File size cannot be negative")
    
    return len(Errors) == 0, Errors


# Database table structure definitions
DATABASE_SCHEMA = {
    "Books": {
        "Id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "Title": "TEXT NOT NULL",
        "Author": "TEXT",
        "FileName": "TEXT NOT NULL",
        "FilePath": "TEXT NOT NULL",
        "FileSize": "INTEGER DEFAULT 0",
        "Subject": "TEXT",
        "Publisher": "TEXT", 
        "PublishDate": "TEXT",
        "Keywords": "TEXT",
        "Description": "TEXT",
        "PageCount": "INTEGER DEFAULT 0",
        "CreationDate": "TEXT",
        "ModificationDate": "TEXT",
        "Category": "TEXT",
        "Subcategory": "TEXT",
        "Language": "TEXT DEFAULT 'English'",
        "DateAdded": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "LastAccessed": "TEXT",
        "Rating": "INTEGER DEFAULT 0",
        "ReadStatus": "TEXT DEFAULT 'Unread'",
        "FileFormat": "TEXT DEFAULT 'PDF'",
        "FileHash": "TEXT",
        "ThumbnailPath": "TEXT",
        "ISBN": "TEXT",
        "Edition": "TEXT",
        "Series": "TEXT",
        "Volume": "TEXT"
    }
}

# Common SQL queries as constants
COMMON_QUERIES = {
    "SELECT_ALL": "SELECT * FROM Books",
    "SELECT_BY_ID": "SELECT * FROM Books WHERE Id = ?",
    "SELECT_BY_TITLE": "SELECT * FROM Books WHERE Title LIKE ?",
    "SELECT_BY_AUTHOR": "SELECT * FROM Books WHERE Author LIKE ?",
    "COUNT_TOTAL": "SELECT COUNT(*) FROM Books",
    "GET_CATEGORIES": "SELECT DISTINCT Category FROM Books WHERE Category IS NOT NULL ORDER BY Category",
    "GET_AUTHORS": "SELECT DISTINCT Author FROM Books WHERE Author IS NOT NULL ORDER BY Author",
    "GET_SUBJECTS": "SELECT DISTINCT Subject FROM Books WHERE Subject IS NOT NULL ORDER BY Subject"
}

# Legacy compatibility - add aliases for old class names AND function names
Book = BookRecord  # Compatibility alias
Category = CategoryInfo  # Compatibility alias  
Subject = CategoryInfo  # Compatibility alias for subjects
CreateBookFromRow = CreateBookRecordFromDict  # Compatibility alias for old function name