"""
database.py
Handles all SQLite database setup and connections for the
AI Face Recognition & Smart Attendance System.
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def get_db():
    """Return a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def add_column_if_missing(conn, table, column_def):
    column_name = column_def.split()[0]
    if not column_exists(conn, table, column_name):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def init_db():
    """Create all tables if they do not already exist, and seed defaults."""
    conn = get_db()
    cur = conn.cursor()

    # --- Admin users --------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- Registered people ---------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            person_code TEXT,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            email TEXT,
            department TEXT,
            role TEXT,
            address TEXT,
            dob TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'Active',
            consent_given INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            last_seen TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    add_column_if_missing(conn, 'persons', 'user_id INTEGER NOT NULL DEFAULT 1')
    add_column_if_missing(conn, 'persons', 'person_code TEXT')

    # --- Face encodings (multiple samples per person) -------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS face_encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            encoding BLOB NOT NULL,
            quality REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
        )
    """)

    # --- Attendance -------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
            UNIQUE(person_id, date)
        )
    """)

    # --- Recognition history (every event, known or unknown) -----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recognition_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            person_id INTEGER,
            person_name TEXT,
            confidence REAL,
            recognized_at TEXT DEFAULT (datetime('now')),
            is_known INTEGER DEFAULT 1,
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    add_column_if_missing(conn, 'recognition_history', 'user_id INTEGER NOT NULL DEFAULT 1')

    # --- Unknown faces ------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS unknown_faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            snapshot_path TEXT,
            confidence REAL,
            detection_count INTEGER DEFAULT 1,
            first_seen TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now')),
            encoding BLOB,
            resolved INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    add_column_if_missing(conn, 'unknown_faces', 'user_id INTEGER NOT NULL DEFAULT 1')

    # --- Settings (key/value) -------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()

    # Seed default admin user (demo credentials — see README)
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "Admin"),
        )

    # Seed default settings
    defaults = {
        "recognition_threshold": "0.55",   # face_recognition "tolerance"-like score
        "detection_sensitivity": "0.5",
        "camera_device": "0",
        "resolution": "640x480",
        "fps": "15",
        "session_timeout": "30",
        "unknown_cooldown_seconds": "30",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row is None:
        return default
    return row["value"]


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str():
    return datetime.now().strftime("%H:%M:%S")
