import sqlite3
import os
from datetime import datetime

DATABASE = os.getenv('DB_PATH', 'key_checkout.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with our tables (fresh install)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Key fobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_fobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fob_id TEXT UNIQUE NOT NULL,
            vehicle_name TEXT NOT NULL,
	    category TEXT DEFAULT 'Vehicle',	
            location TEXT DEFAULT 'Shop',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Checkouts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fob_id INTEGER NOT NULL,
            checked_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checked_in_at TIMESTAMP NULL,
            kiosk_id TEXT DEFAULT 'kiosk1',
            property_note TEXT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (fob_id) REFERENCES key_fobs(id)
        )
    ''')
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create reservations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fob_id INTEGER NOT NULL,
            user_id INTEGER,
            reserved_for_name TEXT,
            reserved_datetime TEXT NOT NULL,
            display_hours_before INTEGER DEFAULT 24,
            reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            FOREIGN KEY (fob_id) REFERENCES key_fobs (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Create notes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fob_id INTEGER NOT NULL UNIQUE,
            note_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            expires_at TEXT NULL,
            FOREIGN KEY (fob_id) REFERENCES key_fobs (id)
        )
    ''')

    # Stock items catalog - covers both warehouse "Stock Parts" (smoke detectors,
    # locks, light switches, etc.) and "Cut Keys" blanks. Both are identified by
    # a scanned barcode/QR code and are NOT a traditional checkout/checkin item -
    # they get logged as consumed/used against a property, not checked back in
    # to a person (stock parts CAN be logged back in as unused-and-returned).
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'stock_part',
            on_hand_qty INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Stock movement log - one row per scanned item per session. Used for both
    # Stock Parts Out/In and Cut Keys. session_id groups everything scanned
    # together in one kiosk trip (one fob scan + one property note covering
    # possibly multiple items), for reporting.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            property_note TEXT NOT NULL,
            kiosk_id TEXT DEFAULT 'kiosk1',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES stock_items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

    # Also run migrations, so `python database.py` is safe to re-run on an
    # existing install and will pick up any columns added after initial setup.
    migrate_db()


def _column_exists(conn, table, column):
    cols = conn.execute(f'PRAGMA table_info({table})').fetchall()
    return any(c['name'] == column for c in cols)


def migrate_db():
    """
    Safe, idempotent migration for EXISTING databases that were created
    before the property_note / expires_at / stock tables existed.
    Safe to call every time the app starts.
    """
    conn = get_db()
    try:
        # notes.expires_at was referenced by app.py's note code but was
        # missing from the original schema - this was causing note saves
        # to fail with "no such column: expires_at".
        if not _column_exists(conn, 'notes', 'expires_at'):
            conn.execute('ALTER TABLE notes ADD COLUMN expires_at TEXT NULL')
            print("Migration: added notes.expires_at")

        # checkouts.property_note - required free-text "which property is
        # this going to" field for Rentables and Lock Box checkouts.
        if not _column_exists(conn, 'checkouts', 'property_note'):
            conn.execute('ALTER TABLE checkouts ADD COLUMN property_note TEXT NULL')
            print("Migration: added checkouts.property_note")

        # New tables for Stock Parts / Cut Keys - safe no-op if they already exist.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                item_type TEXT NOT NULL DEFAULT 'stock_part',
                on_hand_qty INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                property_note TEXT NOT NULL,
                kiosk_id TEXT DEFAULT 'kiosk1',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES stock_items (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
