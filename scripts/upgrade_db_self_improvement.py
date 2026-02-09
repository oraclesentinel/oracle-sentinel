#!/usr/bin/env python3
"""
Database Upgrade Script for Self-Improvement System
Adds tables and columns needed for agent self-awareness and self-improvement.
Run once to upgrade existing database.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


def log(message):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {message}")


def upgrade_database():
    """Add self-improvement tables and columns to existing database."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    log("Starting database upgrade for self-improvement system...")
    
    # =========================================================
    # 1. Add category column to prediction_tracking
    # =========================================================
    try:
        cursor.execute("ALTER TABLE prediction_tracking ADD COLUMN category TEXT")
        log("✓ Added 'category' column to prediction_tracking")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            log("  'category' column already exists")
        else:
            log(f"  Error: {e}")
    
    # =========================================================
    # 2. Add reasoning_snapshot column to prediction_tracking
    # =========================================================
    try:
        cursor.execute("ALTER TABLE prediction_tracking ADD COLUMN reasoning_snapshot TEXT")
        log("✓ Added 'reasoning_snapshot' column to prediction_tracking")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            log("  'reasoning_snapshot' column already exists")
        else:
            log(f"  Error: {e}")
    
    # =========================================================
    # 3. Create metrics_by_category table
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics_by_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            total_predictions INTEGER DEFAULT 0,
            resolved_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            accuracy_pct REAL,
            avg_edge REAL,
            avg_confidence_correct REAL,
            avg_confidence_wrong REAL,
            total_pnl REAL DEFAULT 0,
            trend TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, category)
        )
    ''')
    log("✓ Created 'metrics_by_category' table")
    
    # =========================================================
    # 4. Create error_analysis table
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            category TEXT,
            predicted_probability REAL,
            actual_outcome INTEGER,
            error_type TEXT,
            error_magnitude REAL,
            possible_causes TEXT,
            reasoning_at_prediction TEXT,
            what_was_missed TEXT,
            lessons_learned TEXT,
            analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prediction_id) REFERENCES prediction_tracking(id)
        )
    ''')
    log("✓ Created 'error_analysis' table")
    
    # =========================================================
    # 5. Create self_improvement_log table
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS self_improvement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diagnosis_type TEXT NOT NULL,
            diagnosis_detail TEXT,
            category_affected TEXT,
            proposed_fix TEXT,
            fix_type TEXT,
            backtest_before REAL,
            backtest_after REAL,
            improvement_pct REAL,
            status TEXT DEFAULT 'proposed',
            applied_at DATETIME,
            result_after_apply TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    log("✓ Created 'self_improvement_log' table")
    
    # =========================================================
    # 6. Create agent_metrics table (overall performance tracking)
    # =========================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_predictions INTEGER DEFAULT 0,
            total_resolved INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            overall_accuracy REAL,
            accuracy_trend TEXT,
            best_category TEXT,
            worst_category TEXT,
            overconfidence_score REAL,
            underconfidence_score REAL,
            brier_score REAL,
            total_api_cost REAL DEFAULT 0,
            avg_cost_per_prediction REAL,
            self_improvements_applied INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    log("✓ Created 'agent_metrics' table")
    
    # =========================================================
    # 7. Create indexes for performance
    # =========================================================
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_category ON prediction_tracking(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_category_date ON metrics_by_category(category, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_category ON error_analysis(category)')
    log("✓ Created indexes")
    
    conn.commit()
    conn.close()
    
    log("")
    log("=" * 50)
    log("Database upgrade complete!")
    log("New tables: metrics_by_category, error_analysis, self_improvement_log, agent_metrics")
    log("New columns: prediction_tracking.category, prediction_tracking.reasoning_snapshot")
    log("=" * 50)


if __name__ == "__main__":
    upgrade_database()
