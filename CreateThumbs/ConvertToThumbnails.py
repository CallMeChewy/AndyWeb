#!/usr/bin/env python3
"""
File: ConvertToThumbnails.py
Path: /home/herb/Desktop/BowersWorld-com/ConvertToThumbnails.py
Standard: AIDEV-PascalCase-1.7
Created: 2025-06-25
Author: Herb Bowers - Project Himalaya
Description: Convert PNG book covers to web-optimized thumbnails for Anderson's Library
"""

import os
import sys
from pathlib import Path
from PIL import Image
import time
from datetime import datetime

# Configuration
SOURCE_DIR = "/home/herb/Desktop/BowersWorld-com/Covers"
OUTPUT_DIR = "/home/herb/Desktop/BowersWorld-com/Thumbs"
THUMBNAIL_SIZE = (64, 85)  # Width x Height - optimized for book covers
QUALITY_SETTING = 85  # PNG optimization level
PROGRESS_INTERVAL = 25  # Show progress every N files

def CreateOutputDirectory(OutputPath):
    """
    Create the output directory if it doesn't exist
    
    Args:
        OutputPath: Path to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Path(OutputPath).mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {OutputPath}")
        return True
    except Exception as CreateError:
        print(f"❌ Failed to create output directory: {CreateError}")
        return False

def ValidateSourceDirectory(SourcePath):
    """
    Validate that source directory exists and contains PNG files
    
    Args:
        SourcePath: Path to validate
        
    Returns:
        tuple: (bool: valid, int: png_count)
    """
    if not os.path.exists(SourcePath):
        print(f"❌ Source directory not found: {SourcePath}")
        return False, 0
    
    PngFiles = list(Path(SourcePath).glob("*.png"))
    PngCount = len(PngFiles)
    
    if PngCount == 0:
        print(f"⚠️ No PNG files found in: {SourcePath}")
        return False, 0
    
    print(f"📁 Found {PngCount} PNG files in source directory")
    return True, PngCount

def ConvertSingleImage(SourcePath, OutputPath, ThumbnailSize):
    """
    Convert a single PNG file to thumbnail
    
    Args:
        SourcePath: Path to source PNG file
        OutputPath: Path for output thumbnail
        ThumbnailSize: Tuple of (width, height)
        
    Returns:
        tuple: (bool: success, int: original_size, int: thumbnail_size)
    """
    try:
        # Get original file size
        OriginalSize = os.path.getsize(SourcePath)
        
        # Open and process image
        with Image.open(SourcePath) as OriginalImage:
            # Convert RGBA to RGB if necessary (remove transparency)
            if OriginalImage.mode in ('RGBA', 'LA'):
                # Create white background
                RgbImage = Image.new('RGB', OriginalImage.size, (255, 255, 255))
                if OriginalImage.mode == 'RGBA':
                    RgbImage.paste(OriginalImage, mask=OriginalImage.split()[-1])
                else:
                    RgbImage.paste(OriginalImage, mask=OriginalImage.split()[-1])
                ProcessedImage = RgbImage
            else:
                ProcessedImage = OriginalImage.copy()
            
            # Create thumbnail while maintaining aspect ratio
            ProcessedImage.thumbnail(ThumbnailSize, Image.Resampling.LANCZOS)
            
            # Save optimized thumbnail
            ProcessedImage.save(OutputPath, 'PNG', optimize=True, quality=QUALITY_SETTING)
        
        # Get thumbnail file size
        ThumbnailSize = os.path.getsize(OutputPath)
        
        return True, OriginalSize, ThumbnailSize
        
    except Exception as ConversionError:
        print(f"❌ Error converting {SourcePath}: {ConversionError}")
        return False, 0, 0

def FormatFileSize(SizeInBytes):
    """
    Format file size in human-readable format
    
    Args:
        SizeInBytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for Unit in ['B', 'KB', 'MB', 'GB']:
        if SizeInBytes < 1024.0:
            return f"{SizeInBytes:.1f} {Unit}"
        SizeInBytes /= 1024.0
    return f"{SizeInBytes:.1f} TB"

