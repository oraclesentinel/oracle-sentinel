#!/usr/bin/env python3
"""
Auto Resolver - Automatically resolve predictions by fetching final market data
Checks markets that have passed their end_date and updates final_resolution
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'auto_resolver.log')

# Telegram Config
from config_loader import BOT_TOKEN, CHAT_IDS

# Polymarket API
from jupiter_prediction_client import JupiterPredictionClient


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
            log(f"  ⚠ Telegram error: {e}")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_market_from_jupiter(market_id: str) -> dict:
    """Fetch market data from Jupiter Prediction API"""
    try:
        jupiter = JupiterPredictionClient()
        market = jupiter.get_market_by_id(market_id)
        if market:
            # Convert to compatible format
            pricing = market.get('pricing', {})
            yes_price = (pricing.get('buyYesPriceUsd', 0) or 0) / 1_000_000
            return {
                'id': market_id,
                'question': market.get('title', ''),
                'closed': market.get('status') == 'closed',
                'outcomePrices': [yes_price, 1 - yes_price],
                'resolved': market.get('status') == 'resolved',
            }
        else:
            log(f"  ⚠ Market not found: {market_id}")
            return None
    except Exception as e:
        log(f"  ⚠ Fetch error: {e}")
        return None


def get_unresolved_past_predictions() -> list:
    """Get predictions where market has ended but not yet resolved"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute('''
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
            m.slug
        FROM prediction_tracking pt
        JOIN markets m ON m.id = pt.market_id
        WHERE pt.final_resolution IS NULL
          AND pt.market_end_date IS NOT NULL
          AND pt.market_end_date < ?
    ''', (now,))
    
    predictions = []
    for row in cursor.fetchall():
        predictions.append(dict(row))
    
    conn.close()
    return predictions


def determine_resolution(market_data: dict) -> str:
    """Determine if market resolved YES or NO based on outcome prices"""
    try:
        # Must check closed/resolved first - don't resolve markets that aren't closed
        is_closed = market_data.get('closed', False)
        is_resolved = market_data.get('resolved', False)
        
        if not is_closed and not is_resolved:
            return None  # Market not finished yet
        
        if is_closed or is_resolved:
            outcome_prices = market_data.get('outcomePrices', [])
            if not outcome_prices:
                outcome_prices = market_data.get('outcome_prices', [])
            
            if outcome_prices:
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
                
                yes_price = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0
                
                if yes_price >= 0.95:
                    return 'YES'
                elif yes_price <= 0.05:
                    return 'NO'
            
            # Check resolution field directly (only if market is closed)
            resolution = market_data.get('resolution', market_data.get('result'))
            if resolution:
                return resolution.upper()
        
        return None
    except Exception as e:
        log(f"  ⚠ Resolution parse error: {e}")
        return None


def update_resolution(pred_id: int, resolution: str, direction_correct: int):
    """Update prediction_tracking with resolution"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE prediction_tracking
        SET final_resolution = ?,
            resolved_at = ?,
            direction_correct = ?
        WHERE id = ?
    ''', (resolution, datetime.now().isoformat(), direction_correct, pred_id))
    
    conn.commit()
    conn.close()


def send_resolution_alert(pred: dict, resolution: str, correct: bool):
    """Send Telegram alert for resolved prediction"""
    emoji = "✅" if correct else "❌"
    
    msg = f"""{emoji} <b>PREDICTION RESOLVED</b>

📊 <b>Market:</b> {pred['question'][:100]}

<b>Our Signal:</b> {pred['signal_type']}
<b>AI Probability:</b> {pred['ai_probability']*100:.0f}%
<b>Result:</b> <b>{resolution}</b>

{emoji} <b>{'CORRECT!' if correct else 'WRONG'}</b>

🔗 https://jup.ag/prediction/{pred.get('slug', '')}"""

    send_telegram(msg)


def run_auto_resolver():
    """Main function - check and resolve past predictions"""
    log("=" * 60)
    log("🔍 Auto Resolver Started")
    log("=" * 60)
    
    predictions = get_unresolved_past_predictions()
    
    if not predictions:
        log("No unresolved past predictions found. Exiting.")
        return
    
    log(f"\nFound {len(predictions)} prediction(s) past end date\n")
    
    resolved_count = 0
    correct_count = 0
    
    for pred in predictions:
        log(f"\n{'─' * 50}")
        log(f"Checking: {pred['question'][:60]}...")
        log(f"  Signal: {pred['signal_type']} | End date: {pred['market_end_date']}")
        
        # Fetch from Polymarket API
        if not pred['polymarket_id']:
            log(f"  ⚠ No polymarket_id - skipping")
            continue
        
        market_data = fetch_market_from_jupiter(pred['polymarket_id'])
        if not market_data:
            log(f"  ⚠ Could not fetch market data - skipping")
            continue
        
        # Determine resolution
        resolution = determine_resolution(market_data)
        if not resolution:
            log(f"  ⏳ Market not yet resolved - skipping")
            continue
        
        # Check if correct
        # Signal-based: BUY_YES correct if YES, BUY_NO correct if NO
        signal_correct = (
            (pred['signal_type'] == 'BUY_YES' and resolution == 'YES') or
            (pred['signal_type'] == 'BUY_NO' and resolution == 'NO')
        )
        # Probability-based: AI estimate >50% and resolves YES, or <50% and resolves NO
        prob_correct = (
            (pred['ai_probability'] >= 0.5 and resolution == 'YES') or
            (pred['ai_probability'] < 0.5 and resolution == 'NO')
        )
        # Use probability-based as primary metric
        # AI estimating 92% YES on market that resolves YES = correct
        correct = prob_correct
        direction_correct = 1 if correct else 0

        # Log both metrics
        log(f"  Signal direction: {'✅' if signal_correct else '❌'} | AI probability: {'✅' if prob_correct else '❌'}")
        
        # Update database
        update_resolution(pred['id'], resolution, direction_correct)
        
        # Log result
        emoji = "✅" if correct else "❌"
        log(f"  {emoji} Resolved: {resolution} | {'CORRECT' if correct else 'WRONG'}")
        
        # Send Telegram alert
        send_resolution_alert(pred, resolution, correct)
        
        resolved_count += 1
        if correct:
            correct_count += 1
    
    # Summary
    log(f"\n{'=' * 60}")
    log(f"Auto Resolver Complete")
    if resolved_count > 0:
        accuracy = correct_count / resolved_count * 100
        log(f"  Resolved: {resolved_count}")
        log(f"  Accuracy: {correct_count}/{resolved_count} ({accuracy:.0f}%)")
        
        # Send summary only if multiple resolved
        if resolved_count > 1:
            summary = f"""📊 <b>AUTO-RESOLVER SUMMARY</b>

Resolved: {resolved_count} prediction(s)
Accuracy: {correct_count}/{resolved_count} ({accuracy:.0f}%)"""
            send_telegram(summary)
    else:
        log(f"  No markets resolved this run")
    log(f"{'=' * 60}\n")


if __name__ == '__main__':
    run_auto_resolver()
