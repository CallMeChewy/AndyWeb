# File: AndersonLibrary.py
# Path: AndersonLibrary.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  12:15PM
"""
Description: Anderson's Library Entry Point - Original Pattern (Fixed)
Follows the exact pattern from Legacy/Andy.py to prevent system lockups.
"""

import sys
import logging
import os
from pathlib import Path
from typing import Optional

# Ensure application's working directory is set correctly
os.chdir(Path(__file__).parent)

# Ensure Source directory is in Python path
SourcePath = Path(__file__).parent / "Source"
if str(SourcePath) not in sys.path:
    sys.path.insert(0, str(SourcePath))

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QIcon
except ImportError as ImportError:
    print("❌ PySide6 is not installed!")
    print("💡 Please install it with: pip install PySide6")
    sys.exit(1)

# Import our modules using original pattern
try:
    from Source.Interface.MainWindow import MainWindow
    from Source.Core.DatabaseManager import DatabaseManager
    from Source.Core.BookService import BookService
except ImportError as Error:
    print(f"❌ Failed to import application modules: {Error}")
    print("💡 Make sure all Source files are in place")
    sys.exit(1)


def PrintStartupBanner() -> None:
    """Print the professional startup banner"""
    print("🏔️ Anderson's Library - Professional Edition")
    print("=" * 50)
    print("📚 Digital Library Management System")
    print("🎯 Project Himalaya - BowersWorld.com")
    print("⚡ Modular Architecture - Design Standard v1.8")
    print("🔧 Using Original CustomWindow Pattern")
    print("=" * 50)


def ValidateEnvironment() -> bool:
    """
    Validate the environment and required files.
    
    Returns:
        True if environment is valid, False otherwise
    """
    print("📁 Checking file structure...")
    
    RequiredFiles = [
        "Source/Data/DatabaseModels.py",
        "Source/Core/DatabaseManager.py", 
        "Source/Core/BookService.py",
        "Source/Interface/FilterPanel.py",
        "Source/Interface/BookGrid.py",
        "Source/Interface/MainWindow.py",
    ]
    
    MissingFiles = []
    PresentFiles = []
    
    for FilePath in RequiredFiles:
        if Path(FilePath).exists():
            print(f" ✅ {FilePath}")
            PresentFiles.append(FilePath)
        else:
            print(f" ❌ {FilePath}")
            MissingFiles.append(FilePath)
    
    print(f"📊 Files: {len(PresentFiles)} present, {len(MissingFiles)} missing")
    
    # Check database
    print("🗄️ Testing database connection...")
    DatabasePath = Path("Assets/my_library.db")
    if DatabasePath.exists():
        print(f" ✅ Found database: {DatabasePath}")
    else:
        print(f" ⚠️ Database not found: {DatabasePath}")
        print(" 💡 Application will attempt to create/find database")
    
    # Check PySide6 and CustomWindow compatibility
    print("🐍 Testing Python imports...")
    try:
        from PySide6.QtWidgets import QApplication
        print(" ✅ PySide6 available")
    except ImportError as Error:
        print(f" ❌ Import error: {Error}")
        return False
    
    print("=" * 50)
    
    if MissingFiles:
        print(f"❌ Missing {len(MissingFiles)} required files!")
        return False
    
    print("✅ ENVIRONMENT VALIDATION PASSED")
    return True


def InitializeLogging() -> None:
    """Initialize application logging"""
    # Create logs directory if it doesn't exist
    LogsDir = Path("Logs")
    LogsDir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(LogsDir / "anderson_library.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def RunApplicationOriginalPattern() -> int:
    """
    Run Anderson's Library using the exact original pattern from Legacy/Andy.py.
    
    Returns:
        Application exit code
    """
    try:
        # Print startup banner
        PrintStartupBanner()
        
        # Validate environment
        if not ValidateEnvironment():
            print("❌ Environment validation failed!")
            print("💡 Please fix the issues above and try again")
            return 1
        
        # Initialize logging
        InitializeLogging()
        Logger = logging.getLogger("AndersonLibrary")
        
        print("🚀 Starting Anderson's Library...")
        print("=" * 50)
        
        # Create QApplication (like original Andy.py)
        App = QApplication(sys.argv)
        App.setApplicationName("Anderson's Library")
        App.setApplicationVersion("2.0")
        App.setOrganizationName("Project Himalaya")
        App.setOrganizationDomain("BowersWorld.com")
        AppIconPath = Path(__file__).parent / "Assets" / "icon.png"
        AppIcon = QIcon(str(AppIconPath))
        if AppIcon.isNull():
            Logger.warning(f"Failed to load application icon from {AppIconPath}")
        App.setWindowIcon(AppIcon)
        
        # Apply the original stylesheet (exactly like Legacy/Andy.py)
        
        
        try:
            # Follow the EXACT original pattern from Legacy/Andy.py:
            # main_window = MainWindow()
            # window = CustomWindow("Anderson's Library", main_window)
            # window.showMaximized()
            
            Logger.info("Creating main window...")
            MainWindowInstance = MainWindow()
            
            Logger.info("Showing maximized...")
            MainWindowInstance.showMaximized()
            MainWindowInstance.setWindowIcon(AppIcon)
            
            Logger.info("Anderson's Library started successfully")
            
            # Run the event loop (like original)
            ExitCode = App.exec()
            Logger.info(f"Application exited with code: {ExitCode}")
            return ExitCode
            
        except Exception as Error:
            Logger.error(f"Failed to start main window: {Error}")
            
            # Show error message
            QMessageBox.critical(
                None,
                "Application Error",
                f"Failed to start Anderson's Library:\n\n{Error}\n\nPlease check the console for details."
            )
            return 1
            
    except Exception as Error:
        print(f"❌ Critical error: {Error}")
        return 1


def ShowQuickHelp() -> None:
    """Show quick help information"""
    print("\n🆘 Anderson's Library - Quick Help")
    print("=" * 40)
    print("📋 Common Issues:")
    print("• Missing PySide6: pip install PySide6")
    print("• Missing CustomWindow: cp Legacy/CustomWindow.py Source/Interface/")
    print("• Missing files: Check Source/ directory structure")
    print("• Database issues: Ensure Assets/my_library.db exists")
    print("• Import errors: Verify all __init__.py files exist")
    print("\n📁 Required Directory Structure:")
    print("Source/")
    print("├── Core/")
    print("├── Data/") 
    print("├── Interface/")
    print("│   ├── CustomWindow.py  ← Critical!")
    print("│   ├── MainWindow.py")
    print("│   ├── FilterPanel.py")
    print("│   └── BookGrid.py")
    print("└── Utils/")
    print("\n🔧 Original Pattern:")
    print("• main_window = MainWindow()          # Content widget")
    print("• window = CustomWindow(..., main_window)  # Wrapper")
    print("• window.showMaximized()             # Display")
    print("\n🔗 Contact: HimalayaProject1@gmail.com")


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            ShowQuickHelp()
            sys.exit(0)
        elif sys.argv[1] in ["--version", "-v"]:
            print("Anderson's Library v2.0 - Professional Edition")
            print("Built with Design Standard v1.8")
            print("Using Original CustomWindow Pattern")
            sys.exit(0)
    
    # Run the application with original pattern
    ExitCode = RunApplicationOriginalPattern()
    sys.exit(ExitCode)