def GenerateThumbnails():
    """
    Main function to convert all PNG files to thumbnails
    
    Returns:
        bool: True if successful, False otherwise
    """
    StartTime = time.time()
    
    print("🎨 Anderson's Library Thumbnail Generator")
    print("=" * 50)
    print(f"📂 Source: {SOURCE_DIR}")
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"📏 Size: {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]} pixels")
    print("=" * 50)
    
    # Validate source directory
    IsValid, TotalFiles = ValidateSourceDirectory(SOURCE_DIR)
    if not IsValid:
        return False
    
    # Create output directory
    if not CreateOutputDirectory(OUTPUT_DIR):
        return False
    
    # Process all PNG files
    ProcessedCount = 0
    ErrorCount = 0
    TotalOriginalSize = 0
    TotalThumbnailSize = 0
    SkippedCount = 0
    
    PngFiles = list(Path(SOURCE_DIR).glob("*.png"))
    
    print(f"🔄 Starting conversion of {len(PngFiles)} files...")
    print()
    
    for FileIndex, SourceFile in enumerate(PngFiles, 1):
        FileName = SourceFile.name
        OutputFile = Path(OUTPUT_DIR) / FileName
        
        # Check if thumbnail already exists
        if OutputFile.exists():
            print(f"⏭️ Skipping {FileName} (already exists)")
            SkippedCount += 1
            continue
        
        # Convert image
        Success, OriginalSize, ThumbnailSize = ConvertSingleImage(
            str(SourceFile), str(OutputFile), THUMBNAIL_SIZE
        )
        
        if Success:
            ProcessedCount += 1
            TotalOriginalSize += OriginalSize
            TotalThumbnailSize += ThumbnailSize
            
            # Calculate compression ratio
            CompressionRatio = (1 - (ThumbnailSize / OriginalSize)) * 100 if OriginalSize > 0 else 0
            
            # Show progress
            if ProcessedCount % PROGRESS_INTERVAL == 0 or FileIndex == len(PngFiles):
                print(f"📸 Processed {ProcessedCount}/{TotalFiles}: {FileName}")
                print(f"   📊 {FormatFileSize(OriginalSize)} → {FormatFileSize(ThumbnailSize)} ({CompressionRatio:.1f}% reduction)")
                
        else:
            ErrorCount += 1
    
    # Calculate final statistics
    EndTime = time.time()
    ProcessingTime = EndTime - StartTime
    
    print()
    print("=" * 50)
    print("✅ THUMBNAIL CONVERSION COMPLETE!")
    print("=" * 50)
    print(f"📊 Files processed: {ProcessedCount}")
    print(f"⏭️ Files skipped: {SkippedCount}")
    print(f"❌ Errors: {ErrorCount}")
    print(f"⏱️ Processing time: {ProcessingTime:.1f} seconds")
    
    if ProcessedCount > 0:
        # Size comparison
        TotalReduction = (1 - (TotalThumbnailSize / TotalOriginalSize)) * 100 if TotalOriginalSize > 0 else 0
        AverageOriginalSize = TotalOriginalSize / ProcessedCount
        AverageThumbnailSize = TotalThumbnailSize / ProcessedCount
        
        print()
        print("📈 SIZE ANALYSIS:")
        print(f"   Original total: {FormatFileSize(TotalOriginalSize)}")
        print(f"   Thumbnail total: {FormatFileSize(TotalThumbnailSize)}")
        print(f"   Total reduction: {TotalReduction:.1f}%")
        print(f"   Average original: {FormatFileSize(AverageOriginalSize)}")
        print(f"   Average thumbnail: {FormatFileSize(AverageThumbnailSize)}")
        
        # Performance metrics
        FilesPerSecond = ProcessedCount / ProcessingTime if ProcessingTime > 0 else 0
        print(f"   Processing speed: {FilesPerSecond:.1f} files/second")
    
    print()
    print(f"📁 Thumbnails saved to: {OUTPUT_DIR}")
    print("🎉 Ready for web deployment!")
    
    return ErrorCount == 0

def ShowUsageInformation():
    """Display usage information for the script"""
    print("📚 Anderson's Library Thumbnail Generator")
    print()
    print("USAGE:")
    print("  python ConvertToThumbnails.py")
    print()
    print("CONFIGURATION:")
    print(f"  Source Directory: {SOURCE_DIR}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    print(f"  Thumbnail Size: {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]} pixels")
    print()
    print("FEATURES:")
    print("  ✅ Maintains aspect ratio")
    print("  ✅ Optimizes file size")
    print("  ✅ Handles RGBA to RGB conversion")
    print("  ✅ Progress tracking")
    print("  ✅ Error handling")
    print("  ✅ Skips existing files")
    print()
    print("OUTPUT:")
    print("  • Creates optimized PNG thumbnails")
    print("  • Typically 95%+ smaller than originals")
    print("  • Perfect for web deployment")

def ValidateEnvironment():
    """
    Validate that required dependencies are available
    
    Returns:
        bool: True if environment is ready
    """
    try:
        import PIL
        print(f"✅ PIL/Pillow version: {PIL.__version__}")
        return True
    except ImportError:
        print("❌ PIL/Pillow not found!")
        print("   Install with: pip install Pillow")
        return False

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        ShowUsageInformation()
        sys.exit(0)
    
    # Validate environment
    if not ValidateEnvironment():
        sys.exit(1)
    
    # Run thumbnail generation
    try:
        Success = GenerateThumbnails()
        ExitCode = 0 if Success else 1
        
        if Success:
            print(f"\n🎉 Thumbnail generation completed successfully!")
            print(f"   Ready to integrate with Anderson's Library web interface")
        else:
            print(f"\n⚠️ Thumbnail generation completed with errors")
            print(f"   Check the output above for details")
        
        sys.exit(ExitCode)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Conversion interrupted by user")
        print("   Partial results may be available in the output directory")
        sys.exit(1)
    except Exception as UnexpectedError:
        print(f"\n❌ Unexpected error: {UnexpectedError}")
        print("   Please check file permissions and available disk space")
        sys.exit(1)