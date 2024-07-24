
### Comments in the Code

#### `background_hashing.py`

```python
import os
import gc
import threading
import time
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from utils.database import create_database, save_hashes_to_db, save_zero_size_files, save_error_files
from utils.hashing import hash_file

DB_PATH = 'file_hashes.db'
WATCH_PATH = 'E:\\'  # Specify the root directory to watch
BATCH_SIZE = 8192

processed_files_count = 0
total_files_count = 0

def get_folder_size(folder):
    """Calculate the total size of the folder."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def update_tooltip(icon):
    """Update the tooltip of the system tray icon with the progress information."""
    global processed_files_count, total_files_count
    if total_files_count > 0:
        percentage = (processed_files_count / total_files_count) * 100
        icon.title = f"File Hasher: {processed_files_count}/{total_files_count} files processed ({percentage:.2f}%)"
    else:
        icon.title = "File Hasher: Initializing..."

def process_files_batch(files, db_path, icon):
    """Process a batch of files, compute their hashes and update the database."""
    global processed_files_count
    new_hashes = []
    zero_size_files = []
    error_files = []

    for file_path in files:
        if not os.path.exists(file_path):
            continue
        file_size = os.path.getsize(file_path)
        last_modified = os.path.getmtime(file_path)
        if file_size == 0:
            zero_size_files.append((file_path,))
            continue
        file_hash, error = hash_file(file_path)
        if file_hash:
            new_hashes.append((file_path, file_hash, file_size, last_modified))
        else:
            error_files.append((file_path, error))

        processed_files_count += 1
        update_tooltip(icon)

    if new_hashes:
        save_hashes_to_db(new_hashes, db_path)
    if zero_size_files:
        save_zero_size_files(zero_size_files, db_path)
    if error_files:
        save_error_files(error_files, db_path)

def scan_files(root_path, db_path, icon):
    """Scan all files in the root directory and process them in batches."""
    global total_files_count
    files = []
    for root, dirs, filenames in os.walk(root_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))

    total_files_count = len(files)

    file_batches = [files[i:i + BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]

    with tqdm(total=len(files), desc="Hashing files", unit="file") as pbar:
        for batch in file_batches:
            process_files_batch(batch, db_path, icon)
            pbar.update(len(batch))
            gc.collect()  # Explicitly call the garbage collector

class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events to process created or modified files."""
    def __init__(self, db_path, icon):
        self.db_path = db_path
        self.icon = icon

    def on_created(self, event):
        if not event.is_directory:
            process_files_batch([event.src_path], self.db_path, self.icon)

    def on_modified(self, event):
        if not event.is_directory:
            process_files_batch([event.src_path], self.db_path, self.icon)

def background_scan(root_path, db_path, icon):
    """Continuously scan the directory in the background."""
    while True:
        scan_files(root_path, db_path, icon)
        time.sleep(5)  # Repeat every 5 seconds

def start_background_scan(icon):
    """Start the background scanning thread."""
    thread = threading.Thread(target=background_scan, args=(WATCH_PATH, DB_PATH, icon))
    thread.daemon = True
    thread.start()

def on_exit(icon):
    """Stop the icon when exiting."""
    icon.stop()

def create_image():
    """Create an image for the system tray icon."""
    image = Image.new('RGB', (64, 64), 'white')
    dc = ImageDraw.Draw(image)
    dc.rectangle([0, 0, 64, 64], fill="black")
    dc.text((10, 10), "H", fill="white")
    return image

def main():
    """Main function to set up the system tray icon and start the background scan."""
    create_database(DB_PATH)
    icon = Icon("File Hasher", create_image(), "File Hasher", menu=Menu(
        MenuItem('Quit', on_exit)
    ))
    start_background_scan(icon)

    event_handler = FileEventHandler(DB_PATH, icon)
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_PATH, recursive=True)
    observer.start()

    icon.run()

if __name__ == "__main__":
    main()
