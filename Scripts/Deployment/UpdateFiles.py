# File: UpdateFiles.py
# Path: Scripts/Deployment/UpdateFiles.py
# Standard: AIDEV-PascalCase-1.9
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:42PM
"""
Description: Enhanced web-aware file management system for Project Himalaya
Handles automated file placement with Design Standard v1.9 compliance including
web framework exceptions, PascalCase conversion, and proper path handling.
Supports modern web development conventions alongside traditional PascalCase rules.
"""

import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
Logger = logging.getLogger(__name__)

class WebAwareFileManager:
    """Enhanced file manager with web framework awareness and v1.9 compliance."""
    
    def __init__(self, ProjectRoot: str = "."):
        """Initialize file manager with project root and web conventions."""
        self.ProjectRoot = Path(ProjectRoot).resolve()
        self.UpdatesFolder = self.ProjectRoot / "Updates"
        self.ArchiveFolder = self.ProjectRoot / "Archive"
        self.DocsFolder = self.ProjectRoot / "Docs"
        
        # Web framework exceptions - CRITICAL for compatibility
        self.WEB_EXCEPTIONS = {
            # Directories that MUST stay lowercase
            'node_modules': 'node_modules',
            'public': 'public',
            'src': 'src',
            'assets': 'assets',
            'components': 'components',
            'static': 'static',
            'dist': 'dist',
            'build': 'build',
            
            # Files that MUST stay lowercase
            'index.html': 'index.html',
            'package.json': 'package.json',
            'package-lock.json': 'package-lock.json',
            'tsconfig.json': 'tsconfig.json',
            'webpack.config.js': 'webpack.config.js',
            'babel.config.js': 'babel.config.js',
            'vite.config.js': 'vite.config.js',
            '.gitignore': '.gitignore',
            'robots.txt': 'robots.txt',
            'sitemap.xml': 'sitemap.xml',
            'favicon.ico': 'favicon.ico',
            
            # API special cases - context sensitive
            'API': 'API',          # Source/API/ (Python modules)
            'api': 'api',          # WebPages/api/ or /api/ (web routes)
            
            # Common web utilities (lowercase convention)
            'utils.js': 'utils.js',
            'utils.ts': 'utils.ts',
            'constants.js': 'constants.js',
            'config.js': 'config.js',
            'main.js': 'main.js',
            'main.css': 'main.css',
            'style.css': 'style.css',
            'styles.css': 'styles.css',
            'app.js': 'app.js',
            'app.css': 'app.css'
        }
        
        # Web-specific file extensions that follow web conventions
        self.WEB_EXTENSIONS = {
            '.html', '.css', '.js', '.ts', '.json', '.xml', '.txt',
            '.scss', '.sass', '.less', '.vue', '.jsx', '.tsx'
        }
        
        # Initialize folders
        self._EnsureFoldersExist()
        
    def _EnsureFoldersExist(self) -> None:
        """Ensure required folders exist."""
        for Folder in [self.UpdatesFolder, self.ArchiveFolder]:
            Folder.mkdir(exist_ok=True)
            
    def _IsWebFile(self, FilePath: Path) -> bool:
        """Determine if file should follow web conventions."""
        # Check if file is in web-related directories
        WebPaths = ['WebPages', 'web', 'frontend', 'client', 'public', 'src', 'assets']
        PathParts = FilePath.parts
        
        for Part in PathParts:
            if Part.lower() in [p.lower() for p in WebPaths]:
                return True
                
        # Check file extension
        if FilePath.suffix.lower() in self.WEB_EXTENSIONS:
            return True
            
        return False
        
    def _ApplyWebExceptions(self, Name: str, IsDirectory: bool = False, 
                          FilePath: Optional[Path] = None) -> str:
        """Apply web framework exceptions to naming."""
        
        # Direct exception match
        if Name in self.WEB_EXCEPTIONS:
            Logger.debug(f"Web exception applied: {Name} -> {self.WEB_EXCEPTIONS[Name]}")
            return self.WEB_EXCEPTIONS[Name]
            
        # Context-sensitive API handling
        if Name.upper() == 'API':
            if FilePath and self._IsWebFile(FilePath):
                # In web context, use lowercase
                if 'WebPages' in str(FilePath) or 'frontend' in str(FilePath):
                    Logger.debug(f"Web API context: {Name} -> api")
                    return 'api'
            # In Python context, use uppercase
            Logger.debug(f"Python API context: {Name} -> API")
            return 'API'
            
        # Web file extensions should often stay lowercase
        if FilePath and FilePath.suffix.lower() in self.WEB_EXTENSIONS:
            if self._IsWebFile(FilePath):
                # Common web patterns that should stay lowercase
                WebPatterns = [
                    'index', 'main', 'app', 'utils', 'config', 'constants',
                    'style', 'styles', 'component', 'service'
                ]
                
                NameLower = Name.lower()
                for Pattern in WebPatterns:
                    if Pattern in NameLower:
                        Logger.debug(f"Web pattern match: {Name} -> {Name.lower()}")
                        return Name.lower()
                        
        return None  # No exception applied
        
    def _ConvertToPascalCase(self, Name: str, IsDirectory: bool = False, 
                           FilePath: Optional[Path] = None) -> str:
        """Convert name to PascalCase with web framework awareness."""
        
        # First check for web exceptions
        WebException = self._ApplyWebExceptions(Name, IsDirectory, FilePath)
        if WebException is not None:
            return WebException
            
        # Apply standard PascalCase conversion
        # Remove file extension for processing
        NamePart = Name
        Extension = ""
        
        if not IsDirectory and '.' in Name:
            NamePart, Extension = Name.rsplit('.', 1)
            Extension = '.' + Extension
            
        # Convert underscores and hyphens to spaces, then to PascalCase
        Words = re.split(r'[_\-\s]+', NamePart)
        PascalName = ''.join(Word.capitalize() for Word in Words if Word)
        
        Result = PascalName + Extension
        Logger.debug(f"PascalCase conversion: {Name} -> {Result}")
        return Result
        
    def _ExtractHeaderPath(self, FilePath: Path) -> Optional[str]:
        """Extract Path: header from file."""
        try:
            with open(FilePath, 'r', encoding='utf-8', errors='ignore') as File:
                for LineNum, Line in enumerate(File, 1):
                    if LineNum > 20:  # Only check first 20 lines
                        break
                        
                    # Match various header formats
                    Patterns = [
                        r'^#\s*Path:\s*(.+)$',          # Python/Shell
                        r'^//\s*Path:\s*(.+)$',         # JavaScript
                        r'^<!--\s*.*Path:\s*(.+).*-->$', # HTML
                        r'^/\*\s*.*Path:\s*(.+).*\*/$', # CSS
                        r'^\s*"_path":\s*"(.+)"',       # JSON
                    ]
                    
                    for Pattern in Patterns:
                        Match = re.search(Pattern, Line.strip(), re.IGNORECASE)
                        if Match:
                            Path = Match.group(1).strip()
                            Logger.debug(f"Found header path: {Path}")
                            return Path
                            
        except Exception as Error:
            Logger.warning(f"Could not read header from {FilePath}: {Error}")
            
        return None
        
    def _StripBaseDirectories(self, Path: str) -> str:
        """Remove known base directories from path."""
        BaseDirs = ['ProjectHimalaya', 'BowersWorld-com', 'AndyWeb', 'Project']
        
        for BaseDir in BaseDirs:
            if Path.startswith(BaseDir + '/'):
                Path = Path[len(BaseDir) + 1:]
                Logger.debug(f"Stripped base directory: {BaseDir}")
                
        return Path
        
    def _ConvertPathToPascalCase(self, Path: str) -> str:
        """Convert entire path to PascalCase with web awareness."""
        PathParts = Path.split('/')
        ConvertedParts = []
        
        for i, Part in enumerate(PathParts):
            if not Part:
                continue
                
            IsDirectory = i < len(PathParts) - 1
            
            # Create a temporary path for context
            CurrentPath = Path('/'.join(PathParts[:i+1]))
            TempPath = Path(CurrentPath)
            
            ConvertedPart = self._ConvertToPascalCase(Part, IsDirectory, TempPath)
            ConvertedParts.append(ConvertedPart)
            
        Result = '/'.join(ConvertedParts)
        Logger.debug(f"Path conversion: {Path} -> {Result}")
        return Result
        
    def _ArchiveExistingFile(self, TargetPath: Path) -> bool:
        """Archive existing file with timestamp."""
        if not TargetPath.exists():
            return True
            
        try:
            Timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ArchiveName = f"{TargetPath.stem}_{Timestamp}{TargetPath.suffix}"
            ArchivePath = self.ArchiveFolder / ArchiveName
            
            # Ensure archive directory exists
            self.ArchiveFolder.mkdir(exist_ok=True)
            
            shutil.move(str(TargetPath), str(ArchivePath))
            Logger.info(f"Archived: {TargetPath.name} -> {ArchivePath.name}")
            return True
            
        except Exception as Error:
            Logger.error(f"Failed to archive {TargetPath}: {Error}")
            return False
            
    def _ValidateTimestamp(self, FilePath: Path) -> bool:
        """Validate that file has proper timestamp (v1.9 compliance)."""
        try:
            with open(FilePath, 'r', encoding='utf-8', errors='ignore') as File:
                Content = File.read(500)  # Check first 500 chars
                
            # Look for Last Modified timestamp
            Pattern = r'Last Modified:\s*\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[AP]M'
            if re.search(Pattern, Content):
                Logger.debug(f"Valid timestamp found in {FilePath.name}")
                return True
            else:
                Logger.warning(f"Missing or invalid timestamp in {FilePath.name}")
                return False
                
        except Exception as Error:
            Logger.warning(f"Could not validate timestamp in {FilePath}: {Error}")
            return False
            
    def ProcessFile(self, SourceFile: Path) -> Dict[str, str]:
        """Process a single file according to Design Standard v1.9."""
        Result = {
            'status': 'skipped',
            'source': str(SourceFile),
            'target': '',
            'message': 'Unknown'
        }
        
        try:
            # Validate timestamp (v1.9 requirement)
            if not self._ValidateTimestamp(SourceFile):
                Result['status'] = 'warning'
                Result['message'] = 'Invalid or missing timestamp'
                
            # Extract header path
            HeaderPath = self._ExtractHeaderPath(SourceFile)
            
            if HeaderPath:
                # Process header path
                CleanPath = self._StripBaseDirectories(HeaderPath)
                ConvertedPath = self._ConvertPathToPascalCase(CleanPath)
                TargetPath = self.ProjectRoot / ConvertedPath
                
                # Ensure target directory exists
                TargetPath.parent.mkdir(parents=True, exist_ok=True)
                
                # Archive existing file
                if not self._ArchiveExistingFile(TargetPath):
                    Result['status'] = 'error'
                    Result['message'] = 'Failed to archive existing file'
                    return Result
                    
                # Move file
                shutil.move(str(SourceFile), str(TargetPath))
                
                Result['status'] = 'moved'
                Result['target'] = str(TargetPath)
                Result['message'] = f'Moved by header path (v1.9 compliant)'
                Logger.info(f"✅ {SourceFile.name} -> {ConvertedPath}")
                
            elif SourceFile.suffix.lower() in ['.md', '.txt', '.pdf']:
                # Documentation files go to dated docs folder
                Today = datetime.now().strftime("%Y-%m-%d")
                DocsDateFolder = self.DocsFolder / Today
                DocsDateFolder.mkdir(parents=True, exist_ok=True)
                
                TargetPath = DocsDateFolder / SourceFile.name
                shutil.move(str(SourceFile), str(TargetPath))
                
                Result['status'] = 'moved'
                Result['target'] = str(TargetPath)
                Result['message'] = 'Moved to docs (dated, original filename)'
                Logger.info(f"✅ {SourceFile.name} -> {TargetPath}")
                
            else:
                Result['status'] = 'skipped'
                Result['message'] = 'No header path found and not a doc file'
                Logger.info(f"⏭️ {SourceFile.name} -> Skipped")
                
        except Exception as Error:
            Result['status'] = 'error'
            Result['message'] = f'Processing error: {Error}'
            Logger.error(f"❌ {SourceFile.name} -> Error: {Error}")
            
        return Result
        
    def ProcessAllFiles(self) -> Dict[str, any]:
        """Process all files in Updates folder."""
        Logger.info("Starting file processing with Design Standard v1.9...")
        
        if not self.UpdatesFolder.exists():
            Logger.error("Updates folder does not exist")
            return {'status': 'error', 'message': 'Updates folder not found'}
            
        Files = list(self.UpdatesFolder.iterdir())
        if not Files:
            Logger.info("No files to process")
            return {'status': 'success', 'message': 'No files found', 'results': []}
            
        Results = []
        Stats = {'moved': 0, 'skipped': 0, 'errors': 0, 'warnings': 0}
        
        for File in Files:
            if File.is_file():
                Result = self.ProcessFile(File)
                Results.append(Result)
                
                # Update stats
                if Result['status'] in Stats:
                    Stats[Result['status']] += 1
                else:
                    Stats['errors'] += 1
                    
        # Generate report
        ReportPath = self._GenerateReport(Results, Stats)
        
        Logger.info(f"Processing complete: {Stats}")
        
        return {
            'status': 'success',
            'stats': Stats,
            'results': Results,
            'report_path': str(ReportPath)
        }
        
    def _GenerateReport(self, Results: List[Dict], Stats: Dict) -> Path:
        """Generate markdown report with v1.9 compliance details."""
        Timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ReportPath = self.DocsFolder / "Updates" / f"Updates_{Timestamp}.md"
        
        # Ensure directory exists
        ReportPath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ReportPath, 'w', encoding='utf-8') as Report:
            Report.write(f"""# File: Updates_{Timestamp}.md
# Path: Docs/Updates/Updates_{Timestamp}.md
# Standard: AIDEV-PascalCase-1.9
# Created: {datetime.now().strftime("%Y-%m-%d")}
# Last Modified: {datetime.now().strftime("%Y-%m-%d  %I:%M%p")}
---

# Updates Status Report — {Timestamp}

**Design Standard:** v1.9 (Web-Enhanced & AI-Compliant)

**Total files processed:** {len(Results)}

**Summary:**
- ✅ Moved: {Stats['moved']}
- ⏭️ Skipped: {Stats['skipped']}
- ❌ Errors: {Stats['errors']}
- ⚠️ Warnings: {Stats['warnings']}

**Details:**

""")
            
            for Result in Results:
                Status = Result['status']
                StatusIcon = {
                    'moved': '✅',
                    'skipped': '⏭️',
                    'error': '❌',
                    'warning': '⚠️'
                }.get(Status, '❓')
                
                SourceName = Path(Result['source']).name
                Message = Result['message']
                
                if Result['target']:
                    TargetRel = Path(Result['target']).relative_to(self.ProjectRoot)
                    Report.write(f"- {StatusIcon} **{SourceName}**: {Message}  \n")
                    Report.write(f"    `{TargetRel}`\n\n")
                else:
                    Report.write(f"- {StatusIcon} **{SourceName}**: {Message}  \n")
                    Report.write(f"    `Kept in: Updates/{SourceName}`\n\n")
                    
        Logger.info(f"Report generated: {ReportPath}")
        return ReportPath

def main():
    """Main execution function."""
    Manager = WebAwareFileManager()
    
    try:
        Results = Manager.ProcessAllFiles()
        
        if Results['status'] == 'success':
            print(f"✅ Processing completed successfully!")
            print(f"📊 Stats: {Results['stats']}")
            print(f"📄 Report: {Results['report_path']}")
        else:
            print(f"❌ Processing failed: {Results.get('message', 'Unknown error')}")
            
    except Exception as Error:
        Logger.error(f"Fatal error: {Error}")
        print(f"💥 Fatal error: {Error}")

if __name__ == "__main__":
    main()