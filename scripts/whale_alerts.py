#!/usr/bin/env python3
"""
Whale Alerts - Real-time whale activity monitoring
Runs every 30 minutes via system cron
Sends Telegram alerts when significant whale activity detected
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from whale_tracker import WhaleTracker, get_market_tokens

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

# Telegram config (same as scan_more.py)
from config_loader import BOT_TOKEN, CHAT_IDS

# Alert thresholds
VOLUME_SPIKE_THRESHOLD = 2.0      # 2x daily average
IMBALANCE_THRESHOLD = 0.70        # 70% one-sided
WHALE_ORDERS_THRESHOLD = 3        # 3+ whale orders (>$1K each)
MOMENTUM_THRESHOLD = 5.0          # 5% move in 1 hour
MOMENTUM_6H_THRESHOLD = 10.0      # 10% move in 6 hours


def send_telegram(text):
    """Send alert to all Telegram channels"""
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
            print(f"Telegram send failed: {e}")


def get_top_markets(limit=20):
    """Get top markets by volume"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, question, volume_24h, slug, outcome_prices
        FROM markets
        WHERE active = 1
        ORDER BY volume_24h DESC
        LIMIT ?
    ''', (limit,))
    markets = cursor.fetchall()
    conn.close()
    return markets


def check_whale_alerts(whale_data, question, slug):
    """Check if whale data triggers any alerts"""
    alerts = []
    
    ob_yes = whale_data.get("order_book_yes", {})
    ob_no = whale_data.get("order_book_no", {})
    momentum = whale_data.get("momentum", {})
    volume = whale_data.get("volume", {})
    sentiment = whale_data.get("overall_sentiment", "NEUTRAL")
    
    # Check volume spike
    vol_signal = volume.get("volume_signal", "NORMAL")
    vol_multiplier = volume.get("spike_multiplier", 1.0)
    if vol_signal in ("SPIKE", "EXTREME_SPIKE") and vol_multiplier >= VOLUME_SPIKE_THRESHOLD:
        alerts.append({
            "type": "VOLUME_SPIKE",
            "emoji": "📊",
            "message": f"Volume {vol_multiplier:.1f}x daily average"
        })
    
    # Check order book imbalance (YES token)
    yes_imbalance = ob_yes.get("imbalance_ratio", 0.5)
    if yes_imbalance >= IMBALANCE_THRESHOLD:
        alerts.append({
            "type": "BULLISH_IMBALANCE",
            "emoji": "🟢",
            "message": f"YES book {yes_imbalance:.0%} bid-heavy (buyers dominating)"
        })
    elif yes_imbalance <= (1 - IMBALANCE_THRESHOLD):
        alerts.append({
            "type": "BEARISH_IMBALANCE", 
            "emoji": "🔴",
            "message": f"YES book {1-yes_imbalance:.0%} ask-heavy (sellers dominating)"
        })
    
    # Check whale orders
    whale_bids = ob_yes.get("whale_bids", 0)
    whale_asks = ob_yes.get("whale_asks", 0)
    if whale_bids >= WHALE_ORDERS_THRESHOLD:
        alerts.append({
            "type": "WHALE_BUYING",
            "emoji": "🐋",
            "message": f"{whale_bids} whale buy orders (>$1K each) on YES"
        })
    if whale_asks >= WHALE_ORDERS_THRESHOLD:
        alerts.append({
            "type": "WHALE_SELLING",
            "emoji": "🐋",
            "message": f"{whale_asks} whale sell orders (>$1K each) on YES"
        })
    
    # Check NO token whale activity
    no_whale_bids = ob_no.get("whale_bids", 0)
    if no_whale_bids >= WHALE_ORDERS_THRESHOLD:
        alerts.append({
            "type": "WHALE_BUYING_NO",
            "emoji": "🐋",
            "message": f"{no_whale_bids} whale buy orders on NO token"
        })
    
    # Check price momentum
    change_1h = momentum.get("change_1h", 0)
    change_6h = momentum.get("change_6h", 0)
    if abs(change_1h) >= MOMENTUM_THRESHOLD:
        direction = "📈" if change_1h > 0 else "📉"
        alerts.append({
            "type": "MOMENTUM_1H",
            "emoji": direction,
            "message": f"Price moved {change_1h:+.1f}% in last hour"
        })
    elif abs(change_6h) >= MOMENTUM_6H_THRESHOLD:
        direction = "📈" if change_6h > 0 else "📉"
        alerts.append({
            "type": "MOMENTUM_6H",
            "emoji": direction,
            "message": f"Price moved {change_6h:+.1f}% in last 6 hours"
        })
    
    # Check high volatility
    if momentum.get("volatility") == "HIGH":
        alerts.append({
            "type": "HIGH_VOLATILITY",
            "emoji": "⚡",
            "message": "High price volatility detected"
        })
    
    return alerts, sentiment


def format_alert_message(market_alerts):
    """Format all alerts into a single Telegram message"""
    lines = []
    lines.append("🐋 <b>WHALE ALERT — Oracle Sentinel</b>")
    lines.append(f"⏱ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    
    for market in market_alerts:
        question = market["question"][:50]
        sentiment = market["sentiment"]
        alerts = market["alerts"]
        slug = market["slug"]
        
        # Sentiment emoji
        sent_emoji = "🟢" if sentiment == "BULLISH" else "🔴" if sentiment == "BEARISH" else "⚪"
        
        lines.append(f"<b>{question}...</b>")
        lines.append(f"Sentiment: {sent_emoji} {sentiment}")
        
        for alert in alerts:
            lines.append(f"  {alert['emoji']} {alert['message']}")
        
        lines.append(f"  🔗 polymarket.com/event/{slug}")
        lines.append("")
    
    lines.append("🤖 <i>Oracle Sentinel — Whale Intelligence</i>")
    
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("🐋 Oracle Sentinel - Whale Alerts")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    
    tracker = WhaleTracker()
    markets = get_top_markets(limit=20)
    
    print(f"\nChecking {len(markets)} markets for whale activity...")
    
    all_alerts = []
    
    for market in markets:
        market_id = market["id"]
        question = market["question"]
        slug = market["slug"]
        volume = market["volume_24h"] or 0
        
        print(f"\n  Checking: {question[:45]}...")
        
        # Get token IDs
        tokens = get_market_tokens(market_id)
        if not tokens.get("token_id_yes") or not tokens.get("token_id_no"):
            print("    ⚠ Missing token IDs, skipping")
            continue
        
        # Analyze whale activity
        try:
            whale_data = tracker.analyze_market_whales(
                tokens["token_id_yes"],
                tokens["token_id_no"],
                question,
                tokens.get("condition_id", ""),
                volume
            )
        except Exception as e:
            print(f"    ⚠ Analysis failed: {e}")
            continue
        
        # Check for alerts
        alerts, sentiment = check_whale_alerts(whale_data, question, slug)
        
        if alerts:
            print(f"    🚨 {len(alerts)} alerts detected! Sentiment: {sentiment}")
            for alert in alerts:
                print(f"       {alert['emoji']} {alert['message']}")
            
            all_alerts.append({
                "question": question,
                "slug": slug,
                "sentiment": sentiment,
                "alerts": alerts
            })
        else:
            print(f"    ✓ No significant activity")
    
    # Send Telegram if we have alerts
    print(f"\n{'='*60}")
    if all_alerts:
        print(f"🚨 Total: {len(all_alerts)} markets with whale activity")
        print("\n📱 Sending Telegram alert...")
        
        msg = format_alert_message(all_alerts)
        send_telegram(msg)
        print("   ✅ Alert sent!")
    else:
        print("✅ No significant whale activity detected")
        # Optionally send "all clear" message (commented out to reduce noise)
        # send_telegram("🐋 Whale Check: No significant activity detected")
    
    print(f"\n{'='*60}")
    print("Done!")


if __name__ == '__main__':
    main()