#!/usr/bin/env python3
import sqlite3
import sys

def get_stats(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Try to read total_files from meta
    total = None
    try:
        c.execute("SELECT value FROM meta WHERE key = 'total_files'")
        row = c.fetchone()
        if row and str(row[0]).isdigit():
            total = int(row[0])
    except sqlite3.OperationalError:
        pass  # table meta does not exist yet

    # Count hashed files
    hashed = None
    try:
        c.execute("SELECT COUNT(*) FROM file_hashes")
        hashed = c.fetchone()[0]
    except sqlite3.OperationalError:
        pass  # table file_hashes does not exist yet

    conn.close()
    return total, hashed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: stats.py <db_path>")
        sys.exit(1)

    db_path = sys.argv[1]
    total, hashed = get_stats(db_path)

    print("=== File Hashing Stats ===")
    print(f"Database: {db_path}")

    if total is None:
        print("⚠️  No snapshot of total files in DB (meta table missing or empty).")
    else:
        print(f"Total files (snapshot): {total}")

    if hashed is None:
        print("⚠️  No file_hashes table yet — no files processed.")
    else:
        print(f"Hashed files: {hashed}")
        if total:
            left = max(total - hashed, 0)
            percent = hashed / total * 100
            print(f"Remaining: {left}")
            print(f"Progress: {percent:.2f}%")
