


import os
import datetime

def list_files_and_dates():
    """
    Lists all files in the current directory and their last modification dates.
    """
    files_with_dates = []
    for item in os.listdir('.'):
        if os.path.isfile(item):
            try:
                timestamp = os.path.getmtime(item)
                files_with_dates.append((timestamp, item))
            except Exception as e:
                print(f"Warning: Could not retrieve date for {item} ({e})")

    files_with_dates.sort() # Sort by timestamp (oldest first)

    print("Files and their last modification dates in the current directory (oldest first):")
    for timestamp, item in files_with_dates:
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        print(f"- {dt_object.strftime('%Y-%m-%d %H:%M:%S')}: {item}")

if __name__ == "__main__":
    list_files_and_dates()
