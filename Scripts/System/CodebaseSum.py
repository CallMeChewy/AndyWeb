#!/usr/bin/env python3
"""
File: CodebaseSum.py
Path: BowersWorld-com/Scripts/CodebaseSum.py
Created: 2025-06-25
Description: Generate a comprehensive codebase snapshot in a structured format,
             respecting .gitignore rules including negation and precedence.
"""

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import shutil
import sys
from PyPDF2 import PdfReader
import pathspec # Import pathspec

def generate_tree_output(start_path, spec, base_path, patterns, prefix="", output_lines=None):
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
            for line in patterns: # Use passed patterns
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
                generate_tree_output(item_path, spec, base_path, patterns, prefix=prefix + extension, output_lines=output_lines)
    return output_lines

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"CodebaseSummary_{timestamp}.txt"

    # The 'tree' command is no longer required.
    # if not shutil.which('tree'):
    #     print("Error: The 'tree' command is required but not found.")
    #     return 1

    print(f"Generating codebase summary to {output_file}...")
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

    with tempfile.TemporaryDirectory() as temp_dir:
        header_file = Path(temp_dir) / "header.txt"
        structure_file = Path(temp_dir) / "structure.txt"
        files_list_file = Path(temp_dir) / "files_list.txt"
        files_content_file = Path(temp_dir) / "files_content.txt"

        header_content = f"""
# Codebase Summary
- **Project:** {base_path.name}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Run from:** {os.getcwd()}
"""
        header_file.write_text(header_content, encoding='utf-8')

        # Generate gitignore-aware tree view
        print("Generating gitignore-aware tree view...")
        tree_lines = [f". ({base_path.name})"]
        tree_lines.extend(generate_tree_output(base_path, spec, base_path, patterns))
        structure_file.write_text("\n".join(tree_lines) + "\n")

        print("Finding relevant project files...")
        file_extensions = {'.py', '.sh', '.md', '.html', '.txt', '.pdf'}
        relevant_files = []

        for root, dirs, files in os.walk(base_path, topdown=True, followlinks=False):
            # Filter directories and files using pathspec
            # Prune ignored directories from traversal. Add trailing slash for dirs.
            dirs[:] = [d for d in dirs if not spec.match_file(
                str(Path(root, d).relative_to(base_path).as_posix()) + '/'
            )]

            for file in files:
                file_path = Path(root) / file
                
                # Skip symbolic links pointing outside the base path
                if os.path.islink(file_path) and not Path(os.path.realpath(file_path)).is_relative_to(base_path):
                    continue

                relative_file_path = file_path.relative_to(base_path).as_posix()
                
                # Only include files that are of relevant extension and not ignored by pathspec
                if file_path.suffix in file_extensions and not spec.match_file(relative_file_path):
                    relevant_files.append(file_path)

        relevant_files.sort()

        files_list_file.write_text("\n".join(str(p.relative_to(base_path).as_posix()) for p in relevant_files), encoding='utf-8')

        print(f"Processing {len(relevant_files)} files...")
        with open(files_content_file, 'w', encoding='utf-8') as fc:
            fc.write("================\nFiles\n================\n\n")
            for file_path in relevant_files:
                relative_name = file_path.relative_to(base_path).as_posix()
                fc.write(f"================\nFile: {relative_name}\n================\n")
                try:
                    if file_path.suffix == '.pdf':
                        try:
                            reader = PdfReader(file_path)
                            text = ""
                            for page in reader.pages:
                                text += page.extract_text() or ""
                            fc.write(f"[PDF Content Extracted]\n{text}")
                        except Exception as pdf_e:
                            fc.write(f"[Error reading PDF content: {pdf_e}]")
                    else:
                        fc.write(file_path.read_text(encoding='utf-8', errors='ignore'))
                except Exception as e:
                    fc.write(f"[Error reading content: {e}]")
                fc.write("\n\n")

        print(f"Combining parts into {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(header_file.read_text(encoding='utf-8'))
            output.write("\n\n")
            output.write("================\nDirectory Tree\n================\n\n")
            output.write(structure_file.read_text(encoding='utf-8'))
            output.write("\n\n")
            output.write(files_content_file.read_text(encoding='utf-8'))
            output.write("\n\nList of Included Files\n====================\n")
            output.write(files_list_file.read_text(encoding='utf-8'))
            output.write(f"\n\nSummary: {len(relevant_files)} files included.\n")

    print(f"Codebase summary generated: {output_file}")
    print(f"It contains {len(relevant_files)} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())