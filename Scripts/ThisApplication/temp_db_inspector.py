import sqlite3
import os

def inspect_db():
    db_path = 'Assets/my_library.db'

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get column names
        cursor.execute("PRAGMA table_info(books)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns in 'books' table: {columns}")

        # Select a few sample books to check FilePath and ThumbnailPath
        cursor.execute("SELECT title, FilePath, ThumbnailPath FROM books LIMIT 5")
        sample_books = cursor.fetchall()

        print("\nSample Book Data (Title, FilePath, ThumbnailPath):")
        for book in sample_books:
            print(book)

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    inspect_db()