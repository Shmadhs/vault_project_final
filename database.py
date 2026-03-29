import sqlite3
import os

DB_NAME = "vault.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_data (
            id INTEGER PRIMARY KEY,
            salt BLOB NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_bundle BLOB NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print(f"SUCCESS: {DB_NAME} initialized")

if __name__ == "__main__":
    init_db()