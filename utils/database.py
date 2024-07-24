import sqlite3

def create_database(db_path):
    """Create the database and necessary tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS file_hashes (
        path TEXT PRIMARY KEY,
        hash TEXT,
        size INTEGER,
        last_modified INTEGER
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS zero_size_files (
        path TEXT PRIMARY KEY
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS error_files (
        path TEXT PRIMARY KEY,
        error TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_hashes_to_db(hashes, db_path):
    """Save file hashes to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO file_hashes (path, hash, size, last_modified) VALUES (?, ?, ?, ?)", hashes)
    conn.commit()
    conn.close()

def save_zero_size_files(files, db_path):
    """Save zero size files to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO zero_size_files (path) VALUES (?)", files)
    conn.commit()
    conn.close()

def save_error_files(files, db_path):
    """Save files with errors to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO error_files (path, error) VALUES (?, ?)", files)
    conn.commit()
    conn.close()

def get_file_info_from_db(db_path, file_path):
    """Get file information from the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT path, hash, size, last_modified FROM file_hashes WHERE path = ?", (file_path,))
    result = c.fetchone()
    conn.close()
    return result

def get_all_files_from_db(db_path):
    """Get all file paths from the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT path FROM file_hashes")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def delete_nonexistent_files(files, db_path):
    """Delete files from the database that no longer exist on disk."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("DELETE FROM file_hashes WHERE path = ?", [(file,) for file in files])
    conn.commit()
    conn.close()
