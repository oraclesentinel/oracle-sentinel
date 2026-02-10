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
from accuracy_tracker import AccuracyTracker

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



def auto_fetch_market_from_api(trade: dict) -> int:
    """
    Auto-fetch market dari Polymarket API jika belum ada di database.
    Returns market_id jika berhasil, None jika gagal.
    """
    from polymarket_client import PolymarketClient
    
    slug = trade.get('eventSlug', '')
    title = trade.get('title', '')
    
    if not slug:
        print(f"  ⚠ No slug available for auto-fetch")
        return None
    
    print(f"  🔄 Auto-fetching market from Polymarket API...")
    print(f"     Slug: {slug}")
    
    try:
        client = PolymarketClient()
        
        # Fetch market by slug
        market_data = client.get_market_by_slug(slug)
        
        if not market_data:
            print(f"  ⚠ Market not found on Polymarket API")
            return None
        
        # Save to database
        market_id = client.save_market(market_data)
        
        print(f"  ✅ Market auto-fetched and saved! ID: {market_id}")
        print(f"     Question: {market_data.get('question', '')[:60]}...")
        
        return market_id
        
    except Exception as e:
        print(f"  ❌ Auto-fetch failed: {e}")
        return None


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
            print(f"  ⚠ Market not found in DB, attempting auto-fetch...")
            
            # Auto-fetch dari Polymarket API
            auto_market_id = auto_fetch_market_from_api(trade)
            
            if not auto_market_id:
                print(f"  ⚠ Auto-fetch failed, skipping AI analysis")
                return None
            
            # Re-query setelah auto-fetch
            cursor = conn.cursor() if 'cursor' in dir() else sqlite3.connect(DB_PATH).cursor()
            conn_new = sqlite3.connect(DB_PATH)
            cursor_new = conn_new.cursor()
            cursor_new.execute("""
                SELECT id, question, description, end_date, outcome_prices
                FROM markets WHERE id = ?
            """, (auto_market_id,))
            market = cursor_new.fetchone()
            conn_new.close()
            
            if not market:
                print(f"  ⚠ Market still not found after auto-fetch, skipping")
                return None
            
            print(f"  ✅ Market loaded after auto-fetch!")
            
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




def check_whale_exit(trade: dict) -> dict:
    """
    Check if this SELL trade is a whale exiting a market we're tracking.
    Returns info about the tracked prediction if found.
    """
    if trade.get('side', '').upper() != 'SELL':
        return None
    
    title = trade.get('title', '')
    slug = trade.get('eventSlug', '')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Find if this market has a tracked whale signal
        cursor.execute("""
            SELECT pt.id, pt.market_id, pt.signal_type, pt.whale_trader, 
                   pt.whale_status, m.question
            FROM prediction_tracking pt
            JOIN markets m ON m.id = pt.market_id
            WHERE pt.signal_source = 'whale_confirmed'
              AND pt.final_resolution IS NULL
              AND pt.whale_status = 'HOLDING'
              AND (m.slug = ? OR m.question LIKE ?)
            LIMIT 1
        """, (slug, f'%{title[:50]}%'))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'track_id': row[0],
                'market_id': row[1],
                'signal_type': row[2],
                'original_whale': row[3],
                'status': row[4],
                'question': row[5]
            }
        return None
        
    except Exception as e:
        print(f"  ❌ Error checking whale exit: {e}")
        return None


