# Simple Auto-Update Script for BowersWorld.com
# Author: Herb Bowers - Project Himalaya  
# Created: 2025-06-22  17:30
# Path: /UpdateSite.py

import os
import subprocess
import sys
from datetime import datetime

def RunCommand(command, show_output=True):
    """Run a command and return result"""
    try:
        if show_output:
            print(f"🔄 Running: {command}")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            if show_output and result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def UpdateSite(message=None):
    """Simple function to update GitHub Pages site"""
    
    print("🚀 BowersWorld.com Auto-Update Starting...")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Error: Not in a git repository")
        print("   Make sure you're in the BowersWorld-com directory")
        return False
    
    # Check for changes
    print("📋 Checking for changes...")
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    
    if not result.stdout.strip():
        print("✅ No changes detected. Site is up to date!")
        return True
    
    print("📁 Changes found:")
    changes = result.stdout.strip().split('\n')
    for change in changes:
        print(f"   {change}")
    
    # Create automatic commit message if none provided
    if not message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Site update: {timestamp}"
    
    # Add all changes
    print("\n📤 Adding changes...")
    if not RunCommand("git add ."):
        return False
    
    # Commit changes
    print("💾 Creating commit...")
    commit_command = f'git commit -m "{message}"'
    if not RunCommand(commit_command):
        return False
    
    # Push to GitHub
    print("🚀 Pushing to GitHub...")
    if not RunCommand("git push origin main"):
        return False
    
    print("\n" + "=" * 50)
    print("✅ SUCCESS! Site updated successfully!")
    print("🌐 GitHub Pages will update in 5-10 minutes")
    print("🔗 View at: https://callmechewy.github.io/BowersWorld-com/")
    print("=" * 50)
    
    return True

def QuickUpdate():
    """Quick update with automatic message"""
    return UpdateSite()

def CustomUpdate():
    """Update with custom commit message"""
    print("📝 Enter a custom commit message:")
    message = input("Message: ").strip()
    
    if not message:
        print("Using automatic message...")
        return UpdateSite()
    
    return UpdateSite(message)

def main():
    """Main menu for the updater"""
    print("📚 BowersWorld.com Site Updater")
    print("=" * 40)
    print("1. Quick update (automatic message)")
    print("2. Custom update (enter your message)")
    print("3. Exit")
    print("=" * 40)
    
    while True:
        try:
            choice = input("Choose option (1-3): ").strip()
            
            if choice == "1":
                QuickUpdate()
                break
            elif choice == "2":
                CustomUpdate()
                break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

# Direct usage functions
def UpdateLibrary():
    """Update library-specific changes"""
    return UpdateSite("Update Anderson's Library")

def UpdateMainSite():
    """Update main site changes"""
    return UpdateSite("Update Project Himalaya site")

def UpdateDatabase():
    """Update when database changes"""
    return UpdateSite("Update library database")

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            QuickUpdate()
        elif sys.argv[1] == "--library":
            UpdateLibrary()
        elif sys.argv[1] == "--main":
            UpdateMainSite()
        elif sys.argv[1] == "--database":
            UpdateDatabase()
        elif sys.argv[1] == "--message" and len(sys.argv) > 2:
            UpdateSite(" ".join(sys.argv[2:]))
        else:
            print("Usage:")
            print("  python update_site.py               # Interactive menu")
            print("  python update_site.py --quick       # Quick update")
            print("  python update_site.py --library     # Library update")
            print("  python update_site.py --main        # Main site update")
            print("  python update_site.py --database    # Database update")
            print("  python update_site.py --message 'Your message'")
    else:
        # Run interactive menu
        main()
