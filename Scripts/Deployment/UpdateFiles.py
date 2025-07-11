# File: CliveJob.py
# Path: Scripts/Deployment/UpdateFiles.py
# Standard: AIDEV-PascalCase-1.7
# Created: 2025-06-05
# Last Modified: 2025-06-26  17:45 PM
"""
Description: Clive's Job – Himalaya-standard update/move/archive utility.
Processes Updates folder, reads header for intended path, enforces PascalCase for all
created directories and files (unless ecosystem exception), archives old copies,
generates audit/status report, with full error handling, logging, and audit trail.

Fixed: Now ignores base directory from header paths and uses relative paths from current directory.
Fixed: Regex now handles both comment-style (# Path:) and docstring-style (Path:) headers.
Fixed: Better handling of absolute paths with leading slashes.
Fixed: Smarter base directory stripping - only strips known base directories, preserves nested paths.
Updated: .md files with Path: headers now go to specified location instead of Docs folder.
"""

import os
import re
import shutil
import logging
from datetime import datetime

# --- CONSTANTS ---
UPDATES_DIR = 'Updates'
ARCHIVE_DIR = 'Archive'
DOCS_BASE = 'Docs'
DOCS_UPDATES = os.path.join(DOCS_BASE, 'Updates')
DATE_FMT = "%Y-%m-%d"
TS_FMT = "%Y-%m-%d_%H-%M-%S"

logging.basicConfig(
    level=logging.INFO,
    format='[CliveJob] %(levelname)s: %(message)s'
)

def ToPascalCase(Segment: str) -> str:
    """
    Converts any file or directory segment to Himalaya PascalCase.
    Preserves extension (lowercase), applies PascalCase to base.
    Preserves already-good PascalCase filenames.
    """
    # Ecosystem exceptions
    if Segment in ('__init__.py', 'setup.py'):
        return Segment

    # Handle file extension (only split at LAST dot)
    if '.' in Segment and not Segment.startswith('.'):
        Base, Ext = Segment.rsplit('.', 1)
        Ext = Ext.lower()
    else:
        Base, Ext = Segment, ''

    # Check if Base is already in good PascalCase format
    if IsAlreadyPascalCase(Base):
        logging.info(f"Preserving already-good PascalCase: '{Base}'")
        return f"{Base}.{Ext}" if Ext else Base

    # Remove all non-alphanumeric separators, PascalCase the rest
    Words = re.split(r'[\s_\-]+', Base)
    Pascal = ''.join(Word.capitalize() for Word in Words if Word)

    return f"{Pascal}.{Ext}" if Ext else Pascal

def IsAlreadyPascalCase(Text: str) -> bool:
    """
    Check if text is already in acceptable PascalCase format.
    Returns True if the text should be preserved as-is.
    """
    # Must start with uppercase letter
    if not Text or not Text[0].isupper():
        return False
    
    # Must be all alphanumeric
    if not Text.isalnum():
        return False
    
    # Check for reasonable PascalCase pattern:
    # - Starts with uppercase
    # - Has at least one more uppercase letter (indicating word boundaries)
    # - No consecutive uppercase letters (avoid ALL_CAPS)
    uppercase_count = sum(1 for c in Text if c.isupper())
    
    # If it's all one word (like "Script"), allow it
    if len(Text) <= 8 and uppercase_count == 1:
        return True
    
    # For longer names, require multiple uppercase letters (PascalCase pattern)
    # but not too many (avoid ALLCAPS)
    if uppercase_count >= 2 and uppercase_count <= len(Text) // 2:
        # Check for consecutive uppercase (avoid "XMLHTTPRequest" style)
        consecutive_upper = any(Text[i].isupper() and Text[i+1].isupper() 
                               for i in range(len(Text)-1))
        if not consecutive_upper:
            return True
    
    return False

def PascalCasePath(Path: str) -> str:
    """
    Applies ToPascalCase to every segment of a path (directories and filename).
    """
    Path = Path.replace('\\', '/')
    Segments = Path.split('/')
    PascalSegments = [ToPascalCase(Segment) for Segment in Segments if Segment]
    return '/'.join(PascalSegments)

