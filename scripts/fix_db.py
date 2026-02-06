#!/usr/bin/env python3
"""Fix: Add missing columns to database"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(opportunities)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current columns: {columns}")

# Add raw_data column if missing
if 'raw_data' not in columns:
    cursor.execute('ALTER TABLE opportunities ADD COLUMN raw_data TEXT')
    print("  + Added 'raw_data' column")

# Add status default if missing
if 'status' not in columns:
    cursor.execute("ALTER TABLE opportunities ADD COLUMN status TEXT DEFAULT 'active'")
    print("  + Added 'status' column")

conn.commit()
conn.close()
print("\n✅ Database schema updated!")