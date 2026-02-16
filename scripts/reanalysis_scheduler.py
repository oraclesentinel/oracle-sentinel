#!/usr/bin/env python3
"""
Re-analysis Scheduler - Position Management System
Analyzes existing positions 5-6 hours before market close
OUTPUT: HOLD / TAKE_PROFIT / CUT_LOSS / ALERT (bukan sinyal baru!)

Key Changes from original:
1. Reanalysis BUKAN untuk kasih sinyal baru
2. Reanalysis untuk MANAGE existing position
3. Tidak affect accuracy calculation
4. Skip jika harga sudah ekstrem (>85% atau <15%)
"""

import os
import sys
import json
import sqlite3
import subprocess
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'reanalysis.log')

# Telegram Config
try:
    from config_loader import BOT_TOKEN, CHAT_IDS
except:
    BOT_TOKEN = None
    CHAT_IDS = []

# Window: 5-6 hours before market close
HOURS_BEFORE_CLOSE_MIN = 5
HOURS_BEFORE_CLOSE_MAX = 6

# Position Management Thresholds
TAKE_PROFIT_THRESHOLD = 50  # Take profit if P&L >= 50%
CUT_LOSS_THRESHOLD = -30    # Cut loss if P&L <= -30%
EXTREME_PRICE_HIGH = 0.85   # Skip if price > 85%
EXTREME_PRICE_LOW = 0.15    # Skip if price < 15%


