#!/usr/bin/env python3
"""
Whale Trades Monitor - Real-time large trade alerts
Monitors Polymarket Data API for whale trades
Sends Telegram alert for each new large trade (no duplicates)
"""

import os
import sys
import sqlite3
import requests
import time
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

# Telegram config
from config_loader import BOT_TOKEN, CHAT_IDS

# Alert threshold - minimum trade size in USD
MIN_TRADE_SIZE_USD = 5000  # $1,000 minimum

# Data API
DATA_API_BASE = "https://data-api.polymarket.com"


def init_db():
    """Create table for tracking alerted trades"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whale_trades_alerted (
            tx_hash TEXT PRIMARY KEY,
            market_title TEXT,
            trade_size REAL,
            trade_side TEXT,
            outcome TEXT,
            price REAL,
            trader_name TEXT,
            alerted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def is_already_alerted(tx_hash: str) -> bool:
    """Check if this TX has already been alerted"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM whale_trades_alerted WHERE tx_hash = ?', (tx_hash,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def mark_as_alerted(trade: dict):
    """Mark this TX as alerted to prevent duplicates"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO whale_trades_alerted 
        (tx_hash, market_title, trade_size, trade_side, outcome, price, trader_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        trade['transactionHash'],
        trade.get('title', '')[:200],
        trade.get('size', 0) * trade.get('price', 0),
        trade.get('side', ''),
        trade.get('outcome', ''),
        trade.get('price', 0),
        trade.get('name', trade.get('pseudonym', 'Anonymous'))
    ))
    conn.commit()
    conn.close()


def send_telegram(text: str):
    """Send alert to Telegram"""
    for chat_id in CHAT_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
        except Exception as e:
            print(f"Telegram error: {e}")


def fetch_recent_trades(limit: int = 50) -> list:
    """Fetch recent trades from Polymarket Data API"""
    try:
        resp = requests.get(
            f"{DATA_API_BASE}/trades",
            params={"limit": limit},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"API error: {resp.status_code}")
            return []
    except Exception as e:
        print(f"Fetch error: {e}")
        return []


def calculate_trade_value(trade: dict) -> float:
    """Calculate trade value in USD"""
    size = float(trade.get('size', 0))
    price = float(trade.get('price', 0))
    return size * price


def format_trade_alert(trade: dict) -> str:
    """Format single trade alert message"""
    title = trade.get('title', 'Unknown Market')[:60]
    side = trade.get('side', 'UNKNOWN')
    outcome = trade.get('outcome', '?')
    size = float(trade.get('size', 0))
    price = float(trade.get('price', 0))
    value_usd = size * price
    tx_hash = trade.get('transactionHash', '')
    trader = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    slug = trade.get('eventSlug', '')
    
    # Emoji based on side
    if side == 'BUY':
        emoji = "🟢"
        action = "bought"
    else:
        emoji = "🔴"
        action = "sold"
    
    # Format timestamp
    ts = trade.get('timestamp', 0)
    if ts:
        trade_time = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%H:%M:%S UTC')
    else:
        trade_time = "now"
    
    lines = [
        f"🐋 <b>WHALE TRADE DETECTED</b>",
        f"",
        f"<b>{title}...</b>",
        f"",
        f"{emoji} <b>{trader}</b> {action} <b>{outcome}</b>",
        f"",
        f"Size: {size:,.0f} shares",
        f"Price: ${price:.3f} ({price*100:.1f}%)",
        f"Value: <b>${value_usd:,.0f}</b>",
        f"Time: {trade_time}",
        f"",
        f"Market: polymarket.com/event/{slug}",
        f"TX: polygonscan.com/tx/{tx_hash}",
        f"",
        f"🤖 <i>Oracle Sentinel — Whale Intelligence</i>"
    ]
    
    return "\n".join(lines)


def process_trades(trades: list) -> int:
    """Process trades and send alerts for new whales"""
    alerts_sent = 0
    
    for trade in trades:
        tx_hash = trade.get('transactionHash', '')
        if not tx_hash:
            continue
        
        # Calculate trade value
        value_usd = calculate_trade_value(trade)
        
        # Skip small trades
        if value_usd < MIN_TRADE_SIZE_USD:
            continue
        
        # Check if already alerted
        if is_already_alerted(tx_hash):
            continue
        
        # New whale trade! Send alert
        print(f"  🐋 New whale: ${value_usd:,.0f} - {trade.get('title', '')[:40]}...")
        
        msg = format_trade_alert(trade)
        send_telegram(msg)
        
        # Mark as alerted
        mark_as_alerted(trade)
        alerts_sent += 1
        
        # Small delay between alerts to avoid spam
        time.sleep(1)
    
    return alerts_sent


def cleanup_old_records(days: int = 7):
    """Remove old alerted records to keep DB clean"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM whale_trades_alerted 
        WHERE alerted_at < datetime('now', ?)
    ''', (f'-{days} days',))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def main():
    print("=" * 60)
    print("🐋 Oracle Sentinel - Whale Trades Monitor")
    print(f"   Threshold: ${MIN_TRADE_SIZE_USD:,}+ trades")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Cleanup old records
    deleted = cleanup_old_records(days=7)
    if deleted:
        print(f"\n🧹 Cleaned up {deleted} old records")
    
    # Fetch recent trades
    print(f"\n📡 Fetching recent trades...")
    trades = fetch_recent_trades(limit=100)
    print(f"   Found {len(trades)} recent trades")
    
    # Filter and count whale trades
    whale_trades = [t for t in trades if calculate_trade_value(t) >= MIN_TRADE_SIZE_USD]
    print(f"   Whale trades (>=${MIN_TRADE_SIZE_USD:,}): {len(whale_trades)}")
    
    # Process and alert
    print(f"\n🔍 Processing whale trades...")
    alerts_sent = process_trades(trades)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Done! Alerts sent: {alerts_sent}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()