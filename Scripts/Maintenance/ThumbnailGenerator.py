# File: ThumbnailGenerator.py
# Path: Scripts/Maintenance/ThumbnailGenerator.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-05
# Last Modified: 2025-07-05  08:30PM
"""
Description: Thumbnail Generator for Anderson's Library
Generates placeholder thumbnails for books that don't have existing images.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import sqlite3

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from Source.Core.DatabaseManager import DatabaseManager


class ThumbnailGenerator:
    """
    Generates placeholder thumbnails for books without existing images.
    """
    
    def __init__(self, DatabasePath: str = "Assets/my_library.db", 
                 ThumbnailDir: str = "Data/Thumbs"):
        self.DatabasePath = DatabasePath
        self.ThumbnailDir = ThumbnailDir
        self.Logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure thumbnail directory exists
        Path(self.ThumbnailDir).mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.DatabaseManager = DatabaseManager(DatabasePath)
    
    def GenerateAllThumbnails(self):
        """Generate thumbnails for all books that don't have them."""
        try:
            # Get all books from database
            Books = self.DatabaseManager.GetBooks()
            
            GeneratedCount = 0
            SkippedCount = 0
            
            for Book in Books:
                Title = Book.get('Title', '')
                if not Title:
                    continue
                
                ThumbnailPath = os.path.join(self.ThumbnailDir, f"{Title}.png")
                
                # Skip if thumbnail already exists
                if os.path.exists(ThumbnailPath):
                    SkippedCount += 1
                    continue
                
                # Generate thumbnail
                if self.GenerateThumbnail(Book, ThumbnailPath):
                    GeneratedCount += 1
                    self.Logger.info(f"Generated thumbnail: {Title}")
                else:
                    self.Logger.warning(f"Failed to generate thumbnail: {Title}")
            
            self.Logger.info(f"Thumbnail generation complete. Generated: {GeneratedCount}, Skipped: {SkippedCount}")
            print(f"✅ Generated {GeneratedCount} thumbnails, skipped {SkippedCount} existing")
            
        except Exception as Error:
            self.Logger.error(f"Failed to generate thumbnails: {Error}")
            print(f"❌ Error generating thumbnails: {Error}")
    
    def GenerateThumbnail(self, BookData: Dict[str, Any], OutputPath: str) -> bool:
        """
        Generate a single thumbnail for a book.
        
        Args:
            BookData: Dictionary containing book information
            OutputPath: Path where thumbnail should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Thumbnail dimensions
            Width, Height = 180, 240
            
            # Create image
            Image_obj = Image.new('RGB', (Width, Height), color='white')
            Draw = ImageDraw.Draw(Image_obj)
            
            # Get book information
            Title = BookData.get('Title', 'Unknown Title')
            Author = BookData.get('Author', 'Unknown Author')
            Category = BookData.get('Category', 'General')
            
            # Choose colors based on category
            Colors = self.GetCategoryColors(Category)
            
            # Draw background gradient effect
            self.DrawBackground(Draw, Width, Height, Colors)
            
            # Draw border
            Draw.rectangle([2, 2, Width-3, Height-3], outline=Colors['border'], width=2)
            
            # Draw book icon
            self.DrawBookIcon(Draw, Width, Height, Colors)
            
            # Draw text
            self.DrawBookText(Draw, Width, Height, Title, Author, Colors)
            
            # Save image
            Image_obj.save(OutputPath, 'PNG', quality=90)
            return True
            
        except Exception as Error:
            self.Logger.error(f"Failed to generate thumbnail for {BookData.get('Title', 'Unknown')}: {Error}")
            return False
    
    def GetCategoryColors(self, Category: str) -> Dict[str, str]:
        """
        Get color scheme based on book category.
        
        Args:
            Category: Book category
            
        Returns:
            Dictionary of colors for the category
        """
        CategoryColors = {
            'Programming': {
                'primary': '#3498db',
                'secondary': '#2980b9', 
                'accent': '#85C1E9',
                'text': '#ffffff',
                'border': '#2c3e50'
            },
            'Science': {
                'primary': '#27ae60',
                'secondary': '#229954',
                'accent': '#A9DFBF',
                'text': '#ffffff',
                'border': '#1e8449'
            },
            'Business': {
                'primary': '#e74c3c',
                'secondary': '#c0392b',
                'accent': '#F1948A',
                'text': '#ffffff',
                'border': '#922b21'
            },
            'Mathematics': {
                'primary': '#9b59b6',
                'secondary': '#8e44ad',
                'accent': '#D2B4DE',
                'text': '#ffffff',
                'border': '#6c3483'
            },
            'History': {
                'primary': '#d35400',
                'secondary': '#ba4a00',
                'accent': '#F0B27A',
                'text': '#ffffff',
                'border': '#a04000'
            }
        }
        
        # Default color scheme
        DefaultColors = {
            'primary': '#34495e',
            'secondary': '#2c3e50',
            'accent': '#BDC3C7',
            'text': '#ffffff',
            'border': '#1b2631'
        }
        
        # Return category colors or default
        return CategoryColors.get(Category, DefaultColors)
    
    def DrawBackground(self, Draw: ImageDraw.ImageDraw, Width: int, Height: int, Colors: Dict[str, str]):
        """Draw gradient background."""
        # Simple gradient effect with rectangles
        for i in range(Height):
            # Calculate color interpolation
            ratio = i / Height
            # Draw horizontal line with gradually changing color
            if i % 2 == 0:  # Every other line for subtle effect
                Draw.line([(0, i), (Width, i)], fill=Colors['primary'])
            else:
                Draw.line([(0, i), (Width, i)], fill=Colors['secondary'])
    
    def DrawBookIcon(self, Draw: ImageDraw.ImageDraw, Width: int, Height: int, Colors: Dict[str, str]):
        """Draw a simple book icon."""
        # Book spine
        BookWidth = 60
        BookHeight = 80
        BookX = (Width - BookWidth) // 2
        BookY = 40
        
        # Draw book rectangle
        Draw.rectangle([BookX, BookY, BookX + BookWidth, BookY + BookHeight], 
                      fill=Colors['accent'], outline=Colors['border'], width=2)
        
        # Draw book "pages" lines
        for i in range(5):
            LineY = BookY + 15 + (i * 12)
            Draw.line([BookX + 10, LineY, BookX + BookWidth - 10, LineY], 
                     fill=Colors['border'], width=1)
    
    def DrawBookText(self, Draw: ImageDraw.ImageDraw, Width: int, Height: int, 
                    Title: str, Author: str, Colors: Dict[str, str]):
        """Draw book title and author text."""
        try:
            # Try to load a system font
            try:
                TitleFont = ImageFont.truetype("arial.ttf", 12)
                AuthorFont = ImageFont.truetype("arial.ttf", 10)
            except:
                # Fallback to default font
                TitleFont = ImageFont.load_default()
                AuthorFont = ImageFont.load_default()
            
            # Truncate title if too long
            if len(Title) > 25:
                Title = Title[:22] + "..."
            
            # Truncate author if too long
            if len(Author) > 20:
                Author = Author[:17] + "..."
            
            # Draw title
            TitleBbox = Draw.textbbox((0, 0), Title, font=TitleFont)
            TitleWidth = TitleBbox[2] - TitleBbox[0]
            TitleX = (Width - TitleWidth) // 2
            Draw.text((TitleX, Height - 80), Title, fill=Colors['text'], font=TitleFont)
            
            # Draw author
            AuthorBbox = Draw.textbbox((0, 0), Author, font=AuthorFont)
            AuthorWidth = AuthorBbox[2] - AuthorBbox[0]
            AuthorX = (Width - AuthorWidth) // 2
            Draw.text((AuthorX, Height - 60), Author, fill=Colors['text'], font=AuthorFont)
            
            # Draw category
            Draw.text((10, 10), Category, fill=Colors['text'], font=AuthorFont)
            
        except Exception as Error:
            self.Logger.warning(f"Could not draw text: {Error}")
    
    def CleanupOldThumbnails(self):
        """Remove thumbnails for books that no longer exist in database."""
        try:
            # Get all books from database
            Books = self.DatabaseManager.GetBooks()
            BookTitles = {Book.get('Title', '') for Book in Books if Book.get('Title')}
            
            # Get all thumbnail files
            ThumbnailFiles = list(Path(self.ThumbnailDir).glob("*.png"))
            
            RemovedCount = 0
            for ThumbnailFile in ThumbnailFiles:
                # Extract title from filename (remove .png extension)
                Title = ThumbnailFile.stem
                
                if Title not in BookTitles:
                    ThumbnailFile.unlink()  # Delete file
                    RemovedCount += 1
                    self.Logger.info(f"Removed orphaned thumbnail: {Title}")
            
            self.Logger.info(f"Cleanup complete. Removed {RemovedCount} orphaned thumbnails")
            print(f"🧹 Cleaned up {RemovedCount} orphaned thumbnails")
            
        except Exception as Error:
            self.Logger.error(f"Failed to cleanup thumbnails: {Error}")
            print(f"❌ Error during cleanup: {Error}")


def main():
    """Main function to run thumbnail generation."""
    print("🏔️ Anderson's Library - Thumbnail Generator")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create thumbnail generator
        Generator = ThumbnailGenerator()
        
        print("📚 Generating thumbnails for all books...")
        Generator.GenerateAllThumbnails()
        
        print("🧹 Cleaning up orphaned thumbnails...")
        Generator.CleanupOldThumbnails()
        
        print("\n✅ Thumbnail generation complete!")
        print("📁 Thumbnails saved to: Data/Thumbs/")
        
    except Exception as Error:
        print(f"❌ Critical error: {Error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())