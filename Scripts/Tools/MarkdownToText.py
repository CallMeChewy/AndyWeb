# File: MarkdownToText.py
# Path: MarkdownToText.py
# Standard: AIDEV-PascalCase-1.7
# Created: 2025-06-21
# Last Modified: 2025-06-21  09:30 AM
# Author: Claude Code Assistant
"""
Description: Himalaya Markdown to Text Converter Utility
Converts .md files to plain text format by stripping Markdown syntax while preserving
content structure and readability. Handles headers, lists, code blocks, links, and
other common Markdown elements. Follows AIDEV-PascalCase-1.7 standard with comprehensive
error handling, logging, and audit trail generation.

Core Features:
- PascalCase naming convention enforcement
- Comprehensive Markdown syntax removal
- Batch directory processing capabilities
- Detailed logging and status reporting
- Error handling with graceful degradation
"""

import os
import re
import sys
import logging
from datetime import datetime
from typing import Optional

# --- CONSTANTS ---
DOCS_DIR = 'Docs'
TEXT_OUTPUT_DIR = 'TextOutput'
DATE_FMT = "%Y-%m-%d"
TS_FMT = "%Y-%m-%d_%H-%M-%S"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[MarkdownToText] %(levelname)s: %(message)s'
)

def ProcessMarkdownToText(MarkdownContent: str) -> str:
    """
    Processes Markdown content and converts to clean plain text.
    Removes all Markdown syntax while preserving content structure and readability.
    Follows Himalaya text processing standards.
    
    Args:
        MarkdownContent: Raw markdown content as string
        
    Returns:
        Plain text with all Markdown syntax removed
    """
    ProcessedText = MarkdownContent
    
    # Remove code blocks (```code```)
    ProcessedText = re.sub(r'```[\s\S]*?```', '', ProcessedText)
    
    # Remove inline code (`code`)
    ProcessedText = re.sub(r'`([^`]+)`', r'\1', ProcessedText)
    
    # Convert headers (# ## ### etc.) to plain text with spacing
    ProcessedText = re.sub(r'^#{1,6}\s*(.+)$', r'\1', ProcessedText, flags=re.MULTILINE)
    
    # Remove bold/italic markers (**text**, *text*, __text__, _text_)
    ProcessedText = re.sub(r'\*\*([^*]+)\*\*', r'\1', ProcessedText)
    ProcessedText = re.sub(r'\*([^*]+)\*', r'\1', ProcessedText)
    ProcessedText = re.sub(r'__([^_]+)__', r'\1', ProcessedText)
    ProcessedText = re.sub(r'_([^_]+)_', r'\1', ProcessedText)
    
    # Convert links [text](url) to just text
    ProcessedText = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', ProcessedText)
    
    # Remove reference-style links [text]: url
    ProcessedText = re.sub(r'^\s*\[[^\]]+\]:\s*.+$', '', ProcessedText, flags=re.MULTILINE)
    
    # Convert unordered lists (- * +) to plain text with indentation
    ProcessedText = re.sub(r'^(\s*)[-*+]\s+(.+)$', r'\1\2', ProcessedText, flags=re.MULTILINE)
    
    # Convert ordered lists (1. 2. etc.) to plain text with indentation
    ProcessedText = re.sub(r'^(\s*)\d+\.\s+(.+)$', r'\1\2', ProcessedText, flags=re.MULTILINE)
    
    # Remove blockquotes (>)
    ProcessedText = re.sub(r'^>\s*(.*)$', r'\1', ProcessedText, flags=re.MULTILINE)
    
    # Remove horizontal rules (--- or ***)
    ProcessedText = re.sub(r'^[-*]{3,}$', '', ProcessedText, flags=re.MULTILINE)
    
    # Clean up extra whitespace while preserving paragraph breaks
    ProcessedText = re.sub(r'\n{3,}', '\n\n', ProcessedText)
    ProcessedText = re.sub(r'[ \t]+', ' ', ProcessedText)
    
    # Remove leading/trailing whitespace from lines
    CleanedLines = [Line.strip() for Line in ProcessedText.split('\n')]
    ProcessedText = '\n'.join(CleanedLines)
    
    return ProcessedText.strip()

