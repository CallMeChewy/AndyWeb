import os
import stat
from datetime import datetime
import csv
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern # Corrected import

def get_ignored_patterns(gitignore_path):
    """Reads .gitignore file and returns a PathSpec object."""
    if not os.path.exists(gitignore_path):
        return PathSpec.from_lines(GitWildMatchPattern, [])
    with open(gitignore_path, 'r') as f:
        lines = f.readlines()
    return PathSpec.from_lines(GitWildMatchPattern, lines)

def list_py_files_with_details(root_dir, gitignore_path, output_csv_path, filter_date=None):
    """
    Lists all .py files in root_dir, ignoring files based on .gitignore,
    and includes their size, number of lines, and last modified date.
    Outputs the results to a CSV file with headers.
    Optionally filters by a specific date.
    """
    ignored_spec = get_ignored_patterns(gitignore_path)
    
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write headers
        csv_writer.writerow(["Date Time", "Size (KB)", "Lines", "File Path"])

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Filter out ignored directories first
            # Create a copy of dirnames to modify in place
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
                            mod_date_str = mod_date_obj.strftime('%Y-%m-%d %H:%M')
                            
                            # Count lines in the file
                            line_count = 0
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                for line in f:
                                    line_count += 1

                            # Get relative path from root_dir
                            relative_filepath = os.path.relpath(filepath, root_dir)
                            
                            csv_writer.writerow([mod_date_str, f"{size_kb:.2f}", line_count, relative_filepath])
                        except FileNotFoundError:
                            print(f"Warning: File not found after check: {filepath}")
                        except Exception as e:
                            print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    gitignore_file = os.path.join(current_dir, ".gitignore")
    
    # Get current system date for filtering
    today = datetime.now()
    
    # Generate timestamped output filename
    timestamp = today.strftime("%Y%m%d_%H%M%S")
    output_csv_filename = f"py_files_report_{timestamp}.csv"
    output_csv_path = os.path.join(current_dir, output_csv_filename)
    
    list_py_files_with_details(current_dir, gitignore_file, output_csv_path, filter_date=today)
    print(f"Report generated: {output_csv_path}")
