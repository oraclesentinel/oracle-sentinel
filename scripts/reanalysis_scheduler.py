#!/usr/bin/env python3
"""
Re-analysis Scheduler - Analyze predictions 5-6 hours before market close
Runs every hour via cron, but only triggers analysis when timing is right
Now with Telegram alerts for signal changes
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
OPENCLAW_SESSION_ID = "agent:main:main"

# Telegram Config
from config_loader import BOT_TOKEN, CHAT_IDS

# Window: 5-6 hours before market close
HOURS_BEFORE_CLOSE_MIN = 5
HOURS_BEFORE_CLOSE_MAX = 6


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
            log(f"  📱 Telegram sent to {chat_id}")
        except Exception as e:
            log(f"  ⚠ Telegram error: {e}")


def get_db():
    return sqlite3.connect(DB_PATH)


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
            pt.revised_at,
            m.slug,
            m.description
        FROM prediction_tracking pt
        JOIN markets m ON m.id = pt.market_id
        WHERE pt.final_resolution IS NULL
          AND pt.revised_at IS NULL
          AND pt.market_end_date IS NOT NULL
    ''')
    
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
            'description': row[12]
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


def call_openclaw_reanalysis(question: str, slug: str, description: str, original_signal: str, original_prob: float) -> dict:
    """
    Call OpenClaw to re-analyze a market with fresh news
    """
    polymarket_url = f"https://polymarket.com/event/{slug}" if slug else ""
    
    prompt = f"""URGENT RE-ANALYSIS REQUEST - Market closing in 5-6 hours

MARKET: {question}
URL: {polymarket_url}

RESOLUTION RULES:
{description[:1500] if description else 'Not available'}

ORIGINAL PREDICTION (made earlier):
- Signal: {original_signal}
- AI Probability: {original_prob * 100:.1f}%

YOUR TASK:
1. Fetch the latest market data from Polymarket using the URL above
2. Search for any NEW news or developments since the original prediction
3. Re-assess the probability based on current information
4. Compare with original prediction

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "current_market_price": 0.XX,
    "revised_probability": 0.XX,
    "revised_signal": "BUY_YES|BUY_NO|NO_TRADE",
    "revised_confidence": "LOW|MEDIUM|HIGH",
    "signal_changed": true/false,
    "change_reason": "Brief explanation if signal changed, or 'No change - original analysis still valid'",
    "new_information": "Any new developments found, or 'No significant new information'",
    "key_factors": ["factor1", "factor2"]
}}

Be calibrated. If no new information changes the outlook, keep the original signal.
Only change if there's a genuine reason based on new facts."""

    try:
        log(f"  Calling OpenClaw for re-analysis...")
        result = subprocess.run(
            [
                "openclaw", "agent",
                "-m", prompt,
                "--session-id", OPENCLAW_SESSION_ID,
                "--json"
            ],
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/lib/node_modules/.bin"}
        )
        
        if result.returncode != 0:
            log(f"  ⚠ OpenClaw failed: {result.stderr[:200]}")
            return None
        
        try:
            response_data = json.loads(result.stdout)
            # Get response text from payloads array
            payloads = response_data.get('result', {}).get('payloads', [])
            if not payloads:
                log(f"  ⚠ No payloads in response")
                return None
            response_text = payloads[0].get('text', '')
            
            # Strip markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif "```" in response_text:
                response_text = response_text.replace("```", "").strip()
            
            if '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                log(f"  ⚠ No JSON found in response")
                return None
                
        except json.JSONDecodeError as e:
            log(f"  ⚠ JSON parse error: {e}")
            return None
            
    except subprocess.TimeoutExpired:
        log(f"  ⚠ OpenClaw timeout (180s)")
        return None
    except Exception as e:
        log(f"  ⚠ Error calling OpenClaw: {e}")
        return None