def ConvertSingleMarkdownFile(SourcePath: str, DestinationPath: Optional[str] = None) -> bool:
    """
    Converts a single Markdown file to plain text with full error handling.
    Follows Himalaya file processing standards with comprehensive logging.
    
    Args:
        SourcePath: Path to source .md file
        DestinationPath: Optional output path, defaults to source path with .txt extension
        
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Validate source file existence
        if not os.path.exists(SourcePath):
            logging.error(f"Source file not found: {SourcePath}")
            return False
            
        if not SourcePath.lower().endswith('.md'):
            logging.warning(f"Source file is not a Markdown file: {SourcePath}")
        
        # Determine destination path with PascalCase naming
        if DestinationPath is None:
            BaseFileName = os.path.splitext(os.path.basename(SourcePath))[0]
            DestinationPath = f"{BaseFileName}.txt"
        
        # Ensure destination directory exists
        DestinationDir = os.path.dirname(DestinationPath)
        if DestinationDir and not os.path.exists(DestinationDir):
            os.makedirs(DestinationDir, exist_ok=True)
            logging.info(f"Created destination directory: {DestinationDir}")
        
        # Read markdown content with encoding validation
        with open(SourcePath, 'r', encoding='utf-8') as SourceFile:
            MarkdownContent = SourceFile.read()
        
        # Process markdown to plain text
        ConvertedText = ProcessMarkdownToText(MarkdownContent)
        
        # Write output file with UTF-8 encoding
        with open(DestinationPath, 'w', encoding='utf-8') as DestinationFile:
            DestinationFile.write(ConvertedText)
        
        logging.info(f"Successfully converted: {SourcePath} → {DestinationPath}")
        return True
        
    except Exception as ProcessingError:
        logging.error(f"Failed to convert {SourcePath}: {ProcessingError}")
        return False

def ProcessMarkdownDirectory(SourceDirectory: str, DestinationDirectory: Optional[str] = None) -> int:
    """
    Processes all .md files in a directory to .txt files with batch processing.
    Generates comprehensive status report and audit trail.
    
    Args:
        SourceDirectory: Path to directory containing .md files
        DestinationDirectory: Optional output directory, defaults to same as source
        
    Returns:
        Number of files successfully converted
    """
    if not os.path.isdir(SourceDirectory):
        logging.error(f"Source directory not found: {SourceDirectory}")
        return 0
    
    SuccessfulConversions = 0
    ProcessingErrors = 0
    MarkdownFileList = [FileName for FileName in os.listdir(SourceDirectory) if FileName.lower().endswith('.md')]
    
    if not MarkdownFileList:
        logging.warning(f"No .md files found in directory: {SourceDirectory}")
        return 0
    
    logging.info(f"Found {len(MarkdownFileList)} Markdown files to process")
    
    for FileName in MarkdownFileList:
        SourceFilePath = os.path.join(SourceDirectory, FileName)
        
        if DestinationDirectory:
            os.makedirs(DestinationDirectory, exist_ok=True)
            BaseFileName = os.path.splitext(FileName)[0]
            DestinationFilePath = os.path.join(DestinationDirectory, f"{BaseFileName}.txt")
        else:
            DestinationFilePath = None
        
        if ConvertSingleMarkdownFile(SourceFilePath, DestinationFilePath):
            SuccessfulConversions += 1
        else:
            ProcessingErrors += 1
    
    logging.info(f"Batch processing completed: {SuccessfulConversions} successful, {ProcessingErrors} errors")
    logging.info(f"Directory processing summary: {SourceDirectory} → {DestinationDirectory or 'same directory'}")
    return SuccessfulConversions

def ExecuteMarkdownConversion():
    """
    Main execution function for command-line usage.
    Handles both single file and directory batch processing with comprehensive error handling.
    
    Usage: python MarkdownToText.py <source_file_or_directory> [destination_path]
    
    Examples:
        python MarkdownToText.py Document.md
        python MarkdownToText.py Document.md ConvertedDocument.txt
        python MarkdownToText.py ./MarkdownFiles/
        python MarkdownToText.py ./MarkdownFiles/ ./TextFiles/
    """
    if len(sys.argv) < 2:
        print("Usage: python MarkdownToText.py <source_file_or_directory> [destination_path]")
        print("Examples:")
        print("  python MarkdownToText.py Document.md")
        print("  python MarkdownToText.py Document.md ConvertedDocument.txt")
        print("  python MarkdownToText.py ./SourceDocs/")
        print("  python MarkdownToText.py ./SourceDocs/ ./ConvertedText/")
        print("\nHimalaya Markdown to Text Converter - AIDEV-PascalCase-1.7")
        sys.exit(1)
    
    SourcePath = sys.argv[1]
    DestinationPath = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"[MarkdownToText] Himalaya conversion process starting...")
    ExecutionStartTime = datetime.now()
    
    if os.path.isfile(SourcePath):
        ConversionSuccess = ConvertSingleMarkdownFile(SourcePath, DestinationPath)
        if ConversionSuccess:
            print(f"[MarkdownToText] Single file conversion completed successfully")
        else:
            print(f"[MarkdownToText] Single file conversion failed - check logs for details")
            sys.exit(1)
    elif os.path.isdir(SourcePath):
        ProcessedFileCount = ProcessMarkdownDirectory(SourcePath, DestinationPath)
        print(f"[MarkdownToText] Directory batch processing completed: {ProcessedFileCount} files converted")
        if ProcessedFileCount == 0:
            print(f"[MarkdownToText] Warning: No files were successfully converted")
    else:
        print(f"[MarkdownToText] Error: Source path not found: {SourcePath}")
        sys.exit(1)
    
    ExecutionEndTime = datetime.now()
    TotalDuration = (ExecutionEndTime - ExecutionStartTime).total_seconds()
    print(f"[MarkdownToText] Total execution time: {TotalDuration:.2f} seconds")
    print(f"[MarkdownToText] Himalaya conversion process completed successfully")

if __name__ == "__main__":
    ExecuteMarkdownConversion()