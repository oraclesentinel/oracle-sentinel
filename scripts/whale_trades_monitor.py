#!/usr/bin/env python3
"""
Whale Trades Monitor - Real-time large trade alerts
Monitors Polymarket Data API for whale trades
Sends Telegram alert for each new large trade (no duplicates)
Now with AI analysis for mega whales ($20K+)
"""

import os
import sys
import sqlite3
import requests
import time
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

# Telegram config
from config_loader import BOT_TOKEN, CHAT_IDS

# Alert thresholds
MIN_TRADE_SIZE_USD = 5000      # $5,000 minimum for alerts
MEGA_WHALE_THRESHOLD = 20000   # $20,000+ triggers AI analysis

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


def analyze_mega_whale(trade: dict) -> dict:
    """
    Run AI analysis for mega whale trades ($20K+)
    Returns analysis dict with AI insights
    """
    try:
        from news_fetcher import NewsFetcher
        from ai_brain import AIBrain
        
        title = trade.get('title', '')
        slug = trade.get('eventSlug', '')
        
        print(f"  🧠 Running AI analysis for mega whale trade...")
        
        # Try to find market in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, question, description, end_date, outcome_prices
            FROM markets 
            WHERE slug = ? OR question LIKE ?
            LIMIT 1
        ''', (slug, f'%{title[:50]}%'))
        market = cursor.fetchone()
        conn.close()
        
        if not market:
            print(f"  ⚠ Market not found in DB, skipping AI analysis")
            return None
            
        market_id, question, description, end_date, outcome_prices = market
        
        # Fetch fresh news
        print(f"  📰 Fetching news...")
        fetcher = NewsFetcher()
        articles = fetcher.fetch_for_market(market_id, question)
        print(f"  Found {len(articles) if articles else 0} articles")
        
        # Run AI analysis
        print(f"  🤖 Running AI brain...")
        brain = AIBrain()
        
        # Parse current price from outcome_prices
        yes_price = 0.5
        try:
            if outcome_prices:
                prices = json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
                if isinstance(prices, list) and len(prices) > 0:
                    yes_price = float(prices[0])
        except:
            pass
        
        result = brain.analyze_market(market_id=market_id)
        
        if result:
            print(f"  ✅ AI Analysis complete: {result.get('recommendation', 'N/A')}")
            return result
        else:
            print(f"  ⚠ AI analysis returned no result")
            return None
            
    except Exception as e:
        print(f"  ❌ AI analysis error: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_trade_alert(trade: dict, ai_analysis: dict = None) -> str:
    """Format single trade alert message with optional AI analysis"""
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

    # Mega whale indicator
    whale_type = "💎 MEGA WHALE" if value_usd >= MEGA_WHALE_THRESHOLD else "🐋 WHALE TRADE"

    lines = [
        f"<b>{whale_type} DETECTED</b>",
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
    ]
    
    # Add AI analysis if available (for mega whales)
    if ai_analysis:
        ai_prob = ai_analysis.get('ai_probability', 0)
        market_price = ai_analysis.get('market_price', 0)
        edge = ai_analysis.get('edge', 0)
        recommendation = ai_analysis.get('recommendation', 'N/A')
        confidence = ai_analysis.get('confidence', 'N/A')
        reasoning = ai_analysis.get('reasoning', '')[:300]
        
        # Recommendation emoji
        if recommendation == 'BUY_YES':
            rec_emoji = "🟢"
        elif recommendation == 'BUY_NO':
            rec_emoji = "🔴"
        else:
            rec_emoji = "⚪"
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🧠 <b>AI ANALYSIS</b>")
        lines.append("")
        lines.append(f"AI Probability: {ai_prob*100:.1f}%")
        lines.append(f"Market Price: {market_price*100:.1f}%")
        lines.append(f"Edge: {edge:+.1f}%")
        lines.append(f"{rec_emoji} Signal: <b>{recommendation}</b> ({confidence})")
        lines.append("")
        lines.append(f"<i>{reasoning}...</i>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")

    lines.append("")
    lines.append(f"🤖 <i>Oracle Sentinel — Whale Intelligence</i>")

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

        # Run AI analysis for mega whales ($20K+)
        ai_analysis = None
        if value_usd >= MEGA_WHALE_THRESHOLD:
            print(f"  💎 MEGA WHALE detected! Running AI analysis...")
            ai_analysis = analyze_mega_whale(trade)
        
        msg = format_trade_alert(trade, ai_analysis)
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
    print(f"   Mega Whale (AI Analysis): ${MEGA_WHALE_THRESHOLD:,}+ trades")
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
    mega_whales = [t for t in trades if calculate_trade_value(t) >= MEGA_WHALE_THRESHOLD]
    print(f"   Whale trades (>=${MIN_TRADE_SIZE_USD:,}): {len(whale_trades)}")
    print(f"   Mega whales (>=${MEGA_WHALE_THRESHOLD:,}): {len(mega_whales)}")

    # Process and alert
    print(f"\n🔍 Processing whale trades...")
    alerts_sent = process_trades(trades)

    print(f"\n{'=' * 60}")
    print(f"✅ Done! Alerts sent: {alerts_sent}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
