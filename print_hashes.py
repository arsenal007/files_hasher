import sqlite3
import argparse
import sys

def print_hashes(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(file_hashes)")
        print("Table info:", cursor.fetchall())
        cursor.execute("SELECT path, hash, size, last_modified FROM file_hashes")
        rows = cursor.fetchall()
        print(f"\nTotal files: {len(rows)}\n")
        for file_path, file_hash, file_size, last_modified in rows:
            print(f"{file_path}\n  hash: {file_hash}\n  size: {file_size}\n  mtime: {last_modified}\n")
    finally:
        conn.close()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Print file hashes from SQLite database")
    parser.add_argument(
        "db_path",
        metavar="DB_PATH",
        help="Path to the SQLite database file (e.g. sftp_file_hashes.db)"
    )
    args = parser.parse_args(argv)
    print_hashes(args.db_path)

if __name__ == "__main__":
    main()
