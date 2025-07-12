# GitHub Auto-Update Script for BowersWorld.com
# Author: Herb Bowers - Project Himalaya
# Created: 2025-06-22  17:15
# Path: /scripts/AutoUpdateGitHub.py

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import argparse


class GitHubAutoUpdater:
    def __init__(self, repo_path=None, remote_name="origin", branch="main"):
        """
        Initialize the GitHub auto-updater
        
        Args:
            repo_path: Path to your local repository (if None, uses current directory)
            remote_name: Git remote name (usually "origin")
            branch: Branch to push to (usually "main")
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.remote_name = remote_name
        self.branch = branch
        
        # Ensure we're in a git repository
        if not (self.repo_path / '.git').exists():
            raise Exception(f"Not a git repository: {self.repo_path}")
    
    def RunGitCommand(self, command):
        """Execute git command and return result"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {command}")
            print(f"Error: {e.stderr}")
            raise
    
    def CheckGitStatus(self):
        """Check if there are any changes to commit"""
        try:
            # Check for unstaged changes
            unstaged = self.RunGitCommand("git diff --name-only")
            
            # Check for staged changes
            staged = self.RunGitCommand("git diff --cached --name-only")
            
            # Check for untracked files
            untracked = self.RunGitCommand("git ls-files --others --exclude-standard")
            
            changes = {
                'unstaged': unstaged.split('\n') if unstaged else [],
                'staged': staged.split('\n') if staged else [],
                'untracked': untracked.split('\n') if untracked else []
            }
            
            return changes
        except Exception as e:
            print(f"Error checking git status: {e}")
            return None
    
    def AddFiles(self, files=None):
        """Add files to staging area"""
        if files:
            for file in files:
                self.RunGitCommand(f"git add {file}")
        else:
            # Add all changes
            self.RunGitCommand("git add .")
    
    def CreateCommit(self, message=None, auto_message=True):
        """Create a commit with given message"""
        if not message and auto_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto-update: {timestamp}"
        elif not message:
            raise ValueError("Commit message required when auto_message=False")
        
        self.RunGitCommand(f'git commit -m "{message}"')
        return message
    
    def PushToGitHub(self):
        """Push changes to GitHub"""
        push_command = f"git push {self.remote_name} {self.branch}"
        self.RunGitCommand(push_command)
    
    def AutoUpdate(self, commit_message=None, files=None, verbose=True):
        """
        Complete auto-update workflow: add, commit, push
        
        Args:
            commit_message: Custom commit message (auto-generated if None)
            files: Specific files to add (all changes if None)
            verbose: Print status messages
        """
        if verbose:
            print("🔄 Starting GitHub auto-update...")
        
        try:
            # Check for changes
            changes = self.CheckGitStatus()
            if not changes:
                if verbose:
                    print("❌ Error checking repository status")
                return False
            
            total_changes = len(changes['unstaged']) + len(changes['staged']) + len(changes['untracked'])
            
            if total_changes == 0:
                if verbose:
                    print("✅ No changes detected. Repository is up to date.")
                return True
            
            if verbose:
                print(f"📁 Found {total_changes} changed/new files:")
                for file in changes['unstaged'] + changes['untracked']:
                    if file:  # Skip empty strings
                        print(f"   - {file}")
            
            # Add files
            if verbose:
                print("📤 Adding files to staging area...")
            self.AddFiles(files)
            
            # Create commit
            if verbose:
                print("💾 Creating commit...")
            commit_msg = self.CreateCommit(commit_message)
            
            # Push to GitHub
            if verbose:
                print("🚀 Pushing to GitHub...")
            self.PushToGitHub()
            
            if verbose:
                print(f"✅ Successfully updated GitHub!")
                print(f"   Commit: {commit_msg}")
                print(f"   Branch: {self.branch}")
                print("🌐 GitHub Pages will update in 5-10 minutes")
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Error during auto-update: {e}")
            return False
    
    def SetupWatchMode(self, watch_directory=None, interval=30):
        """
        Watch for file changes and auto-update
        
        Args:
            watch_directory: Directory to watch (repo root if None)
            interval: Check interval in seconds
        """
        watch_dir = Path(watch_directory) if watch_directory else self.repo_path
        
        print(f"👀 Watching {watch_dir} for changes...")
        print(f"⏰ Check interval: {interval} seconds")
        print("Press Ctrl+C to stop")
        
        last_check = {}
        
        try:
            while True:
                current_check = {}
                changes_detected = False
                
                # Check modification times of files
                for file_path in watch_dir.rglob('*'):
                    if file_path.is_file() and not str(file_path).startswith('.git'):
                        try:
                            mtime = file_path.stat().st_mtime
                            current_check[str(file_path)] = mtime
                            
                            if str(file_path) in last_check:
                                if last_check[str(file_path)] != mtime:
                                    changes_detected = True
                            else:
                                changes_detected = True
                        except:
                            continue
                
                if changes_detected and last_check:  # Skip first run
                    print(f"\n🔔 Changes detected at {datetime.now().strftime('%H:%M:%S')}")
                    if self.AutoUpdate(verbose=True):
                        print("✅ Auto-update completed successfully\n")
                    else:
                        print("❌ Auto-update failed\n")
                
                last_check = current_check
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Watch mode stopped")


def CreateConfigFile(repo_path="."):
    """Create a configuration file for the auto-updater"""
    config = {
        "repository": {
            "path": str(Path(repo_path).absolute()),
            "remote": "origin",
            "branch": "main"
        },
        "auto_update": {
            "default_message_prefix": "Auto-update",
            "include_timestamp": True,
            "watch_interval": 30
        },
        "excluded_files": [
            ".git/*",
            "*.log",
            "*.tmp",
            "__pycache__/*",
            "node_modules/*"
        ]
    }
    
    config_path = Path(repo_path) / "auto_update_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration file created: {config_path}")
    return config_path


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="GitHub Auto-Update Script")
    parser.add_argument("--path", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--message", "-m", help="Commit message")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch mode for continuous updates")
    parser.add_argument("--interval", "-i", type=int, default=30, help="Watch interval in seconds")
    parser.add_argument("--setup", action="store_true", help="Create configuration file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (less output)")
    
    args = parser.parse_args()
    
    try:
        if args.setup:
            CreateConfigFile(args.path)
            return
        
        # Initialize updater
        updater = GitHubAutoUpdater(repo_path=args.path)
        
        if args.watch:
            # Watch mode
            updater.SetupWatchMode(interval=args.interval)
        else:
            # Single update
            success = updater.AutoUpdate(
                commit_message=args.message,
                verbose=not args.quiet
            )
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


# Usage examples and helper functions
class LibraryUpdater:
    """Specialized updater for Anderson's Library files"""
    
    def __init__(self, repo_path="."):
        self.updater = GitHubAutoUpdater(repo_path)
    
    def UpdateLibraryDatabase(self, db_path):
        """Update when library database changes"""
        return self.updater.AutoUpdate(
            commit_message=f"Update library database: {Path(db_path).name}",
            files=[db_path]
        )
    
    def UpdateLibraryPages(self):
        """Update library-specific pages"""
        library_files = [
            "library/index.html",
            "library/app/index.html", 
            "library/auth/*.html",
            "library/js/*.js",
            "library/css/*.css"
        ]
        
        return self.updater.AutoUpdate(
            commit_message="Update Anderson's Library interface",
            files=library_files
        )
    
    def QuickUpdate(self, message="Quick library update"):
        """Quick update of all changes"""
        return self.updater.AutoUpdate(commit_message=message)


if __name__ == "__main__":
    main()
