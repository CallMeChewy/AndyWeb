#!/usr/bin/env python3
"""
Project backup script that respects .gitignore files, including negation and precedence.
"""

import os
import shutil
import sys
from datetime import datetime
import fnmatch
from pathlib import Path

def parse_gitignore(gitignore_path):
    """Parse .gitignore file and return a list of patterns with their type."""
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                is_negation = line.startswith('!')
                if is_negation:
                    line = line[1:]
                
                patterns.append({'pattern': line, 'negation': is_negation})
    return patterns

def path_matches_pattern(path, pattern, is_dir):
    """Check if a given path string matches a gitignore pattern."""
    # A pattern ending in a slash is for directories only
    if pattern.endswith('/'):
        if not is_dir:
            return False
        pattern = pattern.rstrip('/')

    # A pattern with no slash matches basenames
    if '/' not in pattern:
        return fnmatch.fnmatch(Path(path).name, pattern)
    
    # A pattern with a slash matches from the root
    # We use pathlib's match which understands '**'
    return Path(path).match(pattern)

def is_path_ignored(path, patterns, base_path):
    """Determines if a path should be ignored by finding the last matching pattern."""
    relative_path = Path(path).relative_to(base_path).as_posix()
    is_dir = Path(path).is_dir()

    # According to gitignore spec, a file cannot be re-included if a parent dir is excluded.
    # First, check if any parent directory is conclusively ignored.
    parent = Path(relative_path).parent
    while str(parent) != '.':
        if is_path_ignored(base_path / parent, patterns, base_path):
            # Now, we must check if the current path is explicitly re-included by a negation pattern.
            is_reincluded = False
            for p_info in patterns:
                if p_info['negation'] and path_matches_pattern(relative_path, p_info['pattern'], is_dir):
                    is_reincluded = True
            if not is_reincluded:
                return True # Parent is ignored and this path is not re-included.
        parent = parent.parent

    # Find the last pattern that matches this path.
    last_match = None
    for p_info in patterns:
        if path_matches_pattern(relative_path, p_info['pattern'], is_dir):
            last_match = p_info

    if last_match:
        return not last_match['negation']
    
    return False

def copy_with_gitignore(src, dst, patterns, base_path):
    """Copy directory tree while respecting gitignore patterns."""
    # First, check if the source directory itself should be ignored.
    if is_path_ignored(src, patterns, base_path):
        return

    if not os.path.exists(dst):
        os.makedirs(dst)
    
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        
        if not is_path_ignored(src_path, patterns, base_path):
            if os.path.isdir(src_path):
                copy_with_gitignore(src_path, dst_path, patterns, base_path)
            else:
                shutil.copy2(src_path, dst_path)

def backup_project(project_name=None):
    """Backup the current project, respecting .gitignore if present."""
    if not project_name:
        project_name = os.path.basename(os.getcwd())
    
    backup_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Projects_Backup")
    date_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{project_name}_{date_stamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)
    os.makedirs(backup_dir, exist_ok=True)
    
    src_dir = os.getcwd()
    
    gitignore_path = os.path.join(src_dir, '.gitignore')
    patterns = parse_gitignore(gitignore_path)
    
    # Always ignore .git directory
    patterns.append({'pattern': '.git/', 'negation': False})
    
    print(f"Backing up project: {project_name}")
    print(f"Using {len(patterns)} patterns from .gitignore")
    
    try:
        copy_with_gitignore(src_dir, backup_path, patterns, src_dir)
        print(f"Project backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error during backup: {e}")
        return None

def main():
    """Main entry point"""
    project_name = None
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    
    backup_project(project_name)

if __name__ == "__main__":
    main()
