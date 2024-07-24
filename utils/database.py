import sqlite3

DB_PATH = 'file_hashes.db'

def create_database(db_path=DB_PATH):
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS file_hashes (
        id INTEGER PRIMARY KEY,
        path TEXT NOT NULL,
        hash TEXT NOT NULL,
        size INTEGER NOT NULL,
        last_modified TIMESTAMP NOT NULL,
        UNIQUE(path)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS zero_size_files (
        id INTEGER PRIMARY KEY,
        path TEXT NOT NULL,
        UNIQUE(path)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS error_files (
        id INTEGER PRIMARY KEY,
        path TEXT NOT NULL,
        error TEXT NOT NULL,
        UNIQUE(path)
    )
    ''')
    conn.commit()
    conn.close()

def save_hashes_to_db(hashes, db_path=DB_PATH):
    """Save file hashes to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO file_hashes (path, hash, size, last_modified) VALUES (?, ?, ?, ?)", hashes)
    conn.commit()
    conn.close()

def save_zero_size_files(zero_size_files, db_path=DB_PATH):
    """Save zero-size files to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO zero_size_files (path) VALUES (?)", zero_size_files)
    conn.commit()
    conn.close()

def save_error_files(error_files, db_path=DB_PATH):
    """Save error files to the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("INSERT OR REPLACE INTO error_files (path, error) VALUES (?, ?)", error_files)
    conn.commit()
    conn.close()
