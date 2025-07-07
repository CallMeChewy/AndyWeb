import sqlite3
import os
import logging
from PIL import Image
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_thumbnails():
    logging.info(f"Current working directory: {os.getcwd()}")
    db_path = 'Assets/my_library.db'
    thumbnails_base_dir = 'Data/Thumbs/'
    books_base_dir = 'Data/Books/'

    if not os.path.exists(db_path):
        logging.error(f"Database file not found at {db_path}")
        return

    os.makedirs(thumbnails_base_dir, exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, FilePath, ThumbnailPath FROM books")
        books = cursor.fetchall()

        logging.info(f"Found {len(books)} books in the database. Generating missing thumbnails...")

        for book_id, title, file_path, thumbnail_path in books:
            if not file_path:
                logging.warning(f"Skipping thumbnail generation for '{title}' due to missing FilePath.")
                continue

            # Construct full paths. Assuming file_path and thumbnail_path are relative to project root.
            # If they are already absolute, os.path.join will handle it correctly.
            full_pdf_path = os.path.join(os.getcwd(), file_path)
            full_thumbnail_path = os.path.join(os.getcwd(), thumbnail_path)

            logging.info(f"Checking PDF: {full_pdf_path}")
            logging.info(f"Checking Thumbnail: {full_thumbnail_path}")

            if not os.path.exists(full_pdf_path):
                logging.warning(f"PDF file not found for '{title}' at {full_pdf_path}. Skipping thumbnail generation.")
                continue

            if os.path.exists(full_thumbnail_path):
                logging.info(f"Thumbnail already exists for '{title}'. Skipping.")
                continue

            try:
                doc = fitz.open(full_pdf_path)
                page = doc.load_page(0)  # Get the first page
                pix = page.get_pixmap() # default resolution
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Resize image to a common thumbnail size (e.g., 164x220 as in BookTile)
                thumbnail_size = (164, 220)
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # Ensure the directory for the thumbnail exists
                os.makedirs(os.path.dirname(full_thumbnail_path), exist_ok=True)
                img.save(full_thumbnail_path, "PNG")
                logging.info(f"Generated thumbnail for '{title}' at {full_thumbnail_path}")

            except Exception as e:
                logging.error(f"Error generating thumbnail for '{title}' ({full_pdf_path}): {e}", exc_info=True)
            finally:
                if 'doc' in locals() and doc:
                    doc.close()

    except (sqlite3.Error, IOError) as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    generate_thumbnails()