def handle_whale_exit(trade: dict, tracked_info: dict):
    """
    Handle whale exit: trigger re-analysis and update signal if needed.
    """
    print(f"  ⚠️ WHALE EXIT DETECTED on tracked market!")
    print(f"  📊 Original signal: {tracked_info['signal_type']}")
    
    track_id = tracked_info['track_id']
    market_id = tracked_info['market_id']
    
    try:
        # Import here to avoid circular imports
        from ai_brain import AIBrain
        
        # Run fresh AI analysis
        print(f"  🔄 Triggering re-analysis...")
        brain = AIBrain()
        result = brain.analyze_market(market_id=market_id)
        
        if not result:
            print(f"  ⚠️ Re-analysis failed")
            return
        
        new_recommendation = result.get('recommendation', 'NO_TRADE')
        new_ai_prob = result.get('ai_probability', 0.5)
        old_signal = tracked_info['signal_type']
        
        print(f"  🧠 New AI assessment: {new_ai_prob*100:.1f}% YES → {new_recommendation}")
        
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Mark whale as exited
        cursor.execute("""
            UPDATE prediction_tracking 
            SET whale_status = 'EXITED'
            WHERE id = ?
        """, (track_id,))
        
        # If signal changed, update it
        signal_changed = (old_signal != new_recommendation)
        if signal_changed:
            cursor.execute("""
                UPDATE prediction_tracking 
                SET original_signal_type = COALESCE(original_signal_type, signal_type),
                    original_ai_probability = COALESCE(original_ai_probability, ai_probability),
                    signal_type = ?,
                    ai_probability = ?,
                    revised_at = datetime('now'),
                    revision_reason = ?
                WHERE id = ?
            """, (
                new_recommendation,
                new_ai_prob,
                f'Whale exit detected - re-analyzed',
                track_id
            ))
            print(f"  🔄 Signal REVISED: {old_signal} → {new_recommendation}")
        else:
            cursor.execute("""
                UPDATE prediction_tracking 
                SET revised_at = datetime('now'),
                    revision_reason = ?
                WHERE id = ?
            """, (f'Whale exit detected - signal unchanged after re-analysis', track_id))
            print(f"  ✅ Signal UNCHANGED: {old_signal} (still valid)")
        
        conn.commit()
        conn.close()
        
        # Send Telegram alert
        exit_alert = format_whale_exit_alert(trade, tracked_info, result, signal_changed)
        send_telegram(exit_alert)
        
    except Exception as e:
        print(f"  ❌ Error handling whale exit: {e}")
        import traceback
        traceback.print_exc()


def format_whale_exit_alert(trade: dict, tracked_info: dict, ai_result: dict, signal_changed: bool) -> str:
    """Format Telegram alert for whale exit."""
    title = tracked_info.get('question', trade.get('title', ''))[:60]
    whale_name = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    sell_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
    old_signal = tracked_info['signal_type']
    new_signal = ai_result.get('recommendation', 'NO_TRADE')
    new_prob = ai_result.get('ai_probability', 0.5)
    
    lines = [
        f"⚠️ <b>WHALE EXIT DETECTED</b>",
        f"",
        f"<b>{title}...</b>",
        f"",
        f"🐋 <b>{whale_name}</b> is EXITING",
        f"Sell size: <b>${sell_size:,.0f}</b>",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🔄 <b>RE-ANALYSIS COMPLETE</b>",
        f"",
        f"AI Probability: {new_prob*100:.1f}%",
    ]
    
    if signal_changed:
        lines.append(f"")
        lines.append(f"🔴 <b>SIGNAL REVISED</b>")
        lines.append(f"{old_signal} → {new_signal}")
    else:
        lines.append(f"")
        lines.append(f"✅ <b>SIGNAL UNCHANGED</b>")
        lines.append(f"Still: {old_signal}")
    
    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"")
    lines.append(f"🤖 <i>Oracle Sentinel — Whale Intelligence</i>")
    
    return "\n".join(lines)




