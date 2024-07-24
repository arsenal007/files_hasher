# File Hasher

File Hasher is a background service that monitors a specified directory for file changes and computes the hashes of all files. It stores these hashes in a SQLite database along with the file paths, sizes, and last modified timestamps. The service runs in the system tray and updates its tooltip with the progress of the file processing.

## Features

- Computes MD5 hashes of all files in a specified directory.
- Monitors the directory for any file changes and updates the database accordingly.
- Stores file paths, sizes, and last modified timestamps in a SQLite database.
- Displays progress in the system tray, including the number of files processed and percentage completion.
- Handles zero-size files and files that encounter read errors, storing them in separate tables.

## Requirements

- Python 3.x
- The following Python packages:
  - tqdm
  - watchdog
  - pystray
  - Pillow
  - sqlite3 (built-in with Python)
  
You can install the required packages using pip:

```sh
pip install tqdm watchdog pystray pillow
```

Run the background hasher:

```sh
python background_hashing.py
```
How to Use

    The service will start and begin hashing all files in the specified directory (WATCH_PATH).
    The progress of the hashing process will be displayed in the system tray tooltip.
    The script will rescan the directory every 5 seconds to capture any new or modified files.

Database Schema

    file_hashes: Stores the path, hash, size, and last modified timestamp of each file.
    zero_size_files: Stores the paths of zero-size files.
    error_files: Stores the paths of files that encountered read errors along with the error messages.

License