def ReadHeaderTargetPath(FilePath: str) -> str:
    """
    Extracts intended path from file header ('Path: ...'), removes base directory,
    and PascalCases the remaining relative path.
    
    Example: 'Path: ProjectHimalaya/CliveJob.py' becomes './CliveJob.py'
    Example: 'Path: /BowersWorld-com/SetupSearchSystem_v2.py' becomes './SetupSearchSystem_v2.py'
    """
    try:
        with open(FilePath, 'r', encoding='utf-8') as File:
            for _ in range(15):  # Check first 15 lines for header (docstrings can be longer)
                Line = File.readline()
                if not Line:  # End of file
                    break
                    
                # Match both comment-style and docstring-style paths
                # Handles: # Path: ... OR Path: ... (without #)
                Match = re.match(r'(?:#\s*)?Path:\s*(.+)', Line.strip())
                if Match:
                    FullPath = Match.group(1).strip()
                    logging.info(f"Found header path: '{FullPath}' in {FilePath}")
                    
                    # Remove base directory and use relative path
                    RelativePath = StripBaseDirectory(FullPath)
                    
                    if RelativePath:
                        FinalPath = PascalCasePath(RelativePath)
                        logging.info(f"Processed path: '{FullPath}' -> '{RelativePath}' -> '{FinalPath}'")
                        return FinalPath
                    else:
                        logging.warning(f"Empty path after stripping base directory from: {FullPath}")
                        return None
    except Exception as Error:
        logging.warning(f"Error reading header from {FilePath}: {Error}")
    return None

def StripBaseDirectory(Path: str) -> str:
    """
    Removes known base directories from a path, returning the relative path.
    Only strips if the path starts with a recognized base directory.
    
    Examples:
    - 'ProjectHimalaya/Source/Utilities/File.py' -> 'Source/Utilities/File.py'
    - 'Source/Utilities/File.py' -> 'Source/Utilities/File.py' (unchanged)
    - '/BowersWorld-com/SetupSearchSystem_v2.py' -> 'SetupSearchSystem_v2.py' 
    - 'SingleFile.py' -> 'SingleFile.py'
    """
    # Normalize path separators and remove leading/trailing slashes
    Path = Path.replace('\\', '/').strip('/')
    
    # Split into segments
    Segments = [Segment for Segment in Path.split('/') if Segment]
    
    if len(Segments) <= 1:
        # If only one segment (filename only), return as-is
        return Path
    
    # Known base directories that should be stripped
    # Add any other base directory names you use
    KNOWN_BASE_DIRS = {
        'ProjectHimalaya',
        'BowersWorld-com', 
        'Himalaya',
        'Project',
        # Add more as needed
    }
    
    FirstSegment = Segments[0]
    
    # Only strip if first segment is a known base directory
    if FirstSegment in KNOWN_BASE_DIRS:
        RelativeSegments = Segments[1:]
        RelativePath = '/'.join(RelativeSegments)
        logging.info(f"Stripped known base directory '{FirstSegment}': '{Path}' -> '{RelativePath}'")
        return RelativePath
    else:
        # Path doesn't start with known base dir, return as-is
        logging.info(f"No known base directory found, keeping path as-is: '{Path}'")
        return Path

def ArchiveExisting(TargetPath: str) -> str:
    """
    If file exists, moves it to Archive dir (PascalCase), adds timestamp.
    """
    if os.path.exists(TargetPath):
        ArchiveDir = os.path.join(ARCHIVE_DIR, os.path.dirname(TargetPath))
        os.makedirs(ArchiveDir, exist_ok=True)
        BaseName = os.path.basename(TargetPath)
        TimeStamp = datetime.now().strftime(TS_FMT)
        if '.' in BaseName and not BaseName.startswith('.'):
            Base, Ext = BaseName.rsplit('.', 1)
            Ext = Ext.lower()
        else:
            Base, Ext = BaseName, ''
        ArchiveName = f"{ToPascalCase(Base)}_{TimeStamp}{'.' + Ext if Ext else ''}"
        ArchivePath = os.path.join(ArchiveDir, ArchiveName)
        shutil.move(TargetPath, ArchivePath)
        logging.info(f"Archived old file: {TargetPath} → {ArchivePath}")
        return ArchivePath
    return None

def MoveOrCopyFile(SourcePath: str, DestPath: str) -> None:
    """
    Moves file, archiving old if needed, ensuring PascalCase on all dirs/files.
    """
    # Ensure destination directory exists
    DestDir = os.path.dirname(DestPath)
    if DestDir:  # Only create if there's a directory component
        os.makedirs(DestDir, exist_ok=True)
    
    # Archive existing file if it exists
    ArchiveExisting(DestPath)
    
    # Move the file
    shutil.move(SourcePath, DestPath)
    logging.info(f"Moved: {SourcePath} → {DestPath}")

