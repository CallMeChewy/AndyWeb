import os

def search_files(base_dir, query1, query2, extensions=('.md', '.txtx')):
    matches = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, start=1):
                            if query1.lower() in line.lower() and query2.lower() in line.lower():
                                rel_path = os.path.relpath(path, base_dir)
                                matches.append((rel_path, i, line.strip()))
                except (UnicodeDecodeError, PermissionError) as e:
                    print(f"Skipped {path} due to error: {e}")
    return matches

def main():
    base_dir = os.getcwd()
    query1 = input("Enter the first word or phrase to search for: ").strip()
    query2 = input("Enter the second word or phrase to search for: ").strip()

    if not query1 or not query2:
        print("Both queries must be provided. Exiting.")
        return

    results = search_files(base_dir, query1, query2)
    if results:
        print("\nMatches found (lines containing both phrases):")
        for path, line_num, line in results:
            print(f"{path} (Line {line_num}): {line}")
    else:
        print("No matches found with both phrases in the same line.")

if __name__ == "__main__":
    main()
