-- File: CompleteMyLibraryWebSchema.sql
-- Path: Data/Database/CompleteMyLibraryWebSchema.sql
-- Standard: AIDEV-PascalCase-1.8
-- Created: 2025-07-06
-- Last Modified: 2025-07-06  11:22PM
-- Description: Complete Anderson's Library Web Database Creation Script
-- Author: Herb Bowers - Project Himalaya
-- Purpose: Single script to create entire MyLibraryWeb.db database with all tables and indexes

-- =============================================================================
-- Database Configuration - Enable foreign keys and performance settings
-- =============================================================================
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;

-- =============================================================================
-- Categories Table - Top-level book categorization
-- =============================================================================
CREATE TABLE IF NOT EXISTS Categories (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Category TEXT NOT NULL UNIQUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Subjects Table - Subject classification within categories  
-- =============================================================================
CREATE TABLE IF NOT EXISTS Subjects (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryId INTEGER NOT NULL,
    Subject TEXT NOT NULL,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(CategoryId, Subject),
    FOREIGN KEY(CategoryId) REFERENCES Categories(Id) ON DELETE CASCADE
);

-- =============================================================================
-- Books Table - Core library content with metadata and thumbnails
-- =============================================================================
CREATE TABLE IF NOT EXISTS Books (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT NOT NULL,
    CategoryId INTEGER,
    SubjectId INTEGER, 
    Author TEXT,
    ThumbnailImage BLOB,              -- Embedded thumbnail for web display
    FileSize INTEGER,                 -- File size in bytes
    PageCount INTEGER,                -- Number of pages
    ISBN TEXT,                        -- International Standard Book Number
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(CategoryId) REFERENCES Categories(Id) ON DELETE SET NULL,
    FOREIGN KEY(SubjectId) REFERENCES Subjects(Id) ON DELETE SET NULL
);

-- =============================================================================
-- Performance Indexes - Essential indexes for fast searches
-- =============================================================================

-- Categories table indexes
CREATE INDEX IF NOT EXISTS IdxCategoriesCategory 
ON Categories (Category);

-- Subjects table indexes  
CREATE INDEX IF NOT EXISTS IdxSubjectsCategorySubject 
ON Subjects (CategoryId, Subject);

CREATE INDEX IF NOT EXISTS IdxSubjectsSubject
ON Subjects (Subject);

-- Books table indexes - Core search performance
CREATE INDEX IF NOT EXISTS IdxBooksTitle 
ON Books (Title);

CREATE INDEX IF NOT EXISTS IdxBooksAuthor
ON Books (Author);

CREATE INDEX IF NOT EXISTS IdxBooksCategory
ON Books (CategoryId);

CREATE INDEX IF NOT EXISTS IdxBooksSubject
ON Books (SubjectId);

CREATE INDEX IF NOT EXISTS IdxBooksCategoryTitle 
ON Books (CategoryId, Title);

-- =============================================================================
-- Database Information Table - Track schema version and metadata
-- =============================================================================
CREATE TABLE IF NOT EXISTS DatabaseInfo (
    Key TEXT PRIMARY KEY,
    Value TEXT NOT NULL,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert database metadata
INSERT OR REPLACE INTO DatabaseInfo (Key, Value) VALUES 
('SchemaVersion', '1.0'),
('DatabaseName', 'MyLibraryWeb'),
('CreatedBy', 'Anderson Library System'),
('Standard', 'AIDEV-PascalCase-1.8'),
('LastUpdated', datetime('now'));

-- =============================================================================
-- Verification Queries - Check that everything was created successfully
-- =============================================================================

-- Verify tables exist
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Categories', 'Subjects', 'Books', 'DatabaseInfo');

-- Verify indexes exist  
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'Idx%';

-- Check foreign key enforcement is enabled
PRAGMA foreign_keys;

-- =============================================================================
-- Database Statistics Functions (Views for easy querying)
-- =============================================================================

-- Simple view for library statistics
CREATE VIEW IF NOT EXISTS LibraryStats AS
SELECT 
    (SELECT COUNT(*) FROM Books) AS TotalBooks,
    (SELECT COUNT(*) FROM Categories) AS TotalCategories,
    (SELECT COUNT(*) FROM Subjects) AS TotalSubjects,
    (SELECT COALESCE(SUM(FileSize), 0) FROM Books) AS TotalSizeBytes,
    (SELECT COALESCE(SUM(PageCount), 0) FROM Books) AS TotalPages,
    (SELECT COALESCE(AVG(PageCount), 0) FROM Books WHERE PageCount > 0) AS AvgPages;

-- =============================================================================
-- Sample Data for Testing (Optional - can be commented out for production)
-- =============================================================================

-- Uncomment these lines to add sample data for testing:
/*
INSERT OR IGNORE INTO Categories (Category) VALUES 
('Programming'),
('Science'),
('Mathematics');

INSERT OR IGNORE INTO Subjects (CategoryId, Subject) VALUES 
(1, 'Python'),
(1, 'JavaScript'), 
(1, 'Web Development'),
(2, 'Physics'),
(2, 'Chemistry'),
(3, 'Calculus');

INSERT OR IGNORE INTO Books (Title, CategoryId, SubjectId, Author, PageCount) VALUES 
('Python Crash Course', 1, 1, 'Eric Matthes', 544),
('Learn Python the Hard Way', 1, 1, 'Zed Shaw', 320),
('JavaScript: The Good Parts', 1, 2, 'Douglas Crockford', 176);
*/

-- =============================================================================
-- Final Status Check
-- =============================================================================

-- Display final database status
SELECT 
    'Database MyLibraryWeb.db created successfully!' AS Status,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table') AS TablesCreated,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='index') AS IndexesCreated,
    (SELECT Value FROM DatabaseInfo WHERE Key='SchemaVersion') AS SchemaVersion;