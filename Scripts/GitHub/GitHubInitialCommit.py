#!/usr/bin/env python3
"""
Initial commit script for project.
This script adds all files, creates the initial commit, and pushes to GitHub.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a git command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def check_github_repo(project_name):
    """Check if GitHub repository exists and create if needed."""
    print(f"Checking GitHub repository: {project_name}")
    
    # Check if repo exists
    check_cmd = f"gh repo view {project_name}"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Repository doesn't exist. Creating GitHub repository...")
        create_cmd = f"gh repo create {project_name} --public --source=. --remote=origin --push"
        if not run_command(create_cmd, "Creating GitHub repository"):
            return False
    else:
        print("Repository exists. Checking remote...")
        # Check if remote origin exists
        remote_check = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True)
        if remote_check.returncode != 0:
            # Add remote if it doesn't exist
            add_remote_cmd = f"gh repo set-default {project_name}"
            run_command(add_remote_cmd, "Setting default repository")
            add_remote_cmd = f"git remote add origin https://github.com/$(gh api user --jq .login)/{project_name}.git"
            if not run_command(add_remote_cmd, "Adding remote origin"):
                return False
    
    return True

def main():
    """Create initial commit for the project and push to GitHub."""
    # Get the base folder name
    project_name = os.path.basename(os.getcwd())
    
    print(f"Creating initial commit for {project_name}")
    print("="*50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Check if GitHub CLI is available
    gh_check = subprocess.run("gh --version", shell=True, capture_output=True, text=True)
    if gh_check.returncode != 0:
        print("Error: GitHub CLI (gh) is not installed or not authenticated")
        print("Please install GitHub CLI and run 'gh auth login' first")
        sys.exit(1)
    
    # Add all files
    if not run_command("git add .", "Adding all files to staging area"):
        sys.exit(1)
    
    # Create initial commit
    commit_message = f"Initial commit - {project_name} project structure"
    if not run_command(f'git commit -m "{commit_message}"', "Creating initial commit"):
        sys.exit(1)
    
    # Setup GitHub repository and push
    if not check_github_repo(project_name):
        print("Failed to setup GitHub repository")
        sys.exit(1)
    
    # Push to GitHub
    if not run_command("git push -u origin main", "Pushing to GitHub"):
        sys.exit(1)
    
    print("\nInitial commit created and pushed successfully!")
    print(f"Project: {project_name}")
    print(f"Commit message: {commit_message}")
    print(f"GitHub URL: https://github.com/$(gh api user --jq .login)/{project_name}")

if __name__ == "__main__":
    main()