#!/usr/bin/env python3
"""
Polymarket Intelligence System - Database Initialization
Creates SQLite database with all required tables
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


def init_database():
    """Initialize the SQLite database with all tables"""
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🗄️  Initializing Polymarket Intelligence Database...")
    print(f"📁 Database path: {os.path.abspath(DB_PATH)}")
    
    # TABLE 1: markets - Stores all Polymarket markets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            polymarket_id TEXT UNIQUE NOT NULL,
            condition_id TEXT,
            slug TEXT,
            question TEXT NOT NULL,
            description TEXT,
            outcomes TEXT,
            outcome_prices TEXT,
            resolution_source TEXT,
            end_date TEXT,
            volume REAL DEFAULT 0,
            volume_24h REAL DEFAULT 0,
            liquidity REAL DEFAULT 0,
            active INTEGER DEFAULT 1,
            closed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Table 'markets' created")
    
    # TABLE 2: tokens - Token IDs for each outcome (YES/NO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            token_id TEXT UNIQUE NOT NULL,
            outcome TEXT,
            price REAL DEFAULT 0,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        )
    ''')
    print("✅ Table 'tokens' created")
    
    # TABLE 3: prices - Historical price snapshots
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            token_id TEXT,
            price REAL,
            bid REAL,
            ask REAL,
            spread REAL,
            volume_24h REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_prices_market_timestamp 
        ON prices(market_id, timestamp DESC)
    ''')
    print("✅ Table 'prices' created")
    
    # TABLE 4: opportunities - Detected trading opportunities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            ai_estimate REAL,
            edge REAL,
            confidence REAL,
            raw_data TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        )
    ''')
    print("✅ Table 'opportunities' created")
    
    # TABLE 5: signals - News/social signals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER,
            source_type TEXT NOT NULL,
            source_name TEXT,
            title TEXT,
            content TEXT,
            url TEXT,
            score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        )
    ''')
    print("✅ Table 'signals' created")
    
    # TABLE 6: moltbook_posts - Track posts to Moltbook
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moltbook_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER,
            moltbook_post_id TEXT,
            submolt TEXT,
            title TEXT,
            content TEXT,
            posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            upvotes INTEGER DEFAULT 0,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )
    ''')
    print("✅ Table 'moltbook_posts' created")
    
    # TABLE 7: system_logs - Activity logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            component TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Table 'system_logs' created")
    
    # TABLE 8: config - Key-value config storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Table 'config' created")
    
    # TABLE 9: prediction_tracking - Accuracy tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            market_id INTEGER NOT NULL,
            polymarket_id TEXT,
            question TEXT,
            signal_type TEXT NOT NULL,
            ai_probability REAL,
            market_price_at_signal REAL,
            edge_at_signal REAL,
            confidence TEXT,
            price_after_1h REAL,
            price_after_6h REAL,
            price_after_24h REAL,
            price_after_48h REAL,
            price_after_7d REAL,
            snapshot_1h_at DATETIME,
            snapshot_6h_at DATETIME,
            snapshot_24h_at DATETIME,
            snapshot_48h_at DATETIME,
            snapshot_7d_at DATETIME,
            final_resolution TEXT,
            resolved_at DATETIME,
            hypothetical_pnl REAL,
            direction_correct INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            market_end_date TEXT,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
            FOREIGN KEY (market_id) REFERENCES markets(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_market ON prediction_tracking(market_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_created ON prediction_tracking(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_signal_type ON prediction_tracking(signal_type)')
    print("✅ Table 'prediction_tracking' created")
    
    # TABLE 10: accuracy_daily - Daily summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accuracy_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_signals INTEGER DEFAULT 0,
            buy_yes_count INTEGER DEFAULT 0,
            buy_no_count INTEGER DEFAULT 0,
            resolved_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            accuracy_pct REAL,
            total_pnl REAL DEFAULT 0,
            avg_edge REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Table 'accuracy_daily' created")
    
    # Insert default config
    default_config = [
        ('last_sync', None),
        ('moltbook_api_key', None),
        ('moltbook_agent_name', None),
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
        default_config
    )
    
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    print("\n" + "="*50)
    print(f"✅ Database initialized successfully!")
    print(f"📊 Total tables: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {table[0]}: {count} rows")
    print("="*50)
    
    conn.close()
    return DB_PATH


if __name__ == '__main__':
    init_database()