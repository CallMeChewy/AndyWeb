# File: MigrateLibraryData.py
# Path: Scripts/Migration/MigrateLibraryData.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  11:35PM
"""
Description: Python Data Migration Script for Anderson's Library
Migrates data from MyLibrary.db to MyLibraryWeb.db with error handling and progress reporting.
"""

import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class LibraryDataMigrator:
    """
    Migrates Anderson's Library data from old schema to new web-compatible schema.
    Handles field mapping, date filling, and provides comprehensive error reporting.
    """
    
    def __init__(self, source_db: str = "MyLibrary.db", target_db: str = "MyLibraryWeb.db"):
        self.source_db = source_db
        self.target_db = target_db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.migration_stats = {
            'categories': 0,
            'subjects': 0, 
            'books': 0,
            'errors': 0
        }
    
    def ValidateDatabases(self) -> bool:
        """Validate that both source and target databases exist and are accessible."""
        try:
            # Check source database exists
            if not Path(self.source_db).exists():
                self.logger.error(f"❌ Source database not found: {self.source_db}")
                return False
            
            # Check target database exists
            if not Path(self.target_db).exists():
                self.logger.error(f"❌ Target database not found: {self.target_db}")
                self.logger.info("💡 Create target database first with: CompleteMyLibraryWebSchema.sql")
                return False
            
            # Test connections
            source_conn = sqlite3.connect(self.source_db)
            target_conn = sqlite3.connect(self.target_db)
            
            # Verify source tables exist
            source_cursor = source_conn.cursor()
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            source_tables = [row[0] for row in source_cursor.fetchall()]
            
            required_source_tables = ['categories', 'subjects', 'books']
            missing_tables = [table for table in required_source_tables if table not in source_tables]
            
            if missing_tables:
                self.logger.error(f"❌ Missing tables in source database: {missing_tables}")
                return False
            
            # Verify target tables exist  
            target_cursor = target_conn.cursor()
            target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            target_tables = [row[0] for row in target_cursor.fetchall()]
            
            required_target_tables = ['Categories', 'Subjects', 'Books', 'DatabaseInfo']
            missing_target_tables = [table for table in required_target_tables if table not in target_tables]
            
            if missing_target_tables:
                self.logger.error(f"❌ Missing tables in target database: {missing_target_tables}")
                return False
            
            source_conn.close()
            target_conn.close()
            
            self.logger.info("✅ Database validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database validation failed: {e}")
            return False
    
    def MigrateCategories(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> bool:
        """Migrate categories data."""
        try:
            self.logger.info("📂 Migrating categories...")
            
            # Get source data
            source_cursor = source_conn.cursor()
            source_cursor.execute("SELECT id, category FROM categories ORDER BY id")
            categories = source_cursor.fetchall()
            
            # Insert into target
            target_cursor = target_conn.cursor()
            current_time = datetime.now().isoformat()
            
            for category_id, category_name in categories:
                target_cursor.execute("""
                    INSERT OR REPLACE INTO Categories (Id, Category, CreatedDate, ModifiedDate)
                    VALUES (?, ?, ?, ?)
                """, (category_id, category_name, current_time, current_time))
            
            target_conn.commit()
            self.migration_stats['categories'] = len(categories)
            self.logger.info(f"✅ Migrated {len(categories)} categories")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Category migration failed: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def MigrateSubjects(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> bool:
        """Migrate subjects data."""
        try:
            self.logger.info("📋 Migrating subjects...")
            
            # Get source data
            source_cursor = source_conn.cursor()
            source_cursor.execute("SELECT id, category_id, subject FROM subjects ORDER BY id")
            subjects = source_cursor.fetchall()
            
            # Insert into target
            target_cursor = target_conn.cursor()
            current_time = datetime.now().isoformat()
            
            for subject_id, category_id, subject_name in subjects:
                target_cursor.execute("""
                    INSERT OR REPLACE INTO Subjects (Id, CategoryId, Subject, CreatedDate, ModifiedDate)
                    VALUES (?, ?, ?, ?, ?)
                """, (subject_id, category_id, subject_name, current_time, current_time))
            
            target_conn.commit()
            self.migration_stats['subjects'] = len(subjects)
            self.logger.info(f"✅ Migrated {len(subjects)} subjects")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Subject migration failed: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def MigrateBooks(self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> bool:
        """Migrate books data with field mapping."""
        try:
            self.logger.info("📚 Migrating books...")
            
            # Get source data with all available fields
            source_cursor = source_conn.cursor()
            source_cursor.execute("""
                SELECT id, title, category_id, subject_id, author, 
                       ThumbnailImage, FileSize, PageCount
                FROM books 
                ORDER BY id
            """)
            books = source_cursor.fetchall()
            
            # Insert into target
            target_cursor = target_conn.cursor()
            current_time = datetime.now().isoformat()
            
            successful_books = 0
            failed_books = 0
            
            for book_data in books:
                try:
                    book_id, title, category_id, subject_id, author, thumbnail, file_size, page_count = book_data
                    
                    # Handle missing author
                    if not author or author.strip() == '':
                        author = 'Unknown Author'
                    
                    target_cursor.execute("""
                        INSERT OR REPLACE INTO Books (
                            Id, Title, CategoryId, SubjectId, Author, 
                            ThumbnailImage, FileSize, PageCount, ISBN,
                            CreatedDate, ModifiedDate
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        book_id, title, category_id, subject_id, author,
                        thumbnail, file_size, page_count, None,  # ISBN set to None
                        current_time, current_time
                    ))
                    
                    successful_books += 1
                    
                except Exception as book_error:
                    self.logger.warning(f"⚠️ Failed to migrate book ID {book_data[0]}: {book_error}")
                    failed_books += 1
            
            target_conn.commit()
            self.migration_stats['books'] = successful_books
            
            self.logger.info(f"✅ Migrated {successful_books} books successfully")
            if failed_books > 0:
                self.logger.warning(f"⚠️ {failed_books} books failed to migrate")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Book migration failed: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def UpdateDatabaseMetadata(self, target_conn: sqlite3.Connection) -> bool:
        """Update database metadata with migration information."""
        try:
            self.logger.info("📝 Updating database metadata...")
            
            target_cursor = target_conn.cursor()
            current_time = datetime.now().isoformat()
            
            # Update existing metadata
            target_cursor.execute("""
                UPDATE DatabaseInfo 
                SET Value = ?, ModifiedDate = ?
                WHERE Key = 'LastUpdated'
            """, (f'Data migrated from {self.source_db} on {current_time}', current_time))
            
            # Add migration metadata
            migration_metadata = [
                ('MigrationDate', current_time),
                ('SourceDatabase', self.source_db),
                ('MigrationStatus', 'Completed Successfully'),
                ('CategoriesMigrated', str(self.migration_stats['categories'])),
                ('SubjectsMigrated', str(self.migration_stats['subjects'])),
                ('BooksMigrated', str(self.migration_stats['books'])),
                ('FieldsPreserved', 'Title, Author, Category, Subject, Thumbnails, FileSize, PageCount'),
                ('FieldsNotMigrated', 'FilePath, Rating, Notes, LastOpened, CreatedBy, LastModifiedBy')
            ]
            
            for key, value in migration_metadata:
                target_cursor.execute("""
                    INSERT OR REPLACE INTO DatabaseInfo (Key, Value, CreatedDate, ModifiedDate)
                    VALUES (?, ?, ?, ?)
                """, (key, value, current_time, current_time))
            
            target_conn.commit()
            self.logger.info("✅ Database metadata updated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Metadata update failed: {e}")
            return False
    
    def VerifyMigration(self, target_conn: sqlite3.Connection) -> Dict[str, Any]:
        """Verify migration was successful and return statistics."""
        try:
            self.logger.info("🔍 Verifying migration...")
            
            target_cursor = target_conn.cursor()
            
            # Get counts
            target_cursor.execute("SELECT COUNT(*) FROM Categories")
            categories_count = target_cursor.fetchone()[0]
            
            target_cursor.execute("SELECT COUNT(*) FROM Subjects")
            subjects_count = target_cursor.fetchone()[0]
            
            target_cursor.execute("SELECT COUNT(*) FROM Books")
            books_count = target_cursor.fetchone()[0]
            
            # Check foreign key integrity
            target_cursor.execute("""
                SELECT COUNT(*) FROM Books b 
                JOIN Categories c ON b.CategoryId = c.Id
            """)
            books_with_valid_categories = target_cursor.fetchone()[0]
            
            target_cursor.execute("""
                SELECT COUNT(*) FROM Books b
                JOIN Subjects s ON b.SubjectId = s.Id
            """)
            books_with_valid_subjects = target_cursor.fetchone()[0]
            
            # Check thumbnails
            target_cursor.execute("SELECT COUNT(*) FROM Books WHERE ThumbnailImage IS NOT NULL")
            books_with_thumbnails = target_cursor.fetchone()[0]
            
            verification_results = {
                'categories_migrated': categories_count,
                'subjects_migrated': subjects_count,
                'books_migrated': books_count,
                'books_with_valid_categories': books_with_valid_categories,
                'books_with_valid_subjects': books_with_valid_subjects,
                'books_with_thumbnails': books_with_thumbnails,
                'foreign_key_integrity': books_with_valid_categories == books_count and books_with_valid_subjects == books_count
            }
            
            self.logger.info("✅ Migration verification completed")
            return verification_results
            
        except Exception as e:
            self.logger.error(f"❌ Migration verification failed: {e}")
            return {}
    
    def RunMigration(self) -> bool:
        """Run the complete migration process."""
        try:
            self.logger.info("🚀 Starting Anderson's Library data migration...")
            self.logger.info(f"📂 Source: {self.source_db}")
            self.logger.info(f"🎯 Target: {self.target_db}")
            
            # Validate databases
            if not self.ValidateDatabases():
                return False
            
            # Open connections
            source_conn = sqlite3.connect(self.source_db)
            target_conn = sqlite3.connect(self.target_db)
            
            # Enable foreign keys in target
            target_conn.execute("PRAGMA foreign_keys = ON")
            
            try:
                # Run migration steps
                success = True
                success &= self.MigrateCategories(source_conn, target_conn)
                success &= self.MigrateSubjects(source_conn, target_conn)  
                success &= self.MigrateBooks(source_conn, target_conn)
                success &= self.UpdateDatabaseMetadata(target_conn)
                
                if success:
                    # Verify migration
                    verification = self.VerifyMigration(target_conn)
                    
                    self.logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
                    self.logger.info(f"📊 Categories: {verification.get('categories_migrated', 0)}")
                    self.logger.info(f"📊 Subjects: {verification.get('subjects_migrated', 0)}")
                    self.logger.info(f"📊 Books: {verification.get('books_migrated', 0)}")
                    self.logger.info(f"🖼️ Books with thumbnails: {verification.get('books_with_thumbnails', 0)}")
                    
                    if verification.get('foreign_key_integrity', False):
                        self.logger.info("✅ Foreign key integrity verified")
                    else:
                        self.logger.warning("⚠️ Foreign key integrity issues detected")
                    
                    return True
                else:
                    self.logger.error("❌ Migration completed with errors")
                    return False
                    
            finally:
                source_conn.close()
                target_conn.close()
                
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            return False

def main():
    """Main migration function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Run migration
    migrator = LibraryDataMigrator()
    success = migrator.RunMigration()
    
    if success:
        logger.info("🎯 Migration completed successfully!")
        logger.info("📝 Check migration.log for detailed information")
        return 0
    else:
        logger.error("💥 Migration failed!")
        logger.error("📝 Check migration.log for error details")
        return 1

if __name__ == "__main__":
    exit(main())