def ProcessUpdates() -> None:
    """
    Processes all files in Updates folder with full Himalaya + PascalCase enforcement.
    Now correctly handles relative paths by stripping base directories from headers.
    Updated: .md files with Path: headers go to specified location instead of Docs folder.
    """
    Today = datetime.now().strftime(DATE_FMT)
    StatusEntries = []
    os.makedirs(DOCS_UPDATES, exist_ok=True)

    # Check if Updates directory exists
    if not os.path.exists(UPDATES_DIR):
        logging.warning(f"Updates directory '{UPDATES_DIR}' does not exist!")
        return

    for FileName in os.listdir(UPDATES_DIR):
        SourcePath = os.path.join(UPDATES_DIR, FileName)
        if not os.path.isfile(SourcePath):
            continue
            
        HeaderPath = ReadHeaderTargetPath(SourcePath)
        FileExt = os.path.splitext(FileName)[1].lower()
        Status = {'File': FileName, 'Result': '', 'Detail': ''}
        
        try:
            # Check if it's a .md file
            if FileExt == '.md':
                if HeaderPath:
                    # .md file with Path: header - use specified location
                    DestPath = HeaderPath
                    MoveOrCopyFile(SourcePath, DestPath)
                    Status['Result'] = 'Moved by header path (.md with Path: header)'
                    Status['Detail'] = DestPath
                else:
                    # .md file without Path: header - move to Docs folder
                    DocsDayDir = os.path.join(DOCS_BASE, Today)
                    DestPath = os.path.join(DocsDayDir, FileName)
                    MoveOrCopyFile(SourcePath, DestPath)
                    Status['Result'] = 'Moved to Docs (no Path: header)'
                    Status['Detail'] = DestPath
                    
            # .txt files: always move to Docs/YYYY-MM-DD/ (original name for doc provenance)
            elif FileExt == '.txt':
                DocsDayDir = os.path.join(DOCS_BASE, Today)
                DestPath = os.path.join(DocsDayDir, FileName)
                MoveOrCopyFile(SourcePath, DestPath)
                Status['Result'] = 'Moved to Docs (dated, original filename)'
                Status['Detail'] = DestPath
                
            elif HeaderPath:
                # Other file types with header path
                DestPath = HeaderPath
                MoveOrCopyFile(SourcePath, DestPath)
                Status['Result'] = 'Moved by header path (base directory stripped, PascalCase applied)'
                Status['Detail'] = DestPath
                
            else:
                Status['Result'] = 'Skipped (no header path, not doc)'
                Status['Detail'] = f"Kept in: {SourcePath}"
                logging.warning(f"Skipped: {FileName} (no header path and not .md/.txt)")
                
        except Exception as Error:
            Status['Result'] = 'Error'
            Status['Detail'] = str(Error)
            logging.error(f"Failed processing {FileName}: {Error}")
            
        StatusEntries.append(Status)

    # Write status report
    ReportTimeStamp = datetime.now().strftime(TS_FMT)
    ReportPath = os.path.join(DOCS_UPDATES, f'Updates_{ReportTimeStamp}.md')
    
    with open(ReportPath, 'w', encoding='utf-8') as Report:
        Report.write(f"# Updates Status Report — {ReportTimeStamp}\n\n")
        Report.write(f"**Total files processed:** {len(StatusEntries)}\n\n")
        
        # Summary counts
        Moved = sum(1 for entry in StatusEntries if 'Moved' in entry['Result'])
        Skipped = sum(1 for entry in StatusEntries if 'Skipped' in entry['Result'])
        Errors = sum(1 for entry in StatusEntries if 'Error' in entry['Result'])
        
        Report.write(f"**Summary:**\n")
        Report.write(f"- ✅ Moved: {Moved}\n")
        Report.write(f"- ⏭️ Skipped: {Skipped}\n")
        Report.write(f"- ❌ Errors: {Errors}\n\n")
        Report.write(f"**Details:**\n\n")
        
        for Entry in StatusEntries:
            # Add emoji based on result
            if 'Moved' in Entry['Result']:
                Emoji = '✅'
            elif 'Skipped' in Entry['Result']:
                Emoji = '⏭️'
            elif 'Error' in Entry['Result']:
                Emoji = '❌'
            else:
                Emoji = '❓'
                
            Report.write(f"- {Emoji} **{Entry['File']}**: {Entry['Result']}  \n")
            Report.write(f"    `{Entry['Detail']}`\n\n")
            
    print(f"\n[CliveJob] Status report written: {ReportPath}")
    print(f"[CliveJob] Summary - Moved: {Moved}, Skipped: {Skipped}, Errors: {Errors}")

if __name__ == "__main__":
    print("[CliveJob] Himalaya file processor starting...")
    print("[CliveJob] Fixed version - now strips base directories from header paths")
    print("[CliveJob] Updated: .md files with Path: headers go to specified location")
    ProcessUpdates()
    print("[CliveJob] All done. Review status report for details.")