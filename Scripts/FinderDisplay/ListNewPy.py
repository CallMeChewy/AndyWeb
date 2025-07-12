import os
import stat
from datetime import datetime
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern # Corrected import

def get_ignored_patterns(gitignore_path):
    """Reads .gitignore file and returns a PathSpec object."""
    if not os.path.exists(gitignore_path):
        return PathSpec.from_lines(GitWildMatchPattern, [])
    with open(gitignore_path, 'r') as f:
        lines = f.readlines()
    return PathSpec.from_lines(GitWildMatchPattern, lines)

def list_py_files_with_details(root_dir, gitignore_path, filter_date=None):
    """
    Lists all .py files in root_dir, ignoring files based on .gitignore,
    and includes their size and last modified date.
    Optionally filters by a specific date.
    """
    ignored_spec = get_ignored_patterns(gitignore_path)
    
    file_details = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out ignored directories first
        dirnames[:] = [d for d in dirnames if not ignored_spec.match_file(os.path.join(dirpath, d))]

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                # Check if the file itself is ignored
                if not ignored_spec.match_file(filepath):
                    try:
                        file_stat = os.stat(filepath)
                        mod_time = file_stat.st_mtime
                        mod_date_obj = datetime.fromtimestamp(mod_time)
                        
                        if filter_date and mod_date_obj.date() != filter_date.date():
                            continue # Skip if date doesn't match filter

                        size_kb = file_stat.st_size / 1024
                        
                        # Count lines in the file
                        line_count = 0
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                line_count += 1

                        # Get relative path from root_dir
                        relative_filepath = os.path.relpath(filepath, root_dir)
                        
                        file_details.append({
                            'mod_time': mod_time,
                            'size_kb': size_kb,
                            'line_count': line_count,
                            'relative_filepath': relative_filepath,
                            'mod_date_obj': mod_date_obj
                        })
                    except FileNotFoundError:
                        print(f"Warning: File not found after check: {filepath}")
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}")

    # Sort files by modification time (most recent first)
    file_details.sort(key=lambda x: x['mod_time'], reverse=True)

    print("Python Files (excluding .gitignore patterns), sorted by date (most recent first):")
    print("--------------------------------------------------------------------------------")
    for details in file_details:
        mod_date_str = details['mod_date_obj'].strftime('%Y-%m-%d %H:%M')
        print(f"{mod_date_str} {details['size_kb']:.2f} KB {details['line_count']} lines {details['relative_filepath']}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    gitignore_file = os.path.join(current_dir, ".gitignore")
    
    # Get current system date for filtering
    today = datetime.now()
    
    list_py_files_with_details(current_dir, gitignore_file, filter_date=today)
