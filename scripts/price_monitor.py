#!/usr/bin/env python3
"""
Price Monitor - Real-time position monitoring system
Runs every 15 minutes via cron

Features:
1. Batch fetch prices dari Polymarket
2. Calculate P&L untuk setiap position
3. Check multiple trigger conditions
4. Send alerts via Telegram
"""

import os
import sys
import json
import sqlite3
import requests
from jupiter_prediction_client import JupiterPredictionClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'price_monitor.log')

# Telegram Config
try:
    from config_loader import BOT_TOKEN, CHAT_IDS
except:
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_IDS = [os.getenv('TELEGRAM_CHAT_ID')] if os.getenv('TELEGRAM_CHAT_ID') else []

# =========================================================
# TRIGGER THRESHOLDS
# =========================================================
TRIGGERS = {
    'PRICE_SPIKE': 0.15,        # Alert if price changes 15% from entry
    'EXTREME_HIGH': 0.85,       # Alert if price > 85%
    'EXTREME_LOW': 0.15,        # Alert if price < 15%
    'TAKE_PROFIT_PNL': 50,      # Suggest take profit if P&L >= 50%
    'CUT_LOSS_PNL': -30,        # Suggest cut loss if P&L <= -30%
    'WARNING_PNL': -20,         # Warning if P&L <= -20%
}

# Time-based triggers (hours before close)
TIME_TRIGGERS = {
    'T_MINUS_24H': 24,
    'T_MINUS_6H': 6,
    'T_MINUS_1H': 1,
}


