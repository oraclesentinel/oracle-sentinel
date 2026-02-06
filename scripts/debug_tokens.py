#!/usr/bin/env python3
"""Debug: Check token IDs in database"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== TOKENS TABLE ===")
cursor.execute('SELECT COUNT(*) FROM tokens')
print(f"Total tokens: {cursor.fetchone()[0]}")

cursor.execute('SELECT id, market_id, token_id, outcome, price FROM tokens LIMIT 10')
rows = cursor.fetchall()

for row in rows:
    tid = row[2] if row[2] else "NULL"
    tid_len = len(tid) if tid else 0
    print(f"  ID:{row[0]} | Market:{row[1]} | Outcome:{row[3]} | Price:{row[4]}")
    print(f"    Token({tid_len} chars): {tid[:50]}...")

print("\n=== RAW MARKET DATA (first market) ===")
cursor.execute('SELECT polymarket_id, question, outcomes, outcome_prices FROM markets LIMIT 1')
row = cursor.fetchone()
if row:
    print(f"  ID: {row[0]}")
    print(f"  Question: {row[1]}")
    print(f"  Outcomes: {row[2]}")
    print(f"  Prices: {row[3]}")

conn.close()