def update_prediction_tracking(pred_id: int, original: dict, revised: dict):
    """
    Update prediction_tracking with revised analysis
    """
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE prediction_tracking
        SET 
            original_signal_type = ?,
            original_ai_probability = ?,
            original_edge = ?,
            signal_type = ?,
            ai_probability = ?,
            edge_at_signal = ?,
            confidence = ?,
            revised_at = ?,
            revision_reason = ?
        WHERE id = ?
    ''', (
        original['signal_type'],
        original['ai_probability'],
        original['edge_at_signal'],
        revised.get('revised_signal', original['signal_type']),
        revised.get('revised_probability', original['ai_probability']),
        round((revised.get('revised_probability', original['ai_probability']) - revised.get('current_market_price', original['market_price_at_signal'])) * 100, 2),
        revised.get('revised_confidence', original['confidence']),
        now,
        revised.get('change_reason', 'Re-analysis completed')[:500]
    ))
    
    conn.commit()
    conn.close()
    
    log(f"  ✓ Updated prediction #{pred_id}")


def send_signal_change_alert(pred: dict, revised: dict):
    """Send Telegram alert when signal changes"""
    old_signal = pred['signal_type']
    new_signal = revised.get('revised_signal', old_signal)
    
    # Emoji based on signal
    if new_signal == 'BUY_YES':
        signal_emoji = "🟢"
    elif new_signal == 'BUY_NO':
        signal_emoji = "🔴"
    else:
        signal_emoji = "⚪"
    
    msg = f"""⚡ <b>SIGNAL REVISED</b>

📊 <b>Market:</b> {pred['question'][:100]}

<b>Original:</b> {old_signal} ({pred['ai_probability']*100:.0f}%)
<b>Revised:</b> {signal_emoji} {new_signal} ({revised.get('revised_probability', 0)*100:.0f}%)

<b>Reason:</b> {revised.get('change_reason', 'N/A')[:200]}

<b>New Info:</b> {revised.get('new_information', 'None')[:200]}

⏰ Market closes in ~5 hours

🔗 https://polymarket.com/event/{pred.get('slug', '')}"""

    send_telegram(msg)


def run_reanalysis():
    """Main function - check and re-analyze predictions near close"""
    log("=" * 60)
    log("🔄 Re-analysis Scheduler Started")
    log("=" * 60)
    
    predictions = get_predictions_near_close()
    
    if not predictions:
        log("No predictions found in 5-6 hour window. Exiting.")
        return
    
    log(f"\nFound {len(predictions)} prediction(s) to re-analyze\n")
    
    for pred in predictions:
        log(f"\n{'─' * 50}")
        log(f"Re-analyzing: {pred['question'][:60]}...")
        log(f"  Original signal: {pred['signal_type']} ({pred['ai_probability']*100:.1f}%)")
        log(f"  Market closes: {pred['market_end_date']}")
        
        revised = call_openclaw_reanalysis(
            question=pred['question'],
            slug=pred['slug'],
            description=pred['description'],
            original_signal=pred['signal_type'],
            original_prob=pred['ai_probability']
        )
        
        if not revised:
            log(f"  ⚠ Re-analysis failed - keeping original signal")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE prediction_tracking
                SET revised_at = ?, revision_reason = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), 'Re-analysis attempted but failed', pred['id']))
            conn.commit()
            conn.close()
            continue
        
        # Check if signal changed
        old_signal = pred['signal_type']
        new_signal = revised.get('revised_signal', old_signal)
        signal_changed = revised.get('signal_changed', False) or (old_signal != new_signal)
        
        if signal_changed:
            log(f"  ⚡ SIGNAL CHANGED: {old_signal} → {new_signal}")
            log(f"     Reason: {revised.get('change_reason', 'Unknown')}")
            log(f"     New info: {revised.get('new_information', 'None')}")
            
            # Send Telegram alert
            send_signal_change_alert(pred, revised)
        else:
            log(f"  ✓ Signal confirmed: {old_signal} (no change)")
        
        # Update database
        update_prediction_tracking(pred['id'], pred, revised)
    
    log(f"\n{'=' * 60}")
    log(f"Re-analysis complete. Processed {len(predictions)} prediction(s)")
    log(f"{'=' * 60}\n")


if __name__ == '__main__':
    run_reanalysis()