def log(message: str):
    """Log to file and stdout"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {message}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a') as f:
            f.write(line + '\n')
    except:
        pass


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def send_telegram(text: str):
    """Send alert to Telegram"""
    if not BOT_TOKEN or not CHAT_IDS:
        log("  ⚠ Telegram not configured")
        return False
    
    for chat_id in CHAT_IDS:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            if response.ok:
                log(f"  📱 Telegram sent to {chat_id}")
                return True
            else:
                log(f"  ⚠ Telegram failed: {response.text[:100]}")
        except Exception as e:
            log(f"  ⚠ Telegram error: {e}")
    return False


# =========================================================
# JUPITER API
# =========================================================
def fetch_market_price(market_id: str) -> float:
    """Fetch current price from Jupiter Prediction API"""
    if not market_id:
        return None
    try:
        jupiter = JupiterPredictionClient()
        market = jupiter.get_market_by_id(market_id)
        
        if market:
            pricing = market.get('pricing', {})
            yes_price = (pricing.get('buyYesPriceUsd', 0) or 0) / 1_000_000
            log(f"  📊 Fetched {market_id}: {yes_price*100:.1f}¢")
            return yes_price
    except Exception as e:
        log(f"  ⚠ Jupiter API error for {market_id}: {e}")
    return None

def fetch_prices_batch(positions: list) -> dict:
    """Fetch prices for multiple positions"""
    prices = {}
    
    for pos in positions:
        pid = pos['polymarket_id']
        if pid:
            price = fetch_market_price(pid)
            if price is not None:
                prices[pos['id']] = price
                log(f"  📊 {pos['question'][:30]}... = {price*100:.1f}¢")
            else:
                # Fallback to entry price
                prices[pos['id']] = pos.get('market_price_at_signal')
        
    return prices


# =========================================================
# P&L CALCULATION
# =========================================================
def calculate_pnl(entry_price: float, current_price: float, direction: str) -> float:
    """Calculate P&L percentage"""
    if not entry_price or entry_price == 0:
        return 0
    
    if direction == 'BUY_YES':
        return ((current_price - entry_price) / entry_price) * 100
    else:  # BUY_NO
        entry_no = 1 - entry_price
        current_no = 1 - current_price
        if entry_no > 0:
            return ((current_no - entry_no) / entry_no) * 100
    return 0


def get_hours_to_close(end_date_str: str) -> float:
    """Calculate hours until market close"""
    if not end_date_str:
        return 999
    
    try:
        if 'T' in end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = datetime.fromisoformat(end_date_str + 'T23:59:59+00:00')
        
        now = datetime.now(timezone.utc)
        delta = end_date - now
        return delta.total_seconds() / 3600
    except:
        return 999


# =========================================================
# TRIGGER DETECTION
# =========================================================
def check_triggers(position: dict, current_price: float) -> list:
    """Check all trigger conditions for a position"""
    alerts = []
    
    entry_price = position['market_price_at_signal']
    direction = position['signal_type']
    pnl = calculate_pnl(entry_price, current_price, direction)
    hours_to_close = get_hours_to_close(position.get('market_end_date'))
    alerts_sent = json.loads(position.get('alerts_sent') or '[]')
    
    price_change_pct = abs(current_price - entry_price) / entry_price * 100 if entry_price else 0
    
    # ─────────────────────────────────────────────
    # PRICE-BASED TRIGGERS
    # ─────────────────────────────────────────────
    
    # Extreme high price
    if current_price >= TRIGGERS['EXTREME_HIGH']:
        if direction == 'BUY_YES' and 'EXTREME_HIGH_WIN' not in alerts_sent:
            alerts.append({
                'type': 'EXTREME_HIGH_WIN',
                'urgency': 'high',
                'action': 'TAKE_PROFIT',
                'message': f'🎯 Price at {current_price*100:.0f}¢ - strongly in your favor!',
                'pnl': pnl
            })
        elif direction == 'BUY_NO' and 'EXTREME_HIGH_LOSS' not in alerts_sent:
            alerts.append({
                'type': 'EXTREME_HIGH_LOSS',
                'urgency': 'high',
                'action': 'CUT_LOSS',
                'message': f'⚠️ Price at {current_price*100:.0f}¢ - strongly against your NO position!',
                'pnl': pnl
            })
    
    # Extreme low price
    if current_price <= TRIGGERS['EXTREME_LOW']:
        if direction == 'BUY_NO' and 'EXTREME_LOW_WIN' not in alerts_sent:
            alerts.append({
                'type': 'EXTREME_LOW_WIN',
                'urgency': 'high',
                'action': 'TAKE_PROFIT',
                'message': f'🎯 Price at {current_price*100:.0f}¢ - strongly in your favor!',
                'pnl': pnl
            })
        elif direction == 'BUY_YES' and 'EXTREME_LOW_LOSS' not in alerts_sent:
            alerts.append({
                'type': 'EXTREME_LOW_LOSS',
                'urgency': 'high',
                'action': 'CUT_LOSS',
                'message': f'⚠️ Price at {current_price*100:.0f}¢ - strongly against your YES position!',
                'pnl': pnl
            })
    
    # Price spike (15% change from entry)
    if price_change_pct >= TRIGGERS['PRICE_SPIKE'] * 100 and 'PRICE_SPIKE' not in alerts_sent:
        alerts.append({
            'type': 'PRICE_SPIKE',
            'urgency': 'medium',
            'action': 'REVIEW',
            'message': f'📈 Price moved {price_change_pct:.1f}% since entry!',
            'pnl': pnl
        })
    
    # ─────────────────────────────────────────────
    # P&L-BASED TRIGGERS
    # ─────────────────────────────────────────────
    
    if pnl >= TRIGGERS['TAKE_PROFIT_PNL'] and 'TAKE_PROFIT' not in alerts_sent:
        alerts.append({
            'type': 'TAKE_PROFIT',
            'urgency': 'medium',
            'action': 'TAKE_PROFIT',
            'message': f'💰 Position up {pnl:.1f}%! Consider taking profit.',
            'pnl': pnl
        })
    
    if pnl <= TRIGGERS['CUT_LOSS_PNL'] and 'CUT_LOSS' not in alerts_sent:
        alerts.append({
            'type': 'CUT_LOSS',
            'urgency': 'high',
            'action': 'CUT_LOSS',
            'message': f'🔴 Position down {pnl:.1f}%! Consider cutting loss.',
            'pnl': pnl
        })
    elif pnl <= TRIGGERS['WARNING_PNL'] and 'WARNING' not in alerts_sent:
        alerts.append({
            'type': 'WARNING',
            'urgency': 'medium',
            'action': 'MONITOR',
            'message': f'⚠️ Position down {pnl:.1f}%. Monitor closely.',
            'pnl': pnl
        })
    
    # ─────────────────────────────────────────────
    # TIME-BASED TRIGGERS
    # ─────────────────────────────────────────────
    
    if hours_to_close <= TIME_TRIGGERS['T_MINUS_1H'] and 'T_MINUS_1H' not in alerts_sent:
        alerts.append({
            'type': 'T_MINUS_1H',
            'urgency': 'high',
            'action': 'FINAL_DECISION',
            'message': f'⏰ Market closes in {hours_to_close:.1f} hours! Final decision time.',
            'pnl': pnl
        })
    elif hours_to_close <= TIME_TRIGGERS['T_MINUS_6H'] and 'T_MINUS_6H' not in alerts_sent:
        alerts.append({
            'type': 'T_MINUS_6H',
            'urgency': 'medium',
            'action': 'REVIEW',
            'message': f'⏰ Market closes in {hours_to_close:.1f} hours. Review position.',
            'pnl': pnl
        })
    elif hours_to_close <= TIME_TRIGGERS['T_MINUS_24H'] and 'T_MINUS_24H' not in alerts_sent:
        alerts.append({
            'type': 'T_MINUS_24H',
            'urgency': 'low',
            'action': 'REVIEW',
            'message': f'📅 Market closes in {hours_to_close:.0f} hours.',
            'pnl': pnl
        })
    
    return alerts


# =========================================================
# ALERT PROCESSING
# =========================================================
def format_alert_message(position: dict, alert: dict, current_price: float) -> str:
    """Format alert for Telegram"""
    
    action = alert['action']
    urgency = alert['urgency']
    pnl = alert.get('pnl', 0)
    
    # Emoji based on action
    if action == 'TAKE_PROFIT':
        emoji = "💰"
        title = "TAKE PROFIT OPPORTUNITY"
    elif action == 'CUT_LOSS':
        emoji = "🔴"
        title = "CUT LOSS WARNING"
    elif action == 'FINAL_DECISION':
        emoji = "⏰"
        title = "FINAL DECISION TIME"
    else:
        emoji = "🔔"
        title = "POSITION ALERT"
    
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    urgency_indicator = "🔴" if urgency == 'high' else "🟡" if urgency == 'medium' else "🟢"
    
    msg = f"""{emoji} <b>{title}</b> {urgency_indicator}