def log(message: str):
    """Log to file and stdout"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {message}"
    print(line)
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(line + '\n')
    except:
        pass


def send_telegram(text: str):
    """Send alert to Telegram"""
    if not BOT_TOKEN or not CHAT_IDS:
        return
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
            log(f"  📱 Telegram sent to {chat_id}")
        except Exception as e:
            log(f"  ⚠ Telegram error: {e}")


def get_db():
    return sqlite3.connect(DB_PATH)


def get_current_market_price(market_id: int) -> float:
    """Get current market price from markets table"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT outcome_prices FROM markets WHERE id = ?", (market_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    try:
        import json
        prices = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        return float(prices[0]) if prices else None
    except:
        return None


def calculate_pnl(entry_price: float, current_price: float, direction: str) -> float:
    """
    Calculate P&L percentage for a position
    direction: 'BUY_YES' or 'BUY_NO'
    """
    if direction == 'BUY_YES':
        # Bought YES at entry_price, current value is current_price
        if entry_price > 0:
            return ((current_price - entry_price) / entry_price) * 100
    else:  # BUY_NO
        # Bought NO at (1-entry_price), current NO value is (1-current_price)
        entry_no = 1 - entry_price
        current_no = 1 - current_price
        if entry_no > 0:
            return ((current_no - entry_no) / entry_no) * 100
    return 0


def determine_position_action(
    entry_price: float,
    current_price: float,
    direction: str,
    thesis_still_valid: bool = True,
    has_new_contradicting_info: bool = False
) -> dict:
    """
    Determine position management action
    
    Returns:
        {
            'action': 'HOLD' | 'TAKE_PROFIT' | 'CUT_LOSS' | 'ALERT',
            'reason': str,
            'pnl_pct': float,
            'urgency': 'low' | 'medium' | 'high'
        }
    """
    pnl = calculate_pnl(entry_price, current_price, direction)
    
    # Check for extreme prices - market already decided
    if current_price >= EXTREME_PRICE_HIGH:
        if direction == 'BUY_YES':
            return {
                'action': 'TAKE_PROFIT',
                'reason': f'Market at {current_price*100:.0f}% - strongly favoring YES. Consider taking profit.',
                'pnl_pct': pnl,
                'urgency': 'medium'
            }
        else:
            return {
                'action': 'CUT_LOSS',
                'reason': f'Market at {current_price*100:.0f}% - strongly against NO position.',
                'pnl_pct': pnl,
                'urgency': 'high'
            }
    
    if current_price <= EXTREME_PRICE_LOW:
        if direction == 'BUY_NO':
            return {
                'action': 'TAKE_PROFIT',
                'reason': f'Market at {current_price*100:.0f}% - strongly favoring NO. Consider taking profit.',
                'pnl_pct': pnl,
                'urgency': 'medium'
            }
        else:
            return {
                'action': 'CUT_LOSS',
                'reason': f'Market at {current_price*100:.0f}% - strongly against YES position.',
                'pnl_pct': pnl,
                'urgency': 'high'
            }
    
    # Check P&L thresholds
    if pnl >= TAKE_PROFIT_THRESHOLD:
        return {
            'action': 'TAKE_PROFIT',
            'reason': f'Position up {pnl:.1f}%. Consider securing gains before close.',
            'pnl_pct': pnl,
            'urgency': 'medium'
        }
    
    if pnl <= CUT_LOSS_THRESHOLD:
        if not thesis_still_valid:
            return {
                'action': 'CUT_LOSS',
                'reason': f'Position down {pnl:.1f}% and thesis invalidated. Consider cutting loss.',
                'pnl_pct': pnl,
                'urgency': 'high'
            }
        else:
            return {
                'action': 'ALERT',
                'reason': f'Position down {pnl:.1f}% but thesis still valid. Monitor closely.',
                'pnl_pct': pnl,
                'urgency': 'medium'
            }
    
    # Check for new contradicting information
    if has_new_contradicting_info:
        return {
            'action': 'ALERT',
            'reason': 'New information may affect position. Re-evaluate thesis.',
            'pnl_pct': pnl,
            'urgency': 'high'
        }
    
    # Default: HOLD
    return {
        'action': 'HOLD',
        'reason': f'Position on track (P&L: {pnl:+.1f}%). No action needed.',
        'pnl_pct': pnl,
        'urgency': 'low'
    }


def get_predictions_near_close() -> list:
    """
    Get predictions from prediction_tracking where market_end_date
    is between 5-6 hours from now AND not yet revised
    """
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=HOURS_BEFORE_CLOSE_MIN)
    window_end = now + timedelta(hours=HOURS_BEFORE_CLOSE_MAX)

    log(f"Checking for markets closing between {window_start.isoformat()} and {window_end.isoformat()}")

    cursor.execute("""
        SELECT
            pt.id,
            pt.market_id,
            pt.polymarket_id,
            pt.question,
            pt.signal_type,
            pt.ai_probability,
            pt.market_price_at_signal,
            pt.edge_at_signal,
            pt.confidence,
            pt.market_end_date,
            pt.revised_at,
            m.slug,
            m.description,
            pt.signal_source,
            m.outcome_prices
        FROM prediction_tracking pt
        JOIN markets m ON m.id = pt.market_id
        WHERE pt.final_resolution IS NULL
          AND pt.revised_at IS NULL
          AND pt.market_end_date IS NOT NULL
    """)

    predictions = []
    for row in cursor.fetchall():
        pred = {
            'id': row[0],
            'market_id': row[1],
            'polymarket_id': row[2],
            'question': row[3],
            'signal_type': row[4],
            'ai_probability': row[5],
            'market_price_at_signal': row[6],
            'edge_at_signal': row[7],
            'confidence': row[8],
            'market_end_date': row[9],
            'revised_at': row[10],
            'slug': row[11],
            'description': row[12],
            'signal_source': row[13] if len(row) > 13 else 'scan',
            'current_price': (float(json.loads(row[14])[0]) if row[14] else None) if len(row) > 14 else None
        }

        # Parse end date and check if in window
        try:
            end_date_str = pred['market_end_date']
            if end_date_str:
                if 'T' in end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    end_date = datetime.fromisoformat(end_date_str + 'T00:00:00+00:00')

                if window_start <= end_date <= window_end:
                    pred['end_date_parsed'] = end_date
                    predictions.append(pred)
                    log(f"  → Found: {pred['question'][:50]}... (closes {end_date.isoformat()})")
        except Exception as e:
            log(f"  ⚠ Failed to parse end_date '{pred.get('market_end_date')}': {e}")

    conn.close()
    return predictions


def check_thesis_validity(question: str, original_signal: str, description: str) -> dict:
    """
    Quick check if original thesis is still valid.
    Returns: {'valid': bool, 'new_info': str, 'contradicting': bool}
    
    This is a simplified version - in production you might want to call LLM
    """
    # For now, assume thesis is still valid unless we implement LLM check
    # You can enhance this later with actual news checking
    return {
        'valid': True,
        'new_info': 'No significant new information detected',
        'contradicting': False
    }


