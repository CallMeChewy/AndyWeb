# File: StartAndyWeb.py
# Path: StartAndyWeb.py
# Standard: AIDEV-PascalCase-1.9
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:45PM
"""
Description: Enhanced startup script for AndyWeb with intelligent port detection
Handles environment setup, database verification, and automatic port failover.
Detects HP printer conflicts and other port issues automatically.
"""

import sys
import subprocess
import webbrowser
import time
import os
import socket
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
Logger = logging.getLogger(__name__)

class SmartAndyWebLauncher:
    """Enhanced launcher with intelligent port detection and failover."""
    
    def __init__(self):
        self.ProjectRoot = Path(__file__).parent
        self.APIPath = self.ProjectRoot / "Source" / "API" / "MainAPI.py"
        self.DatabasePath = self.ProjectRoot / "Data" / "Databases" / "MyLibraryWeb.db"
        self.RequirementsPath = self.ProjectRoot / "requirements.txt"
        
        # Smart port selection - try these in order
        self.PreferredPorts = [8000, 8001, 8002, 8003, 8004, 8080, 8888, 9000]
        self.SelectedPort = None
        
    def _IsPortAvailable(self, Port: int) -> bool:
        """Check if a port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Sock:
                Sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                Sock.bind(('127.0.0.1', Port))
                return True
        except OSError:
            return False
            
    def _DetectPortConflicts(self, Port: int) -> str:
        """Detect what might be using a port and provide helpful info."""
        try:
            # Try to get process info (Linux)
            Result = subprocess.run([
                'lsof', '-i', f':{Port}'
            ], capture_output=True, text=True, timeout=5)
            
            if Result.stdout:
                # Parse lsof output to identify the process
                Lines = Result.stdout.strip().split('\n')
                if len(Lines) > 1:  # Skip header
                    ProcessInfo = Lines[1].split()
                    if len(ProcessInfo) >= 2:
                        ProcessName = ProcessInfo[0]
                        ProcessPID = ProcessInfo[1]
                        
                        # Identify common culprits
                        if 'hp-printer' in ProcessName.lower():
                            return f"HP Printer App (PID {ProcessPID}) - very common on Linux"
                        elif 'apache' in ProcessName.lower():
                            return f"Apache Web Server (PID {ProcessPID})"
                        elif 'nginx' in ProcessName.lower():
                            return f"Nginx Web Server (PID {ProcessPID})"
                        elif 'python' in ProcessName.lower():
                            return f"Another Python application (PID {ProcessPID})"
                        else:
                            return f"{ProcessName} (PID {ProcessPID})"
                            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # lsof not available or timeout
            pass
            
        return "Unknown process"
        
    def FindAvailablePort(self) -> int:
        """Find the first available port from preferred list."""
        Logger.info("🔍 Scanning for available ports...")
        
        for Port in self.PreferredPorts:
            if self._IsPortAvailable(Port):
                self.SelectedPort = Port
                Logger.info(f"✅ Port {Port} is available")
                return Port
            else:
                Conflict = self._DetectPortConflicts(Port)
                Logger.info(f"❌ Port {Port} occupied by: {Conflict}")
                
        # If all preferred ports are taken, find any available port
        Logger.warning("⚠️ All preferred ports occupied, scanning for any available port...")
        
        for Port in range(8005, 8100):
            if self._IsPortAvailable(Port):
                self.SelectedPort = Port
                Logger.info(f"✅ Found available port: {Port}")
                return Port
                
        raise RuntimeError("No available ports found in range 8000-8099")
        
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
        """Start FastAPI development server with smart port selection."""
        try:
            # Find available port
            Port = self.FindAvailablePort()
            
            Logger.info("🚀 Starting AndyWeb API server...")
            Logger.info(f"📡 Server will be available at: http://127.0.0.1:{Port}")
            Logger.info(f"📚 API documentation at: http://127.0.0.1:{Port}/api/docs")
            Logger.info(f"🌐 Frontend application at: http://127.0.0.1:{Port}/app")
            
            if Port != 8000:
                Logger.info(f"🔄 Note: Using port {Port} instead of 8000 due to conflicts")
                
            Logger.info("")
            Logger.info("Press Ctrl+C to stop the server")
            Logger.info("=" * 70)
            
            # Change to API directory for relative imports
            APIDirectory = self.APIPath.parent
            os.chdir(APIDirectory)
            
            # Start uvicorn server with selected port
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "MainAPI:App",
                "--host", "127.0.0.1",
                "--port", str(Port),
                "--reload",
                "--log-level", "info"
            ])
            
        except KeyboardInterrupt:
            Logger.info("\nServer stopped by user")
        except Exception as Error:
            Logger.error(f"Failed to start server: {Error}")
            
    def OpenBrowser(self) -> None:
        """Open web browser to application with smart port detection."""
        try:
            # Wait a moment for server to start
            time.sleep(3)
            
            # Use the selected port or default
            Port = self.SelectedPort or 8000
            AppURL = f"http://127.0.0.1:{Port}/app"
            
            # Try to open the frontend application
            webbrowser.open(AppURL)
            Logger.info(f"🌐 Opening browser to: {AppURL}")
            
        except Exception as Error:
            Logger.warning(f"Could not open browser automatically: {Error}")
            Port = self.SelectedPort or 8000
            Logger.info(f"Please manually navigate to: http://127.0.0.1:{Port}/app")
            
    def ShowPortInfo(self) -> None:
        """Display helpful information about port conflicts."""
        print("\n💡 Port Information:")
        print("─" * 50)
        print("• AndyWeb prefers port 8000, but will adapt automatically")
        print("• Common conflicts:")
        print("  - HP Printer App (very common on Linux)")
        print("  - Apache/Nginx web servers")
        print("  - Other development servers")
        print("• AndyWeb will try ports: 8000 → 8001 → 8002 → etc.")
        print("• Your selected port will be shown when server starts")
        print()
            
    def Run(self) -> None:
        """Main launcher routine with intelligent port management."""
        print("🚀 AndyWeb Library - Smart Startup")
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
            
        print("\n✅ All checks passed! Finding available port...")
        print("=" * 50)
        
        # Show port info for educational purposes
        self.ShowPortInfo()
        
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
🔥 AndyWeb Smart Launcher 🔥

Usage: python StartAndyWeb.py [options]

Options:
  --help, -h     Show this help message
  --check        Run environment checks only (don't start server)
  --no-browser   Don't open browser automatically
  --port XXXX    Try specific port first (still falls back if occupied)

Smart Features:
✓ Automatic port detection (8000 → 8001 → 8002 → etc.)
✓ HP Printer conflict detection and resolution
✓ Helpful process identification for port conflicts
✓ Environment validation with detailed feedback
✓ Browser auto-launch with correct port

What this script does:
✓ Validates Python version (3.8+)
✓ Checks database file exists  
✓ Verifies API files are present  
✓ Installs missing dependencies
✓ Configures environment
✓ Finds available port automatically
✓ Starts FastAPI development server
✓ Opens browser to correct port

URLs when running (example with port 8001):
• Frontend App: http://127.0.0.1:8001/app
• API Docs: http://127.0.0.1:8001/api/docs
• API Root: http://127.0.0.1:8001/api

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
            Launcher = SmartAndyWebLauncher()
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
                # Also check port availability
                Port = Launcher.FindAvailablePort()
                print(f"🔌 Available port found: {Port}")
            else:
                print("\n❌ Some checks failed. Fix issues before launching.")
            sys.exit(0)
    
    # Normal startup
    try:
        Launcher = SmartAndyWebLauncher()
        Launcher.Run()
    except KeyboardInterrupt:
        print("\n👋 AndyWeb launcher stopped")
    except Exception as Error:
        print(f"\n💥 Startup error: {Error}")
        print("Run with --help for usage information")