def check_existing_signal(trade: dict) -> dict:
    """
    Check if this market already has a tracked signal.
    Returns info about the existing prediction if found.
    """
    title = trade.get('title', '')
    slug = trade.get('eventSlug', '')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pt.id, pt.market_id, pt.signal_type, pt.ai_probability,
                   pt.signal_source, pt.whale_trader, m.question
            FROM prediction_tracking pt
            JOIN markets m ON m.id = pt.market_id
            WHERE pt.final_resolution IS NULL
              AND (m.slug = ? OR m.question LIKE ?)
            LIMIT 1
        """, (slug, f'%{title[:50]}%'))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'track_id': row[0],
                'market_id': row[1],
                'signal_type': row[2],
                'ai_probability': row[3],
                'signal_source': row[4],
                'whale_trader': row[5],
                'question': row[6]
            }
        return None
        
    except Exception as e:
        print(f"  ❌ Error checking existing signal: {e}")
        return None


def is_same_direction(existing_signal: str, whale_outcome: str, whale_side: str) -> bool:
    """Check if whale trade is same direction as existing signal."""
    outcome_lower = whale_outcome.lower() if whale_outcome else ''
    is_yes = 'yes' in outcome_lower or outcome_lower in ('yes', 'true', '1')
    
    # BUY YES = bullish, BUY NO = bearish
    whale_bullish = (whale_side.upper() == 'BUY' and is_yes) or (whale_side.upper() == 'SELL' and not is_yes)
    signal_bullish = existing_signal == 'BUY_YES'
    
    return whale_bullish == signal_bullish


def handle_existing_signal(trade: dict, existing: dict, ai_result: dict, alignment: dict):
    """
    Handle whale trade on market that already has a tracked signal.
    - Same direction: Update whale info only
    - Different direction: Re-analysis decides (AI wins if still disagree)
    """
    track_id = existing['track_id']
    old_signal = existing['signal_type']
    whale_side = trade.get('side', '').upper()
    whale_outcome = trade.get('outcome', '')
    whale_name = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    whale_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
    whale_price = float(trade.get('price', 0))
    whale_tx = trade.get('transactionHash', '')
    
    same_direction = is_same_direction(old_signal, whale_outcome, whale_side)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if same_direction:
        # Whale confirms existing signal - just update whale info
        print(f"  ✅ Whale CONFIRMS existing signal: {old_signal}")
        cursor.execute("""
            UPDATE prediction_tracking 
            SET signal_source = 'whale_confirmed',
                whale_trader = ?,
                whale_trade_size = ?,
                whale_entry_price = ?,
                whale_tx_hash = ?,
                whale_status = 'HOLDING',
                revised_at = datetime('now'),
                revision_reason = 'Whale confirmed existing signal'
            WHERE id = ?
        """, (whale_name, whale_size, whale_price, whale_tx, track_id))
        conn.commit()
        conn.close()
        
        # Send confirmation alert
        alert = format_whale_confirms_alert(trade, existing)
        send_telegram(alert)
        return
    
    # Different direction - check if AI now agrees with whale after re-analysis
    print(f"  ⚠️ Whale OPPOSITE to existing signal: {old_signal}")
    print(f"  🐋 Whale: {whale_side} {whale_outcome} (${whale_size:,.0f})")
    
    new_signal = alignment.get('signal')
    ai_prob = ai_result.get('ai_probability', 0.5)
    aligned = alignment.get('aligned', False)
    
    if aligned and new_signal and new_signal != old_signal:
        # AI now agrees with whale - UPDATE signal
        print(f"  🔄 AI agrees with whale after re-analysis!")
        print(f"  🔄 Signal UPDATE: {old_signal} → {new_signal}")
        
        cursor.execute("""
            UPDATE prediction_tracking 
            SET original_signal_type = COALESCE(original_signal_type, signal_type),
                original_ai_probability = COALESCE(original_ai_probability, ai_probability),
                signal_type = ?,
                ai_probability = ?,
                signal_source = 'whale_confirmed',
                whale_trader = ?,
                whale_trade_size = ?,
                whale_entry_price = ?,
                whale_tx_hash = ?,
                whale_status = 'HOLDING',
                revised_at = datetime('now'),
                revision_reason = ?
            WHERE id = ?
        """, (
            new_signal,
            ai_prob,
            whale_name,
            whale_size,
            whale_price,
            whale_tx,
            f'Whale + AI aligned: {old_signal} → {new_signal}',
            track_id
        ))
        conn.commit()
        conn.close()
        
        # Send update alert
        alert = format_whale_update_alert(trade, existing, ai_result, new_signal)
        send_telegram(alert)
    else:
        # AI still disagrees with whale - KEEP existing signal (AI wins)
        print(f"  🤖 AI still disagrees with whale after re-analysis")
        print(f"  🤖 AI WINS - keeping: {old_signal}")
        
        cursor.execute("""
            UPDATE prediction_tracking 
            SET revised_at = datetime('now'),
                revision_reason = ?
            WHERE id = ?
        """, (f'Whale conflict - AI disagrees, keeping {old_signal}', track_id))
        conn.commit()
        conn.close()
        
        # Send conflict alert
        alert = format_whale_conflict_alert(trade, existing, ai_result)
        send_telegram(alert)


def format_whale_confirms_alert(trade: dict, existing: dict) -> str:
    """Alert when whale confirms existing signal."""
    title = existing.get('question', '')[:50]
    whale_name = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    whale_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
    signal = existing['signal_type']
    
    lines = [
        f"✅ <b>WHALE CONFIRMS SIGNAL</b>",
        f"",
        f"<b>{title}...</b>",
        f"",
        f"📊 Existing: <b>{signal}</b>",
        f"🐋 Whale: <b>{whale_name}</b> ${whale_size:,.0f}",
        f"",
        f"<i>Whale agrees with Oracle Sentinel!</i>",
        f"",
        f"🤖 <i>Oracle Sentinel — Whale Confirmed</i>"
    ]
    return "\n".join(lines)


def format_whale_update_alert(trade: dict, existing: dict, ai_result: dict, new_signal: str) -> str:
    """Alert when signal is updated after whale + AI agree."""
    title = existing.get('question', '')[:50]
    whale_name = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    whale_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
    old_signal = existing['signal_type']
    ai_prob = ai_result.get('ai_probability', 0.5)
    
    lines = [
        f"🔄 <b>SIGNAL UPDATED</b>",
        f"",
        f"<b>{title}...</b>",
        f"",
        f"📊 Was: <b>{old_signal}</b>",
        f"📊 Now: <b>{new_signal}</b>",
        f"",
        f"🐋 Whale: <b>{whale_name}</b> ${whale_size:,.0f}",
        f"🧠 AI: {ai_prob*100:.0f}%",
        f"",
        f"<i>Whale + AI aligned → Signal updated</i>",
        f"",
        f"🤖 <i>Oracle Sentinel — Whale Intelligence</i>"
    ]
    return "\n".join(lines)


def format_whale_conflict_alert(trade: dict, existing: dict, ai_result: dict) -> str:
    """Alert when AI disagrees with whale (AI wins)."""
    title = existing.get('question', '')[:50]
    whale_name = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
    whale_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
    whale_outcome = trade.get('outcome', '?')
    old_signal = existing['signal_type']
    ai_prob = ai_result.get('ai_probability', 0.5)
    
    lines = [
        f"⚠️ <b>WHALE vs AI CONFLICT</b>",
        f"",
        f"<b>{title}...</b>",
        f"",
        f"📊 Signal: <b>{old_signal}</b>",
        f"🐋 Whale: <b>{whale_name}</b> BUY {whale_outcome} ${whale_size:,.0f}",
        f"🧠 AI: {ai_prob*100:.0f}% (disagrees)",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🤖 <b>AI WINS - SIGNAL UNCHANGED</b>",
        f"Keeping: {old_signal}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"<i>AI analyzed whale intel but still disagrees</i>",
        f"",
        f"🤖 <i>Oracle Sentinel — AI Decision Final</i>"
    ]
    return "\n".join(lines)

def check_whale_ai_alignment(trade: dict, ai_result: dict) -> dict:
    """
    Check if whale action aligns with AI assessment.
    Returns alignment status and recommended action.
    Only processes BUY trades - SELL trades are handled separately.
    """
    if not ai_result:
        return {'aligned': False, 'reason': 'AI analysis failed'}
    
    whale_side = trade.get('side', '').upper()  # BUY or SELL
    
    # Only track BUY trades - SELL handled by check_whale_exit
    if whale_side != 'BUY':
        return {'aligned': False, 'reason': 'Only tracking BUY trades'}
    whale_outcome = trade.get('outcome', '')  # Yes, No, or specific outcome
    ai_prob = ai_result.get('ai_probability', 0.5)
    
    # Normalize outcome
    outcome_lower = whale_outcome.lower() if whale_outcome else ''
    is_yes_outcome = outcome_lower in ('yes', 'true', '1') or 'yes' in outcome_lower
    is_no_outcome = outcome_lower in ('no', 'false', '0') or 'no' in outcome_lower
    
    # Determine whale's directional bet
    # BUY YES = bullish, BUY NO = bearish, SELL YES = bearish, SELL NO = bullish
    if whale_side == 'BUY':
        whale_bullish = is_yes_outcome
    else:  # SELL
        whale_bullish = is_no_outcome
    
    # Check alignment
    if whale_bullish:
        # Whale is bullish (betting YES)
        if ai_prob >= 0.60:
            return {
                'aligned': True,
                'signal': 'BUY_YES',
                'reason': f'Whale bullish + AI {ai_prob*100:.0f}% YES (aligned)',
                'whale_direction': 'BULLISH'
            }
        elif ai_prob <= 0.40:
            return {
                'aligned': False,
                'signal': None,
                'reason': f'Whale bullish but AI only {ai_prob*100:.0f}% YES (conflict)',
                'whale_direction': 'BULLISH'
            }
        else:
            return {
                'aligned': False,
                'signal': None,
                'reason': f'Whale bullish but AI neutral {ai_prob*100:.0f}% (uncertain)',
                'whale_direction': 'BULLISH'
            }
    else:
        # Whale is bearish (betting NO)
        if ai_prob <= 0.40:
            return {
                'aligned': True,
                'signal': 'BUY_NO',
                'reason': f'Whale bearish + AI {ai_prob*100:.0f}% YES (aligned)',
                'whale_direction': 'BEARISH'
            }
        elif ai_prob >= 0.60:
            return {
                'aligned': False,
                'signal': None,
                'reason': f'Whale bearish but AI {ai_prob*100:.0f}% YES (conflict)',
                'whale_direction': 'BEARISH'
            }
        else:
            return {
                'aligned': False,
                'signal': None,
                'reason': f'Whale bearish but AI neutral {ai_prob*100:.0f}% (uncertain)',
                'whale_direction': 'BEARISH'
            }


def save_whale_confirmed_signal(trade: dict, ai_result: dict, alignment: dict) -> int:
    """
    Save whale-confirmed signal to prediction_tracking via AccuracyTracker.
    Returns tracking ID or None.
    """
    if not alignment.get('aligned') or not alignment.get('signal'):
        return None
    
    try:
        # Find market_id from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        title = trade.get('title', '')
        slug = trade.get('eventSlug', '')
        
        cursor.execute("""
            SELECT id FROM markets 
            WHERE slug = ? OR question LIKE ?
            LIMIT 1
        """, (slug, f'%{title[:50]}%'))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            print(f"  ⚠ Market not found for tracking")
            return None
        
        market_id = row[0]
        
        # Prepare result dict for accuracy_tracker
        result = {
            'recommendation': alignment['signal'],
            'ai_probability': ai_result.get('ai_probability', 0),
            'market_price': ai_result.get('market_price', 0),
            'edge': ai_result.get('edge', 0),
            'confidence': ai_result.get('confidence', 'MEDIUM'),
            'signal_source': 'whale_confirmed'
        }
        
        # Use AccuracyTracker to record
        tracker = AccuracyTracker()
        opp_id = ai_result.get('opportunity_id', 0)
        track_id = tracker.record_prediction(opp_id, market_id, result)
        
        if track_id:
            # Update with whale-specific info
            whale_trader = trade.get('name') or trade.get('pseudonym') or 'Anonymous'
            whale_size = float(trade.get('size', 0)) * float(trade.get('price', 0))
            whale_price = float(trade.get('price', 0))
            whale_tx = trade.get('transactionHash', '')
            
            cursor.execute("""
                UPDATE prediction_tracking 
                SET whale_trader = ?,
                    whale_trade_size = ?,
                    whale_entry_price = ?,
                    whale_tx_hash = ?,
                    whale_status = 'HOLDING'
                WHERE id = ?
            """, (whale_trader, whale_size, whale_price, whale_tx, track_id))
            conn.commit()
            
            print(f"  📊 Tracked as whale-confirmed signal #{track_id}")
            print(f"  🐋 Whale: {whale_trader} | ${whale_size:,.0f} | {whale_price:.2%}")
        
        conn.close()
        return track_id
        
    except Exception as e:
        print(f"  ❌ Failed to save whale-confirmed signal: {e}")
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

        # Check if this is a whale EXIT from a tracked market
        if trade.get('side', '').upper() == 'SELL' and value_usd >= MEGA_WHALE_THRESHOLD:
            tracked_info = check_whale_exit(trade)
            if tracked_info:
                handle_whale_exit(trade, tracked_info)
                mark_as_alerted(trade)
                alerts_sent += 1
                time.sleep(1)
                continue  # Skip normal processing
        
        # Run AI analysis for mega whales ($20K+) - only BUY trades
        ai_analysis = None
        if value_usd >= MEGA_WHALE_THRESHOLD and trade.get('side', '').upper() == 'BUY':
            print(f"  💎 MEGA WHALE detected! Running AI analysis...")
            ai_analysis = analyze_mega_whale(trade)
            
            # Check alignment and track if aligned
            if ai_analysis:
                alignment = check_whale_ai_alignment(trade, ai_analysis)
                ai_analysis['alignment'] = alignment
                print(f"  🔍 Alignment: {alignment.get('reason', 'Unknown')}")
                
                # Check if market already has a tracked signal
                existing = check_existing_signal(trade)
                
                if existing:
                    # Market already tracked - handle confirmation or conflict
                    print(f"  📊 Market already tracked: {existing['signal_type']}")
                    handle_existing_signal(trade, existing, ai_analysis, alignment)
                elif alignment.get('aligned'):
                    # New market - save whale-confirmed signal
                    save_whale_confirmed_signal(trade, ai_analysis, alignment)
        
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