def update_position_status(pred_id: int, action_result: dict, current_price: float):
    """
    Update prediction_tracking with position management result.
    NOTE: This does NOT change signal_type - just adds position_action info
    """
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Store position management result in revision fields
    revision_reason = f"[{action_result['action']}] {action_result['reason']} (P&L: {action_result['pnl_pct']:+.1f}%)"
    
    cursor.execute("""
        UPDATE prediction_tracking
        SET 
            revised_at = ?,
            revision_reason = ?
        WHERE id = ?
    """, (now, revision_reason[:500], pred_id))
    
    conn.commit()
    conn.close()
    
    log(f"  ✓ Updated position #{pred_id} with action: {action_result['action']}")


def send_position_alert(pred: dict, action_result: dict, current_price: float):
    """Send Telegram alert for position management"""
    
    action = action_result['action']
    
    # Emoji based on action
    if action == 'TAKE_PROFIT':
        emoji = "💰"
        title = "TAKE PROFIT OPPORTUNITY"
    elif action == 'CUT_LOSS':
        emoji = "⚠️"
        title = "CUT LOSS WARNING"
    elif action == 'ALERT':
        emoji = "🔔"
        title = "POSITION ALERT"
    else:  # HOLD
        emoji = "✅"
        title = "POSITION CONFIRMED"
    
    pnl = action_result['pnl_pct']
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    
    msg = f"""{emoji} <b>{title}</b>

📊 <b>Market:</b> {pred['question'][:100]}

<b>Position:</b> {pred['signal_type']}
<b>Entry Price:</b> {pred['market_price_at_signal']*100:.0f}¢
<b>Current Price:</b> {current_price*100:.0f}¢
{pnl_emoji} <b>P&L:</b> {pnl:+.1f}%

<b>Recommendation:</b> {action_result['action']}
<b>Reason:</b> {action_result['reason'][:200]}

⏰ Market closes in ~5 hours
🔗 https://polymarket.com/event/{pred.get('slug', '')}"""

    send_telegram(msg)


def run_position_management():
    """Main function - check and manage positions near close"""
    log("=" * 60)
    log("📊 Position Management Scheduler Started")
    log("=" * 60)

    predictions = get_predictions_near_close()

    if not predictions:
        log("No positions found in 5-6 hour window. Exiting.")
        return

    log(f"\nFound {len(predictions)} position(s) to review\n")

    for pred in predictions:
        log(f"\n{'─' * 50}")
        log(f"Reviewing: {pred['question'][:60]}...")
        log(f"  Position: {pred['signal_type']} @ {pred['market_price_at_signal']*100:.0f}¢")
        
        # Get current price
        current_price = pred.get('current_price') or get_current_market_price(pred['market_id'])
        
        if current_price is None:
            log(f"  ⚠ Could not get current price - skipping")
            continue
        
        log(f"  Current price: {current_price*100:.0f}¢")
        
        # Calculate P&L
        pnl = calculate_pnl(pred['market_price_at_signal'], current_price, pred['signal_type'])
        log(f"  Current P&L: {pnl:+.1f}%")
        
        # Check thesis validity (simplified)
        thesis_check = check_thesis_validity(
            pred['question'],
            pred['signal_type'],
            pred.get('description', '')
        )
        
        # Determine action
        action_result = determine_position_action(
            entry_price=pred['market_price_at_signal'],
            current_price=current_price,
            direction=pred['signal_type'],
            thesis_still_valid=thesis_check['valid'],
            has_new_contradicting_info=thesis_check['contradicting']
        )
        
        log(f"  📋 Action: {action_result['action']}")
        log(f"     Reason: {action_result['reason']}")
        log(f"     Urgency: {action_result['urgency']}")
        
        # Update database
        update_position_status(pred['id'], action_result, current_price)
        
        # Send alert if not just HOLD with low urgency
        if action_result['action'] != 'HOLD' or action_result['urgency'] != 'low':
            send_position_alert(pred, action_result, current_price)

    log(f"\n{'=' * 60}")
    log(f"Position management complete. Reviewed {len(predictions)} position(s)")
    log(f"{'=' * 60}\n")


# Alias for backward compatibility
run_reanalysis = run_position_management


if __name__ == '__main__':
    run_position_management()
