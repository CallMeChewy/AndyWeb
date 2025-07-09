import shutil
import datetime
import os

def create_backup():
    # Define source directories relative to the script's location
    source_dirs = [
        'Data/Databases',
        'Source',
        'Tests',
        'WebPages'
    ]

    # Files to include from the base directory
    base_files_to_include = [
        '.py',
        '.html'
    ]

    # Get current timestamp for the backup folder name
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_base_dir = 'TempBU'
    destination_dir = os.path.join(backup_base_dir, f'BU_{timestamp}')

    print(f"Creating backup in: {destination_dir}")

    try:
        # Create the destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)

        # Copy specified directories
        for src_dir in source_dirs:
            full_source_path = os.path.join(os.getcwd(), src_dir)
            full_destination_path = os.path.join(destination_dir, src_dir)

            if os.path.exists(full_source_path):
                print(f"Copying directory '{src_dir}' to '{full_destination_path}'...")
                shutil.copytree(full_source_path, full_destination_path, dirs_exist_ok=True, copy_function=shutil.copy2)
                print(f"Successfully copied directory '{src_dir}'.")
            else:
                print(f"Warning: Source directory '{src_dir}' not found. Skipping.")

        # Copy specified files from the base directory
        print("Copying specified files from base directory...")
        for item in os.listdir(os.getcwd()):
            item_path = os.path.join(os.getcwd(), item)
            if os.path.isfile(item_path):
                for ext in base_files_to_include:
                    if item.endswith(ext):
                        dest_file_path = os.path.join(destination_dir, item)
                        print(f"Copying file '{item}' to '{dest_file_path}'...")
                        shutil.copy2(item_path, dest_file_path)
                        print(f"Successfully copied file '{item}'.")
                        break # Move to the next item after first match

        print("Backup completed successfully!")

    except Exception as e:
        print(f"An error occurred during backup: {e}")

if __name__ == "__main__":
    create_backup()
