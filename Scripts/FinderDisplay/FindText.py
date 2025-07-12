import os

def search_files(base_dir, query, extensions=('.md', '.txt')):
    matches = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, start=1):
                            if query.lower() in line.lower():
                                rel_path = os.path.relpath(path, base_dir)
                                matches.append((rel_path, i, line.strip()))
                except (UnicodeDecodeError, PermissionError) as e:
                    print(f"Skipped {path} due to error: {e}")
    return matches

def main():
    base_dir = os.getcwd()
    query = input("Enter a word or sentence to search for: ").strip()
    if not query:
        print("No query entered. Exiting.")
        return

    results = search_files(base_dir, query)
    if results:
        print("\nMatches found:")
        for path, line_num, line in results:
            print(f"{path} (Line {line_num}): {line}")
    else:
        print("No matches found.")

if __name__ == "__main__":
    main()
