# File: StartAndyWeb.py
# Path: StartAndyWeb.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:29PM
"""
Description: Startup script for AndyWeb library system
Launches FastAPI server with proper configuration and opens browser automatically.
Handles environment setup, database verification, and development server startup.
"""

import sys
import subprocess
import webbrowser
import time
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
Logger = logging.getLogger(__name__)

class AndyWebLauncher:
    """Launcher for AndyWeb application with environment setup and validation."""
    
    def __init__(self):
        self.ProjectRoot = Path(__file__).parent
        self.APIPath = self.ProjectRoot / "Source" / "API" / "MainAPI.py"
        self.DatabasePath = self.ProjectRoot / "Data" / "Databases" / "MyLibraryWeb.db"
        self.RequirementsPath = self.ProjectRoot / "requirements.txt"
        
    def CheckPythonVersion(self) -> bool:
        """Verify Python version compatibility."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            Logger.error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}")
            return False
        
        Logger.info(f"Python version: {version.major}.{version.minor}.{version.micro} ✓")
        return True
        
    def CheckDatabase(self) -> bool:
        """Verify database file exists and is accessible."""
        if not self.DatabasePath.exists():
            Logger.error(f"Database not found: {self.DatabasePath}")
            Logger.error("Please ensure MyLibraryWeb.db is in Data/Databases/")
            return False
            
        Logger.info(f"Database found: {self.DatabasePath} ✓")
        return True
        
    def CheckDependencies(self) -> bool:
        """Check and install required dependencies."""
        try:
            # Check if FastAPI is installed
            import fastapi
            import uvicorn
            Logger.info("FastAPI dependencies found ✓")
            return True
            
        except ImportError:
            Logger.warning("FastAPI not found. Attempting to install dependencies...")
            
            if not self.RequirementsPath.exists():
                Logger.error("requirements.txt not found")
                return False
                
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", str(self.RequirementsPath)
                ])
                Logger.info("Dependencies installed successfully ✓")
                return True
                
            except subprocess.CalledProcessError as Error:
                Logger.error(f"Failed to install dependencies: {Error}")
                return False
                
    def CheckAPIFile(self) -> bool:
        """Verify API file exists."""
        if not self.APIPath.exists():
            Logger.error(f"API file not found: {self.APIPath}")
            return False
            
        Logger.info(f"API file found: {self.APIPath} ✓")
        return True
        
    def SetupEnvironment(self) -> bool:
        """Setup Python path and environment variables."""
        try:
            # Add Source directory to Python path
            SourcePath = str(self.ProjectRoot / "Source")
            if SourcePath not in sys.path:
                sys.path.insert(0, SourcePath)
                
            # Set environment variables
            os.environ['PYTHONPATH'] = SourcePath
            
            Logger.info("Environment configured ✓")
            return True
            
        except Exception as Error:
            Logger.error(f"Failed to setup environment: {Error}")
            return False
            
    def StartServer(self) -> None:
        """Start FastAPI development server."""
        try:
            Logger.info("Starting AndyWeb API server...")
            Logger.info("Server will be available at: http://127.0.0.1:8000")
            Logger.info("API documentation at: http://127.0.0.1:8000/api/docs")
            Logger.info("Frontend application at: http://127.0.0.1:8000/app")
            Logger.info("")
            Logger.info("Press Ctrl+C to stop the server")
            Logger.info("=" * 60)
            
            # Change to API directory for relative imports
            APIDirectory = self.APIPath.parent
            os.chdir(APIDirectory)
            
            # Start uvicorn server
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "MainAPI:App",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",
                "--log-level", "info"
            ])
            
        except KeyboardInterrupt:
            Logger.info("\nServer stopped by user")
        except Exception as Error:
            Logger.error(f"Failed to start server: {Error}")
            
    def OpenBrowser(self) -> None:
        """Open web browser to application."""
        try:
            # Wait a moment for server to start
            time.sleep(2)
            
            # Try to open the frontend application
            webbrowser.open("http://127.0.0.1:8000/app")
            Logger.info("Opening browser to AndyWeb application...")
            
        except Exception as Error:
            Logger.warning(f"Could not open browser automatically: {Error}")
            Logger.info("Please manually navigate to: http://127.0.0.1:8000/app")
            
    def Run(self) -> None:
        """Main launcher routine with full validation."""
        print("🚀 AndyWeb Library - Starting Up...")
        print("=" * 50)
        
        # Run all validation checks
        checks = [
            ("Python Version", self.CheckPythonVersion),
            ("Database File", self.CheckDatabase),
            ("API Files", self.CheckAPIFile),
            ("Dependencies", self.CheckDependencies),
            ("Environment", self.SetupEnvironment)
        ]
        
        for CheckName, CheckFunction in checks:
            print(f"Checking {CheckName}...", end=" ")
            if not CheckFunction():
                print(f"❌ {CheckName} check failed")
                print("\nStartup aborted. Please fix the issues above.")
                return
            print("✓")
            
        print("\n✅ All checks passed! Starting server...")
        print("=" * 50)
        
        # Start server (this will block)
        try:
            # Start browser in a separate thread after short delay
            import threading
            BrowserThread = threading.Thread(target=self.OpenBrowser)
            BrowserThread.daemon = True
            BrowserThread.start()
            
            # Start the server (blocking)
            self.StartServer()
            
        except Exception as Error:
            Logger.error(f"Startup failed: {Error}")
            
def ShowHelp():
    """Display help information."""
    print("""
🔥 AndyWeb Library Launcher 🔥

Usage: python StartAndyWeb.py [options]

Options:
  --help, -h     Show this help message
  --check        Run environment checks only (don't start server)
  --no-browser   Don't open browser automatically

What this script does:
✓ Validates Python version (3.8+)
✓ Checks database file exists
✓ Verifies API files are present  
✓ Installs missing dependencies
✓ Configures environment
✓ Starts FastAPI development server
✓ Opens browser to application

URLs when running:
• Frontend App: http://127.0.0.1:8000/app
• API Docs: http://127.0.0.1:8000/api/docs
• API Root: http://127.0.0.1:8000/api

For support: HimalayaProject1@gmail.com
""")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            ShowHelp()
            sys.exit(0)
        elif sys.argv[1] == '--check':
            # Run checks only
            Launcher = AndyWebLauncher()
            checks = [
                ("Python Version", Launcher.CheckPythonVersion),
                ("Database File", Launcher.CheckDatabase),
                ("API Files", Launcher.CheckAPIFile),
                ("Dependencies", Launcher.CheckDependencies),
                ("Environment", Launcher.SetupEnvironment)
            ]
            
            print("🔍 AndyWeb Environment Check")
            print("=" * 30)
            
            AllPassed = True
            for CheckName, CheckFunction in checks:
                print(f"Checking {CheckName}...", end=" ")
                if CheckFunction():
                    print("✓")
                else:
                    print("❌")
                    AllPassed = False
                    
            if AllPassed:
                print("\n✅ All checks passed! Ready to launch.")
            else:
                print("\n❌ Some checks failed. Fix issues before launching.")
            sys.exit(0)
    
    # Normal startup
    try:
        Launcher = AndyWebLauncher()
        Launcher.Run()
    except KeyboardInterrupt:
        print("\n👋 AndyWeb launcher stopped")
    except Exception as Error:
        print(f"\n💥 Startup error: {Error}")
        print("Run with --help for usage information")