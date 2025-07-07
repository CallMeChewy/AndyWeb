#!/usr/bin/env python3
"""
File: VerifyIgnore.py
Description: A script to visualize the project structure while respecting all .gitignore rules.
"""

import os
from pathlib import Path
import fnmatch
import tempfile

# --- Reusing the robust .gitignore parsing logic ---

def parse_gitignore(gitignore_path):
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
    path_abs = Path(path).resolve()

    try:
        relative_path_str = path_abs.relative_to(base_path).as_posix()
    except ValueError:
        print(f"DEBUG: Path {path_abs} is outside base_path {base_path}. Ignoring.")
        return True # Path is outside the base_path, so ignore it for this visualization

    is_dir = path_abs.is_dir()

    print(f"DEBUG: Checking path: {relative_path_str} (is_dir: {is_dir})")

    # Check parent directories for exclusion
    parent = path_abs.parent
    if parent != base_path and parent.is_relative_to(base_path):
         if is_path_ignored(parent, patterns, base_path):
            is_reincluded = False
            for p_info in patterns:
                if p_info['negation'] and path_matches_pattern(relative_path_str, p_info['pattern'], is_dir):
                    is_reincluded = True
                    print(f"DEBUG:   Path {relative_path_str} re-included by negation pattern: {p_info['pattern']}")
                    break
            if not is_reincluded:
                print(f"DEBUG:   Parent {parent} is ignored and {relative_path_str} not re-included. Ignoring.")
                return True

    last_match = None
    for p_info in patterns:
        print(f"DEBUG:   Testing pattern: {p_info['pattern']} (negation: {p_info['negation']}) against {relative_path_str}")

        # Special handling for patterns like 'dir/*' or '**/dir/*'
        # These patterns should ignore contents, but NOT the directory itself.
        if p_info['pattern'].endswith('/*'):
            # Extract the directory name from the pattern (e.g., 'Books' from '**/Books/*')
            # This handles cases like 'dir/*' and '**/dir/*' correctly.
            pattern_parts = p_info['pattern'].split('/')
            pattern_dir_name = pattern_parts[-2] if len(pattern_parts) > 1 else None

            # If the current path is a directory AND its name matches the pattern's directory name,
            # then this specific '/*'-ending pattern should NOT apply to the directory itself.
            if is_dir and pattern_dir_name and Path(relative_path_str).name == pattern_dir_name:
                print(f"DEBUG:     Skipping '/*'-ending pattern {p_info['pattern']} for directory {relative_path_str}")
                continue # Skip this pattern for the directory itself

        if path_matches_pattern(relative_path_str, p_info['pattern'], is_dir):
            last_match = p_info
            print(f"DEBUG:     MATCH! Last match updated to: {p_info}")

    if last_match:
        result = not last_match['negation']
        print(f"DEBUG: Final decision for {relative_path_str}: {result} (matched by {last_match})")
        return result

    print(f"DEBUG: Final decision for {relative_path_str}: False (no match)")
    return False

def generate_tree_output(start_path, patterns, base_path, prefix="", output_lines=None):
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

        # Check if the item itself should be ignored
        should_ignore_item = is_path_ignored(item_path, patterns, base_path)
        print(f"DEBUG:   Item {item_path.relative_to(base_path).as_posix()} should_ignore_item: {should_ignore_item}")

        if not should_ignore_item:
            output_lines.append(f"{prefix}{pointer}{item}")
            if item_path.is_dir():
                extension = '│   ' if i < len(all_entries) - 1 else '    '
                generate_tree_output(item_path, patterns, base_path, prefix=prefix + extension, output_lines=output_lines)
    return output_lines

def main():
    """Main entry point"""
    base_path = Path('.').resolve()
    gitignore_path = base_path / '.gitignore'
    patterns = parse_gitignore(gitignore_path)
    patterns.append({'pattern': '.git/', 'negation': False}) # Always ignore .git
    patterns.append({'pattern': '..Excclude/', 'negation': False}) # Explicitly ignore ..Excclude/

    print(f"Generating gitignore-aware tree view...")
    tree_lines = [f". ({base_path.name})"]
    tree_lines.extend(generate_tree_output(base_path, patterns, base_path))

    output_filename = "gitignore_tree_view.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(tree_lines))
    
    print(f"Full gitignore-aware tree view written to: {output_filename}")

if __name__ == "__main__":
    main()