#!/usr/bin/env python3
"""
Accuracy Tracker - Track prediction accuracy over time
Records every BUY signal, monitors price changes, and calculates P&L
"""

import os
import json
import sqlite3
import sys
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class AccuracyTracker:

    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_tables()

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'accuracy_tracker', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    # =========================================================
    # TABLE SETUP
    # =========================================================
    def _ensure_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                market_id INTEGER NOT NULL,
                polymarket_id TEXT,
                question TEXT,
                
                signal_type TEXT NOT NULL,
                ai_probability REAL,
                market_price_at_signal REAL,
                edge_at_signal REAL,
                confidence TEXT,
                
                price_after_1h REAL,
                price_after_6h REAL,
                price_after_24h REAL,
                price_after_48h REAL,
                price_after_7d REAL,
                
                snapshot_1h_at DATETIME,
                snapshot_6h_at DATETIME,
                snapshot_24h_at DATETIME,
                snapshot_48h_at DATETIME,
                snapshot_7d_at DATETIME,
                
                final_resolution TEXT,
                resolved_at DATETIME,
                
                hypothetical_pnl REAL,
                direction_correct INTEGER,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                market_end_date TEXT,
                
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
                FOREIGN KEY (market_id) REFERENCES markets(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_market ON prediction_tracking(market_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_created ON prediction_tracking(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_signal_type ON prediction_tracking(signal_type)')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accuracy_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_signals INTEGER DEFAULT 0,
                buy_yes_count INTEGER DEFAULT 0,
                buy_no_count INTEGER DEFAULT 0,
                resolved_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                accuracy_pct REAL,
                total_pnl REAL DEFAULT 0,
                avg_edge REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # =========================================================
    # RECORD NEW PREDICTION
    # =========================================================
    def record_prediction(self, opportunity_id: int, market_id: int, result: dict):
        recommendation = result.get('recommendation', '')
        if recommendation not in ('BUY_YES', 'BUY_NO'):
            return None

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT polymarket_id, question, end_date FROM markets WHERE id = ?',
            (market_id,)
        )
        row = cursor.fetchone()
        polymarket_id = row['polymarket_id'] if row else None
        question = row['question'] if row else result.get('question', '')
        end_date = row['end_date'] if row else ''

        # Check duplicate - only one signal per market (skip if already tracked and not resolved)
        cursor.execute('SELECT id FROM prediction_tracking WHERE market_id = ? AND final_resolution IS NULL', (market_id,))
        existing = cursor.fetchone()
        if existing:
            self._log('INFO', f'⏭ Skipping duplicate for market {market_id} (already tracked)')
            conn.close()
            return None

        try:
            signal_source = result.get('signal_source', 'scan')
            cursor.execute('''
                INSERT INTO prediction_tracking (
                    opportunity_id, market_id, polymarket_id, question,
                    signal_type, ai_probability, market_price_at_signal,
                    edge_at_signal, confidence, market_end_date, signal_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opportunity_id, market_id, polymarket_id, question,
                recommendation,
                result.get('ai_probability', 0),
                result.get('market_price', 0),
                result.get('edge', 0),
                result.get('confidence', 'LOW'),
                end_date,
                signal_source
            ))
            conn.commit()
            track_id = cursor.lastrowid
            self._log('INFO', f'📊 Tracked #{track_id}: {recommendation} "{question[:50]}..." (edge: {result.get("edge", 0):+.1f}%)')
            conn.close()
            return track_id
        except Exception as e:
            self._log('ERROR', f'Failed to record prediction: {e}')
            conn.close()
            return None

    # =========================================================
    # UPDATE PRICE SNAPSHOTS
    # =========================================================
    def update_snapshots(self):
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT pt.id, pt.market_id, pt.created_at, pt.signal_type,
                   pt.snapshot_1h_at, pt.snapshot_6h_at, 
                   pt.snapshot_24h_at, pt.snapshot_48h_at, pt.snapshot_7d_at,
                   pt.question
            FROM prediction_tracking pt
            WHERE pt.final_resolution IS NULL
        ''')

        predictions = cursor.fetchall()
        now = datetime.now()
        updated = 0

        for pred in predictions:
            try:
                created_at = datetime.fromisoformat(pred['created_at'])
            except (ValueError, TypeError):
                continue

            hours_since = (now - created_at).total_seconds() / 3600
            current_price = self._get_current_price(cursor, pred['market_id'])
            if current_price is None:
                continue

            updates = []
            params = []

            if hours_since >= 1 and pred['snapshot_1h_at'] is None:
                updates.append('price_after_1h = ?, snapshot_1h_at = ?')
                params.extend([current_price, now.isoformat()])

            if hours_since >= 6 and pred['snapshot_6h_at'] is None:
                updates.append('price_after_6h = ?, snapshot_6h_at = ?')
                params.extend([current_price, now.isoformat()])

            if hours_since >= 24 and pred['snapshot_24h_at'] is None:
                updates.append('price_after_24h = ?, snapshot_24h_at = ?')
                params.extend([current_price, now.isoformat()])

            if hours_since >= 48 and pred['snapshot_48h_at'] is None:
                updates.append('price_after_48h = ?, snapshot_48h_at = ?')
                params.extend([current_price, now.isoformat()])

            if hours_since >= 168 and pred['snapshot_7d_at'] is None:
                updates.append('price_after_7d = ?, snapshot_7d_at = ?')
                params.extend([current_price, now.isoformat()])

            if updates:
                sql = f"UPDATE prediction_tracking SET {', '.join(updates)} WHERE id = ?"
                params.append(pred['id'])
                cursor.execute(sql, params)
                updated += 1

        resolved = self._check_resolutions(cursor)
        conn.commit()
        conn.close()

        self.update_daily_stats()
        self._log('INFO', f'Snapshots: {updated} updated, {resolved} resolved (of {len(predictions)} tracked)')
        return {'updated': updated, 'resolved': resolved, 'total_tracked': len(predictions)}

    def _get_current_price(self, cursor, market_id: int):
        cursor.execute('SELECT outcome_prices FROM markets WHERE id = ?', (market_id,))
        row = cursor.fetchone()
        if not row:
            return None
        try:
            prices = json.loads(row['outcome_prices'])
            return float(prices[0]) if prices else None
        except:
            return None

    # =========================================================
    # CHECK RESOLUTIONS
    # =========================================================
    def _check_resolutions(self, cursor) -> int:
        cursor.execute('''
            SELECT pt.id, pt.market_id, pt.signal_type, 
                   pt.market_price_at_signal, pt.question,
                   m.closed, m.outcome_prices
            FROM prediction_tracking pt
            JOIN markets m ON m.id = pt.market_id
            WHERE pt.final_resolution IS NULL
        ''')

        resolved_count = 0
        for row in cursor.fetchall():
            try:
                prices = json.loads(row['outcome_prices'])
                yes_final = float(prices[0])
            except:
                continue

            # Only resolve if market is actually closed
            if not row['closed']:
                continue
                
            if yes_final >= 0.95:
                resolution = 'YES'
            elif yes_final <= 0.05:
                resolution = 'NO'
            else:
                continue

            pnl = self._calculate_pnl(row['signal_type'], row['market_price_at_signal'], resolution)
            direction_correct = 1 if (
                (row['signal_type'] == 'BUY_YES' and resolution == 'YES') or
                (row['signal_type'] == 'BUY_NO' and resolution == 'NO')
            ) else 0

            cursor.execute('''
                UPDATE prediction_tracking 
                SET final_resolution = ?, resolved_at = ?, hypothetical_pnl = ?, direction_correct = ?
                WHERE id = ?
            ''', (resolution, datetime.now().isoformat(), pnl, direction_correct, row['id']))

            resolved_count += 1
            emoji = "✅" if direction_correct else "❌"
            self._log('INFO', f'  {emoji} Resolved: "{row["question"][:40]}..." → {resolution} | P&L: ${pnl:+.2f}')

        return resolved_count

    def _calculate_pnl(self, signal_type: str, entry_price: float, resolution: str) -> float:
        """Hypothetical P&L on $100 bet"""
        bet = 100.0
        if signal_type == 'BUY_YES':
            return round(bet * (1.0 - entry_price) / entry_price, 2) if resolution == 'YES' else -bet
        elif signal_type == 'BUY_NO':
            no_price = 1.0 - entry_price
            return round(bet * (1.0 - no_price) / no_price, 2) if resolution == 'NO' else -bet
        return 0.0


    # =========================================================
    # UPDATE DAILY STATS
    # =========================================================
    def update_daily_stats(self):
        """
        Aggregate prediction data into accuracy_daily table.
        Called after resolutions are checked.
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT DATE(created_at) as date FROM prediction_tracking ORDER BY date')
        dates = [row['date'] for row in cursor.fetchall()]
        updated = 0
        
        for date in dates:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN signal_type = 'BUY_YES' THEN 1 ELSE 0 END) as buy_yes_count,
                    SUM(CASE WHEN signal_type = 'BUY_NO' THEN 1 ELSE 0 END) as buy_no_count,
                    SUM(CASE WHEN final_resolution IS NOT NULL THEN 1 ELSE 0 END) as resolved_count,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                    SUM(COALESCE(hypothetical_pnl, 0)) as total_pnl,
                    AVG(edge_at_signal) as avg_edge
                FROM prediction_tracking
                WHERE DATE(created_at) = ?
            ''', (date,))
            
            row = cursor.fetchone()
            if not row or row['total_signals'] == 0:
                continue
            
            resolved = row['resolved_count'] or 0
            correct = row['correct_count'] or 0
            accuracy_pct = (correct / resolved * 100) if resolved > 0 else None
            
            cursor.execute('''
                INSERT INTO accuracy_daily (date, total_signals, buy_yes_count, buy_no_count,
                    resolved_count, correct_count, accuracy_pct, total_pnl, avg_edge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_signals = excluded.total_signals,
                    buy_yes_count = excluded.buy_yes_count,
                    buy_no_count = excluded.buy_no_count,
                    resolved_count = excluded.resolved_count,
                    correct_count = excluded.correct_count,
                    accuracy_pct = excluded.accuracy_pct,
                    total_pnl = excluded.total_pnl,
                    avg_edge = excluded.avg_edge
            ''', (date, row['total_signals'], row['buy_yes_count'] or 0, row['buy_no_count'] or 0,
                  resolved, correct, accuracy_pct, row['total_pnl'] or 0, row['avg_edge']))
            updated += 1
        
        conn.commit()
        conn.close()
        self._log('INFO', f'Daily stats updated: {updated} days')
        return updated

    # =========================================================
    # REPORT
    # =========================================================
    def generate_report(self) -> dict:
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as cnt FROM prediction_tracking')
        total = cursor.fetchone()['cnt']

        if total == 0:
            conn.close()
            return {'total': 0, 'message': 'No predictions tracked yet'}

        cursor.execute('SELECT signal_type, COUNT(*) as cnt FROM prediction_tracking GROUP BY signal_type')
        by_type = {row['signal_type']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute('''
            SELECT COUNT(*) as cnt, SUM(direction_correct) as correct,
                   SUM(hypothetical_pnl) as total_pnl, AVG(hypothetical_pnl) as avg_pnl
            FROM prediction_tracking WHERE final_resolution IS NOT NULL
        ''')
        res = cursor.fetchone()
        resolved_count = res['cnt']
        correct_count = res['correct'] or 0
        total_pnl = res['total_pnl'] or 0
        avg_pnl = res['avg_pnl'] or 0
        accuracy = (correct_count / resolved_count * 100) if resolved_count > 0 else 0

        # Price movement for unresolved
        cursor.execute('''
            SELECT signal_type, market_price_at_signal,
                   price_after_7d, price_after_48h, price_after_24h, price_after_6h, price_after_1h
            FROM prediction_tracking WHERE final_resolution IS NULL
        ''')
        moving_right = moving_wrong = 0
        for pred in cursor.fetchall():
            latest = None
            for col in ['price_after_7d', 'price_after_48h', 'price_after_24h', 'price_after_6h', 'price_after_1h']:
                if pred[col] is not None:
                    latest = pred[col]
                    break
            if latest is None:
                continue
            entry = pred['market_price_at_signal']
            if (pred['signal_type'] == 'BUY_YES' and latest > entry) or \
               (pred['signal_type'] == 'BUY_NO' and latest < entry):
                moving_right += 1
            else:
                moving_wrong += 1

        # By confidence
        cursor.execute('''
            SELECT confidence, COUNT(*) as cnt,
                   SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                   SUM(CASE WHEN final_resolution IS NOT NULL THEN 1 ELSE 0 END) as resolved
            FROM prediction_tracking GROUP BY confidence
        ''')
        by_confidence = {}
        for row in cursor.fetchall():
            r = row['resolved']
            c = row['correct'] or 0
            by_confidence[row['confidence']] = {
                'total': row['cnt'], 'resolved': r, 'correct': c,
                'accuracy': round(c / r * 100, 1) if r > 0 else None
            }

        conn.close()

        return {
            'total_predictions': total,
            'by_signal_type': by_type,
            'resolved': {
                'count': resolved_count, 'correct': correct_count,
                'accuracy_pct': round(accuracy, 1),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl_per_trade': round(avg_pnl, 2)
            },
            'unresolved': {
                'count': total - resolved_count,
                'moving_right': moving_right, 'moving_wrong': moving_wrong
            },
            'by_confidence': by_confidence
        }

    def print_report(self):
        report = self.generate_report()

        print()
        print("=" * 60)
        print("📊 ORACLE SENTINEL - ACCURACY REPORT")
        print("=" * 60)

        if report.get('total_predictions', 0) == 0:
            print("\n  No predictions tracked yet. Run scan_more.py first.")
            print("=" * 60)
            return report

        total = report['total_predictions']
        res = report['resolved']
        unres = report['unresolved']

        print(f"\n  Total predictions tracked: {total}")
        print(f"  BUY_YES: {report['by_signal_type'].get('BUY_YES', 0)} | BUY_NO: {report['by_signal_type'].get('BUY_NO', 0)}")

        print(f"\n  📋 RESOLVED: {res['count']}/{total}")
        if res['count'] > 0:
            emoji = "✅" if res['accuracy_pct'] >= 50 else "❌"
            print(f"  {emoji} Accuracy: {res['accuracy_pct']}% ({res['correct']}/{res['count']} correct)")
            pnl_emoji = "💰" if res['total_pnl'] > 0 else "📉"
            print(f"  {pnl_emoji} Total P&L: ${res['total_pnl']:+.2f} (hypothetical $100/bet)")
            print(f"     Avg P&L per trade: ${res['avg_pnl_per_trade']:+.2f}")

        print(f"\n  ⏳ UNRESOLVED: {unres['count']}")
        if unres['moving_right'] + unres['moving_wrong'] > 0:
            total_m = unres['moving_right'] + unres['moving_wrong']
            pct = unres['moving_right'] / total_m * 100
            print(f"     Price moving our way: {unres['moving_right']}/{total_m} ({pct:.0f}%)")

        print(f"\n  📈 BY CONFIDENCE:")
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            if conf in report['by_confidence']:
                d = report['by_confidence'][conf]
                acc = f"{d['accuracy']}%" if d['accuracy'] is not None else "pending"
                print(f"     {conf}: {d['total']} predictions, {d['resolved']} resolved, accuracy: {acc}")

        print(f"\n{'='*60}")
        return report


if __name__ == '__main__':
    tracker = AccuracyTracker()

    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        print("🔄 Updating snapshots...")
        result = tracker.update_snapshots()
        print(f"   Updated: {result['updated']}, Resolved: {result['resolved']}")

    tracker.print_report()