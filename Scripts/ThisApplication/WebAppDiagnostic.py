# File: WebAppDiagnostic.py
# Path: Scripts/System/WebAppDiagnostic.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-08
# Last Modified: 2025-07-08  11:06PM
"""
Description: Anderson's Library Web App Diagnostic Script
Verifies web application setup and identifies common issues
"""

import os
import sys
import requests
import json
from pathlib import Path
from urllib.parse import urljoin

class WebAppDiagnostic:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.project_root = Path(__file__).parent.parent.parent
        self.webpages_dir = self.project_root / "WebPages"
        self.issues = []
        self.successes = []
    
    def log_success(self, message):
        """Log a successful check"""
        self.successes.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def log_issue(self, message, severity="WARNING"):
        """Log an issue found"""
        icon = "❌" if severity == "ERROR" else "⚠️"
        self.issues.append(f"{icon} {severity}: {message}")
        print(f"{icon} {severity}: {message}")
    
    def check_file_exists(self, file_path, description):
        """Check if a file exists"""
        full_path = self.project_root / file_path
        if full_path.exists():
            self.log_success(f"{description} exists: {file_path}")
            return True
        else:
            self.log_issue(f"{description} missing: {file_path}", "ERROR")
            return False
    
    def check_api_endpoint(self, endpoint, description):
        """Check if an API endpoint responds"""
        try:
            url = urljoin(self.base_url, endpoint)
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.log_success(f"{description} responding: {endpoint}")
                return True, response.json()
            else:
                self.log_issue(f"{description} error {response.status_code}: {endpoint}")
                return False, None
                
        except requests.ConnectionError:
            self.log_issue(f"Cannot connect to {description}: {endpoint} (Server not running?)", "ERROR")
            return False, None
        except requests.Timeout:
            self.log_issue(f"{description} timeout: {endpoint}")
            return False, None
        except Exception as e:
            self.log_issue(f"{description} error: {str(e)}")
            return False, None
    
    def run_diagnostic(self):
        """Run complete diagnostic check"""
        print("🔍 Anderson's Library Web App Diagnostic")
        print("=" * 50)
        
        # 1. Check critical files
        print("\n📂 Checking Critical Files:")
        self.check_file_exists("StartAndyWeb.py", "Web launcher")
        self.check_file_exists("Source/API/MainAPI.py", "FastAPI backend")
        self.check_file_exists("WebPages/desktop-library.html", "Desktop web interface")
        self.check_file_exists("WebPages/JS/library-api-client.js", "JavaScript API client")
        self.check_file_exists("Data/Databases/MyLibraryWeb.db", "Web database")
        
        # 2. Check optional files
        print("\n📄 Checking Optional Files:")
        self.check_file_exists("WebPages/mobile-library.html", "Mobile web interface")
        self.check_file_exists("requirements.txt", "Python dependencies")
        
        # 3. Check API server status
        print("\n🌐 Checking API Server:")
        server_running, _ = self.check_api_endpoint("/api/docs", "FastAPI docs")
        
        if server_running:
            # 4. Check API endpoints
            print("\n🔗 Checking API Endpoints:")
            books_ok, books_data = self.check_api_endpoint("/api/books", "Books endpoint")
            cats_ok, cats_data = self.check_api_endpoint("/api/categories", "Categories endpoint")
            subjects_ok, subjects_data = self.check_api_endpoint("/api/subjects", "Subjects endpoint")
            stats_ok, stats_data = self.check_api_endpoint("/api/stats", "Statistics endpoint")
            
            # 5. Check web app serving
            print("\n🖥️ Checking Web Interface:")
            self.check_api_endpoint("/app", "Desktop web app")
            
            # 6. Analyze data if available
            if books_data and isinstance(books_data, dict):
                books_list = books_data.get('books', [])
                total_books = len(books_list)
                if total_books > 0:
                    self.log_success(f"Database contains {total_books} books")
                else:
                    self.log_issue("Database appears empty")
            
            if stats_data:
                total_books = stats_data.get('total_books', 0)
                total_categories = stats_data.get('total_categories', 0)
                total_subjects = stats_data.get('total_subjects', 0)
                self.log_success(f"Library stats: {total_books} books, {total_categories} categories, {total_subjects} subjects")
        
        else:
            print("\n🚫 Cannot check endpoints - server not responding")
            print("💡 Try running: python StartAndyWeb.py")
        
        # 7. Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate final diagnostic report"""
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC REPORT")
        print("=" * 50)
        
        print(f"\n✅ SUCCESSES ({len(self.successes)}):")
        for success in self.successes:
            print(f"  {success}")
        
        if self.issues:
            print(f"\n⚠️  ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
        else:
            print("\n🎉 NO ISSUES FOUND!")
        
        # Provide recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if any("Server not running" in issue for issue in self.issues):
            print("  • Start the web server: python StartAndyWeb.py")
        
        if any("library-api-client.js" in issue for issue in self.issues):
            print("  • Create missing JavaScript API client file")
            print("  • Check WebPages/JS/ directory structure")
        
        if any("Database" in issue for issue in self.issues):
            print("  • Verify database file exists and has data")
            print("  • Check Data/Databases/MyLibraryWeb.db")
        
        if any("404" in issue for issue in self.issues):
            print("  • Verify FastAPI static file mounting configuration")
            print("  • Check MainAPI.py static files setup")
        
        if not self.issues:
            print("  • Your Anderson's Library web app is ready to use!")
            print("  • Open browser to: http://127.0.0.1:8000/app")
        
        print("\n🚀 Happy reading! 📚")

def main():
    """Main diagnostic function"""
    diagnostic = WebAppDiagnostic()
    diagnostic.run_diagnostic()

if __name__ == "__main__":
    main()