📊 <b>Market:</b> {position['question'][:80]}

<b>Position:</b> {position['signal_type']}
<b>Entry:</b> {position['market_price_at_signal']*100:.0f}¢
<b>Current:</b> {current_price*100:.0f}¢
{pnl_emoji} <b>P&L:</b> {pnl:+.1f}%

{alert['message']}

<b>Recommended:</b> {action}"""

    # Add market link if available
    if position.get('polymarket_id'):
        msg += f"\n\n🔗 https://jup.ag/prediction/{position.get('polymarket_id', '')[:20]}"
    
    return msg


def save_alert(prediction_id: int, alert: dict, telegram_sent: bool):
    """Save alert to database"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO position_alerts 
        (prediction_id, alert_type, trigger_value, urgency, message, action_recommended, telegram_sent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        prediction_id,
        alert['type'],
        alert.get('pnl'),
        alert['urgency'],
        alert['message'],
        alert['action'],
        1 if telegram_sent else 0
    ))
    
    conn.commit()
    conn.close()


def update_position(prediction_id: int, current_price: float, pnl: float, new_alerts: list):
    """Update position with current price and P&L"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get existing alerts
    cursor.execute("SELECT alerts_sent FROM prediction_tracking WHERE id = ?", (prediction_id,))
    row = cursor.fetchone()
    existing_alerts = json.loads(row['alerts_sent'] or '[]') if row else []
    
    # Add new alert types
    for alert in new_alerts:
        if alert['type'] not in existing_alerts:
            existing_alerts.append(alert['type'])
    
    # Determine position status
    status = 'ACTIVE'
    for alert in new_alerts:
        if alert['action'] == 'TAKE_PROFIT':
            status = 'TAKE_PROFIT_SUGGESTED'
        elif alert['action'] == 'CUT_LOSS':
            status = 'CUT_LOSS_SUGGESTED'
    
    cursor.execute("""
        UPDATE prediction_tracking
        SET current_price = ?,
            current_pnl = ?,
            last_price_check = ?,
            alerts_sent = ?,
            position_status = ?
        WHERE id = ?
    """, (
        current_price,
        pnl,
        datetime.now().isoformat(),
        json.dumps(existing_alerts),
        status,
        prediction_id
    ))
    
    conn.commit()
    conn.close()


# =========================================================
# MAIN FUNCTION
# =========================================================
def get_active_positions() -> list:
    """Get all active (unresolved) positions"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            pt.*,
            m.outcome_prices,
            m.slug
        FROM prediction_tracking pt
        LEFT JOIN markets m ON m.id = pt.market_id
        WHERE pt.final_resolution IS NULL
        ORDER BY pt.created_at DESC
    """)
    
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return positions


def run_price_monitor():
    """Main function - monitor all active positions"""
    log("=" * 60)
    log("📊 Price Monitor Started")
    log("=" * 60)
    
    # Get active positions
    positions = get_active_positions()
    
    if not positions:
        log("No active positions to monitor.")
        return
    
    log(f"\nMonitoring {len(positions)} active position(s)\n")
    
    # Fetch current prices
    log("Fetching current prices...")
    prices = fetch_prices_batch(positions)
    
    total_alerts = 0
    
    for pos in positions:
        log(f"\n{'─' * 50}")
        log(f"Position: {pos['question'][:50]}...")
        log(f"  Direction: {pos['signal_type']} @ {pos['market_price_at_signal']*100:.0f}¢")
        
        # Get current price
        current_price = prices.get(pos['id'])
        if current_price is None:
            current_price = pos['market_price_at_signal']
        
        log(f"  Current: {current_price*100:.0f}¢")
        
        # Calculate P&L
        pnl = calculate_pnl(pos['market_price_at_signal'], current_price, pos['signal_type'])
        log(f"  P&L: {pnl:+.1f}%")
        
        # Check triggers
        alerts = check_triggers(pos, current_price)
        
        if alerts:
            log(f"  🔔 {len(alerts)} alert(s) triggered!")
            total_alerts += len(alerts)
            
            for alert in alerts:
                log(f"     → {alert['type']}: {alert['message']}")
                
                # Send Telegram
                msg = format_alert_message(pos, alert, current_price)
                telegram_sent = send_telegram(msg)
                
                # Save alert
                save_alert(pos['id'], alert, telegram_sent)
        else:
            log(f"  ✅ No alerts - position on track")
        
        # Update position in database
        update_position(pos['id'], current_price, pnl, alerts)
    
    log(f"\n{'=' * 60}")
    log(f"Price Monitor Complete")
    log(f"  Positions: {len(positions)}")
    log(f"  Alerts: {total_alerts}")
    log(f"{'=' * 60}\n")


if __name__ == '__main__':
    run_price_monitor()
