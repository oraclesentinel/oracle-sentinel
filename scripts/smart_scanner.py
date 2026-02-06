#!/usr/bin/env python3
"""
Smart Scanner - Adaptive Intelligence Layer
Detects volume spikes and price movements, triggers instant analysis
Runs every 10 minutes (offset menit 03: 03, 13, 23, 33, 43, 53)

Cron: 3-53/10 * * * * cd /root/oracle-sentinel/scripts && python3 smart_scanner.py
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import BOT_TOKEN, CHAT_IDS
from news_fetcher import NewsFetcher
from ai_brain import AIBrain
from accuracy_tracker import AccuracyTracker

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'smart_scanner.log')

# Thresholds
VOLUME_SPIKE_THRESHOLD = 0.50  # 50% increase
PRICE_MOVEMENT_THRESHOLD = 0.10  # 10% change
LOOKBACK_HOURS = 1  # Compare vs 1 hour ago

# Limits
MAX_MARKETS_TO_ANALYZE = 5  # Max markets per run to avoid overload


class SmartScanner:
    """
    Adaptive Intelligence Scanner
    - Monitors volume spikes
    - Monitors price movements
    - Triggers full analysis for new opportunities
    """

    def __init__(self):
        self.db_path = DB_PATH
        self.news_fetcher = NewsFetcher()
        self.ai_brain = AIBrain()
        self.accuracy_tracker = AccuracyTracker()
        self._ensure_tables()

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _log(self, message: str):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{ts}] {message}"
        print(line)
        try:
            with open(LOG_PATH, 'a') as f:
                f.write(line + '\n')
        except:
            pass
        # Also log to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                ('INFO', 'smart_scanner', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    def _ensure_tables(self):
        """Create volume_snapshots table if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS volume_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id INTEGER NOT NULL,
                volume_24h REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (market_id) REFERENCES markets(id)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_volume_snapshots_market_time
            ON volume_snapshots(market_id, timestamp DESC)
        ''')
        conn.commit()
        conn.close()

    # =========================================================
    # STEP 1: SAVE VOLUME SNAPSHOTS
    # =========================================================
    def save_volume_snapshots(self) -> int:
        """Save current volume_24h for all active markets"""
        conn = self._get_db()
        cursor = conn.cursor()

        # Get all active, non-closed, non-expired markets
        cursor.execute('''
            SELECT id, volume_24h
            FROM markets
            WHERE active = 1 
              AND closed = 0
              AND (end_date IS NULL OR end_date > datetime('now'))
        ''')
        markets = cursor.fetchall()

        saved = 0
        for market in markets:
            market_id = market['id']
            volume_24h = market['volume_24h'] or 0

            cursor.execute('''
                INSERT INTO volume_snapshots (market_id, volume_24h)
                VALUES (?, ?)
            ''', (market_id, volume_24h))
            saved += 1

        conn.commit()
        conn.close()
        
        self._log(f"Saved {saved} volume snapshots")
        return saved

    # =========================================================
    # STEP 2: DETECT VOLUME SPIKES
    # =========================================================
    def detect_volume_spikes(self) -> List[Dict]:
        """Find markets with volume spike > threshold vs 1 hour ago"""
        conn = self._get_db()
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(hours=LOOKBACK_HOURS)

        # Get current volume and volume 1 hour ago
        cursor.execute('''
            WITH current_vol AS (
                SELECT market_id, volume_24h
                FROM volume_snapshots
                WHERE timestamp = (
                    SELECT MAX(timestamp) FROM volume_snapshots vs2 
                    WHERE vs2.market_id = volume_snapshots.market_id
                )
            ),
            old_vol AS (
                SELECT market_id, volume_24h
                FROM volume_snapshots
                WHERE timestamp <= ?
                  AND timestamp = (
                    SELECT MAX(timestamp) FROM volume_snapshots vs2 
                    WHERE vs2.market_id = volume_snapshots.market_id
                      AND vs2.timestamp <= ?
                )
            )
            SELECT 
                m.id as market_id,
                m.question,
                m.slug,
                cv.volume_24h as current_volume,
                ov.volume_24h as old_volume,
                CASE WHEN ov.volume_24h > 0 
                     THEN (cv.volume_24h - ov.volume_24h) / ov.volume_24h 
                     ELSE 0 
                END as volume_change
            FROM markets m
            JOIN current_vol cv ON cv.market_id = m.id
            LEFT JOIN old_vol ov ON ov.market_id = m.id
            WHERE m.active = 1 
              AND m.closed = 0
              AND (m.end_date IS NULL OR m.end_date > datetime('now'))
              AND ov.volume_24h > 0
              AND cv.volume_24h > ov.volume_24h * (1 + ?)
            ORDER BY volume_change DESC
            LIMIT 20
        ''', (cutoff.isoformat(), cutoff.isoformat(), VOLUME_SPIKE_THRESHOLD))

        spikes = []
        for row in cursor.fetchall():
            spikes.append({
                'market_id': row['market_id'],
                'question': row['question'],
                'slug': row['slug'],
                'current_volume': row['current_volume'],
                'old_volume': row['old_volume'],
                'volume_change': row['volume_change'],
                'trigger': 'volume_spike',
                'trigger_detail': f"+{row['volume_change']*100:.0f}% volume"
            })

        conn.close()
        
        if spikes:
            self._log(f"Found {len(spikes)} volume spikes")
        return spikes

    # =========================================================
    # STEP 3: DETECT PRICE MOVEMENTS
    # =========================================================
    def detect_price_movements(self) -> List[Dict]:
        """Find markets with price movement > threshold vs 1 hour ago"""
        conn = self._get_db()
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(hours=LOOKBACK_HOURS)

        # Get markets with price history
        cursor.execute('''
            SELECT DISTINCT m.id, m.question, m.slug, m.outcome_prices, m.outcomes
            FROM markets m
            JOIN prices p ON p.market_id = m.id
            WHERE m.active = 1 
              AND m.closed = 0
              AND (m.end_date IS NULL OR m.end_date > datetime('now'))
        ''')
        markets = cursor.fetchall()

        movements = []
        for market in markets:
            market_id = market['id']

            # Get current price (latest)
            cursor.execute('''
                SELECT price FROM prices 
                WHERE market_id = ? 
                ORDER BY timestamp DESC LIMIT 1
            ''', (market_id,))
            current_row = cursor.fetchone()

            # Get old price (1 hour ago or closest before)
            cursor.execute('''
                SELECT price FROM prices 
                WHERE market_id = ? AND timestamp <= ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (market_id, cutoff.isoformat()))
            old_row = cursor.fetchone()

            if current_row and old_row:
                current_price = current_row['price'] or 0
                old_price = old_row['price'] or 0

                if old_price > 0:
                    price_change = abs(current_price - old_price)

                    if price_change >= PRICE_MOVEMENT_THRESHOLD:
                        direction = "up" if current_price > old_price else "down"
                        movements.append({
                            'market_id': market_id,
                            'question': market['question'],
                            'slug': market['slug'],
                            'current_price': current_price,
                            'old_price': old_price,
                            'price_change': price_change,
                            'direction': direction,
                            'trigger': 'price_movement',
                            'trigger_detail': f"{direction} {price_change*100:.0f}% ({old_price*100:.0f}% -> {current_price*100:.0f}%)"
                        })

        conn.close()

        if movements:
            self._log(f"Found {len(movements)} price movements")
        return movements

    # =========================================================
    # STEP 4: FILTER - SKIP ALREADY TRACKED
    # =========================================================
    def filter_already_tracked(self, markets: List[Dict]) -> List[Dict]:
        """Remove markets that are already in prediction_tracking (unresolved)"""
        if not markets:
            return []

        conn = self._get_db()
        cursor = conn.cursor()

        market_ids = [m['market_id'] for m in markets]
        placeholders = ','.join('?' * len(market_ids))

        # Get markets already tracked and not resolved
        cursor.execute(f'''
            SELECT DISTINCT market_id FROM prediction_tracking
            WHERE market_id IN ({placeholders})
              AND final_resolution IS NULL
        ''', market_ids)

        tracked_ids = set(row['market_id'] for row in cursor.fetchall())
        conn.close()

        filtered = [m for m in markets if m['market_id'] not in tracked_ids]

        skipped = len(markets) - len(filtered)
        if skipped > 0:
            self._log(f"Skipped {skipped} already-tracked markets")

        return filtered

    # =========================================================
    # STEP 5: FULL ANALYSIS
    # =========================================================
    def full_analyze(self, market: Dict) -> Optional[Dict]:
        """
        Run full analysis pipeline:
        1. Fetch fresh news
        2. AI analysis
        3. Track prediction if BUY signal
        """
        market_id = market['market_id']
        question = market['question']
        trigger = market.get('trigger_detail', 'spike detected')

        self._log(f"")
        self._log(f"{'='*50}")
        self._log(f"ANALYZING: {question[:50]}...")
        self._log(f"Trigger: {trigger}")

        try:
            # Step 1: Fetch fresh news
            self._log(f"  Fetching news...")
            news_result = self.news_fetcher.fetch_for_market(market_id, question)
            articles_count = news_result.get('stats', {}).get('saved', 0)
            self._log(f"  Found {articles_count} articles")

            # Step 2: AI Analysis
            self._log(f"  Running AI analysis...")
            result = self.ai_brain.analyze_market(market_id)

            if not result or result.get('status') == 'skipped':
                self._log(f"  Analysis skipped: {result.get('reason', 'unknown')}")
                return None

            recommendation = result.get('recommendation', 'SKIP')
            ai_prob = result.get('ai_probability', 0)
            market_price = result.get('market_price', 0)
            edge = result.get('edge', 0)
            confidence = result.get('confidence', 'LOW')

            self._log(f"  AI Probability: {ai_prob*100:.1f}%")
            self._log(f"  Market Price: {market_price*100:.1f}%")
            self._log(f"  Edge: {edge:+.1f}%")
            self._log(f"  Recommendation: {recommendation}")

            # Step 3: Track prediction if BUY signal
            if recommendation in ('BUY_YES', 'BUY_NO'):
                # Skip coin-flip zone
                if 0.45 <= market_price <= 0.55:
                    self._log(f"  Skipped: coin-flip zone ({market_price*100:.1f}%)")
                    return result

                opp_id = result.get('opportunity_id')
                if opp_id:
                    track_id = self.accuracy_tracker.record_prediction(opp_id, market_id, {
                        'recommendation': recommendation,
                        'ai_probability': ai_prob,
                        'market_price': market_price,
                        'edge': edge,
                        'confidence': confidence,
                        'question': question
                    })
                    if track_id:
                        self._log(f"  Tracked as prediction #{track_id}")
                        result['track_id'] = track_id

            result['trigger'] = market.get('trigger')
            result['trigger_detail'] = market.get('trigger_detail')
            return result

        except Exception as e:
            self._log(f"  ERROR: {e}")
            return None

    # =========================================================
    # STEP 6: TELEGRAM ALERT
    # =========================================================
    def send_telegram_alert(self, market: Dict, result: Dict):
        """Send Telegram alert for spike + analysis result"""
        question = market.get('question', 'Unknown')[:80]
        trigger_detail = market.get('trigger_detail', 'Spike detected')
        
        recommendation = result.get('recommendation', 'NO_TRADE')
        ai_prob = result.get('ai_probability', 0)
        market_price = result.get('market_price', 0)
        edge = result.get('edge', 0)
        confidence = result.get('confidence', 'LOW')
        reasoning = result.get('reasoning', '')[:200]
        slug = market.get('slug', '')

        # Signal indicator
        if recommendation == 'BUY_YES':
            signal_text = "[YES] BUY_YES"
        elif recommendation == 'BUY_NO':
            signal_text = "[NO] BUY_NO"
        else:
            signal_text = "[--] NO_TRADE"

        msg = f"""SPIKE ALERT + ANALYSIS

TRIGGER: {trigger_detail}

MARKET: {question}

ANALYSIS:
Market Price: {market_price*100:.1f}%
AI Probability: {ai_prob*100:.1f}%
Edge: {edge:+.1f}%
Confidence: {confidence}

SIGNAL: {signal_text}

REASONING: {reasoning}

Link: polymarket.com/event/{slug}

-- Oracle Sentinel Smart Scanner"""

        for chat_id in CHAT_IDS:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": msg,
                        "disable_web_page_preview": True
                    },
                    timeout=10
                )
            except Exception as e:
                self._log(f"Telegram error: {e}")

    # =========================================================
    # STEP 7: CLEANUP
    # =========================================================
    def cleanup_old_snapshots(self, hours: int = 24):
        """Delete volume snapshots older than X hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM volume_snapshots
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{hours} hours',))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            self._log(f"Cleaned up {deleted} old volume snapshots")

    # =========================================================
    # MAIN RUN
    # =========================================================
    def run(self):
        """Main function - run all checks"""
        self._log("")
        self._log("=" * 60)
        self._log("SMART SCANNER - Adaptive Intelligence")
        self._log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("=" * 60)

        # Step 1: Save volume snapshots
        self.save_volume_snapshots()

        # Step 2: Detect volume spikes
        volume_spikes = self.detect_volume_spikes()

        # Step 3: Detect price movements
        price_movements = self.detect_price_movements()

        # Combine and deduplicate
        all_markets = {}
        for m in volume_spikes:
            all_markets[m['market_id']] = m
        for m in price_movements:
            if m['market_id'] not in all_markets:
                all_markets[m['market_id']] = m
            else:
                # Combine triggers
                all_markets[m['market_id']]['trigger_detail'] += f" + {m['trigger_detail']}"

        markets_to_check = list(all_markets.values())
        self._log(f"Total markets with spikes/movements: {len(markets_to_check)}")

        if not markets_to_check:
            self._log("No spikes or movements detected. Done.")
            self.cleanup_old_snapshots()
            return

        # Step 4: Filter already tracked
        markets_to_analyze = self.filter_already_tracked(markets_to_check)

        if not markets_to_analyze:
            self._log("All spike markets already tracked. Done.")
            self.cleanup_old_snapshots()
            return

        # Limit to avoid overload
        if len(markets_to_analyze) > MAX_MARKETS_TO_ANALYZE:
            self._log(f"Limiting to {MAX_MARKETS_TO_ANALYZE} markets (of {len(markets_to_analyze)})")
            markets_to_analyze = markets_to_analyze[:MAX_MARKETS_TO_ANALYZE]

        self._log(f"Markets to analyze: {len(markets_to_analyze)}")

        # Step 5 & 6: Analyze and alert
        analyzed = 0
        signals = 0
        for market in markets_to_analyze:
            result = self.full_analyze(market)
            if result:
                analyzed += 1
                if result.get('recommendation') in ('BUY_YES', 'BUY_NO'):
                    signals += 1
                    self.send_telegram_alert(market, result)

        # Step 7: Cleanup
        self.cleanup_old_snapshots()

        # Summary
        self._log("")
        self._log("=" * 60)
        self._log(f"SUMMARY: Analyzed {analyzed} markets, {signals} signals generated")
        self._log("=" * 60)


if __name__ == '__main__':
    scanner = SmartScanner()
    scanner.run()
