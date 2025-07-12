#!/usr/bin/env python3
"""
File: SimpleTree.py
Description: A simplified tree visualization script that strictly respects .gitignore rules using pathspec.
"""

import os
from pathlib import Path
import pathspec

def generate_tree_output(start_path, spec, base_path, prefix="", output_lines=None):
    """Recursively generates tree view lines, respecting gitignore rules."""
    if output_lines is None:
        output_lines = []

    try:
        entries = sorted(os.listdir(start_path))
    except FileNotFoundError:
        return output_lines

    dirs = [e for e in entries if (start_path / e).is_dir()]
    files = [e for e in entries if not (start_path / e).is_dir()]
    
    all_entries = dirs + files
    pointers = ['├── ' for _ in range(len(all_entries) - 1)] + ['└── ']

    for i, (pointer, item) in enumerate(zip(pointers, all_entries)):
        item_path = start_path / item
        relative_path_str = item_path.relative_to(base_path).as_posix()

        # pathspec.match_file returns True if the file should be ignored
        # We want to include if it's NOT ignored.
        should_ignore_item = spec.match_file(relative_path_str)

        # Special handling for directories that are ignored by content-only patterns (e.g., **/Books/*)
        # pathspec will ignore the directory itself if its contents are ignored.
        # We want to show the directory, but not its contents.
        is_content_only_ignored = False # Initialize here
        if item_path.is_dir() and should_ignore_item:
            # Check if any pattern that matches this directory is a content-only pattern
            # This is a heuristic, as pathspec doesn't expose the matching pattern type directly.
            # We assume if a directory is ignored, but not by a trailing slash pattern, it's content-only.
            is_content_only_ignored = False
            with open(base_path / '.gitignore', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and line.endswith('/*'):
                        # Create a temporary spec for this single pattern
                        temp_spec = pathspec.PathSpec.from_lines('gitwildmatch', [line])
                        if temp_spec.match_file(relative_path_str):
                            is_content_only_ignored = True
                            break
            
            if is_content_only_ignored:
                should_ignore_item = False # Don't ignore the directory itself

        if not should_ignore_item:
            output_lines.append(f"{prefix}{pointer}{item}")
            if item_path.is_dir() and not is_content_only_ignored: # Only recurse if not content-only ignored
                extension = '│   ' if i < len(all_entries) - 1 else '    '
                generate_tree_output(item_path, spec, base_path, prefix=prefix + extension, output_lines=output_lines)
    return output_lines

def main():
    """Main entry point"""
    base_path = Path('.').resolve()
    gitignore_path = base_path / '.gitignore'
    
    # Load .gitignore patterns using pathspec
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = f.readlines()
    
    # Always ignore .git directory and ..Excclude
    patterns.append('.git/')
    patterns.append('..Excclude/')

    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    print(f"Generating simplified gitignore-aware tree view using pathspec...")
    tree_lines = [f". ({base_path.name})"]
    tree_lines.extend(generate_tree_output(base_path, spec, base_path))

    for line in tree_lines:
        print(line)
    
    # No longer writing to a file, so remove the print statement about the file.
    # print(f"Full simplified tree view written to: {output_filename}")

if __name__ == "__main__":
    main()