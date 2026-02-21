#!/usr/bin/env python3
"""
Oracle Sentinel - Price Updater
Fetches latest prices for all tracked markets
Primary: Jupiter Prediction API
"""

import sqlite3
import os
import json
import time
from datetime import datetime
from jupiter_prediction_client import JupiterPredictionClient

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class PriceUpdater:
    """Updates prices for tracked markets using Jupiter API"""

    def __init__(self):
        self.jupiter = JupiterPredictionClient()
        self.db_path = DB_PATH

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'price_updater', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    def get_markets_to_update(self) -> list:
        """Get all active markets from database"""
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, polymarket_id, question, outcome_prices
            FROM markets
            WHERE active = 1
              AND closed = 0
              AND (end_date IS NULL OR end_date > datetime('now'))
              AND polymarket_id IS NOT NULL
              AND polymarket_id != ''
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_market_price_jupiter(self, market: dict) -> bool:
        """Update price for a Jupiter market (POLY-XXXXXX format)"""
        market_id = market['polymarket_id']
        
        try:
            # Fetch market data from Jupiter
            jupiter_market = self.jupiter.get_market_by_id(market_id)
            
            if not jupiter_market:
                return False
            
            # Extract prices
            pricing = jupiter_market.get('pricing', {})
            yes_price = (pricing.get('buyYesPriceUsd', 0) or 0) / 1_000_000
            no_price = (pricing.get('buyNoPriceUsd', 0) or 0) / 1_000_000
            
            if yes_price == 0 and no_price == 0:
                return False
            
            # Update database
            conn = self._get_db()
            cursor = conn.cursor()
            
            # Update market outcome_prices
            new_prices = json.dumps([yes_price, no_price])
            cursor.execute('''
                UPDATE markets 
                SET outcome_prices = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_prices, market['id']))
            
            # Save price history
            cursor.execute('''
                INSERT INTO prices (market_id, token_id, price, bid, ask, spread)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (market['id'], market_id, yes_price, None, None, None))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            # Uncomment for debug:
            # print(f"   Debug error for {market_id}: {e}")
            return False

    def update_all_prices(self) -> dict:
        """Update prices for all tracked markets"""
        self._log('INFO', "Starting Jupiter price update...")

        markets = self.get_markets_to_update()
        
        # Separate Jupiter vs legacy Polymarket markets
        jupiter_markets = [m for m in markets if m['polymarket_id'].startswith('POLY-')]
        legacy_markets = [m for m in markets if not m['polymarket_id'].startswith('POLY-')]
        
        self._log('INFO', f"Found {len(jupiter_markets)} Jupiter markets, {len(legacy_markets)} legacy markets")

        success = 0
        failed = 0

        # Update Jupiter markets
        for i, market in enumerate(jupiter_markets):
            if self.update_market_price_jupiter(market):
                success += 1
            else:
                failed += 1

            # Rate limiting
            if (i + 1) % 20 == 0:
                self._log('INFO', f"Progress: {i+1}/{len(jupiter_markets)}")
                time.sleep(0.5)

        self._log('INFO', f"Jupiter price update complete: {success} success, {failed} failed")
        
        # Note: Legacy Polymarket markets will be updated by resolve_legacy_polymarket.py
        if legacy_markets:
            self._log('INFO', f"Skipped {len(legacy_markets)} legacy Polymarket markets (use resolve_legacy_polymarket.py)")

        return {
            'total': len(jupiter_markets),
            'success': success,
            'failed': failed,
            'legacy_skipped': len(legacy_markets),
            'timestamp': datetime.now().isoformat()
        }

    def get_price_changes(self, hours: int = 1) -> list:
        """Get markets with significant price changes"""
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            WITH latest AS (
                SELECT market_id, token_id, price, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY market_id ORDER BY timestamp DESC) as rn
                FROM prices
            ),
            older AS (
                SELECT market_id, token_id, price, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY market_id ORDER BY timestamp DESC) as rn
                FROM prices
                WHERE timestamp < datetime('now', ?)
            )
            SELECT
                l.market_id,
                l.token_id,
                l.price as current_price,
                o.price as old_price,
                (l.price - o.price) as change,
                m.question
            FROM latest l
            JOIN older o ON l.market_id = o.market_id AND o.rn = 1
            JOIN markets m ON l.market_id = m.id
            WHERE l.rn = 1
            AND ABS(l.price - o.price) > 0.02
            ORDER BY ABS(l.price - o.price) DESC
            LIMIT 10
        ''', (f'-{hours} hours',))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'market_id': row[0],
                'token_id': row[1],
                'current_price': row[2],
                'old_price': row[3],
                'change': row[4],
                'change_pct': (row[4] / row[3] * 100) if row[3] else 0,
                'question': row[5]
            }
            for row in rows
        ]


def main():
    """Run price update"""
    print("="*60)
    print("💰 Oracle Sentinel - Jupiter Price Updater")
    print("="*60)

    updater = PriceUpdater()

    # Update prices
    print("\n💵 Updating prices from Jupiter...")
    result = updater.update_all_prices()

    print(f"\n📈 Results:")
    print(f"   Jupiter markets: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    print(f"   Legacy skipped: {result['legacy_skipped']}")

    # Show price changes if any
    print("\n📊 Recent price movements (>2%):")
    changes = updater.get_price_changes(hours=1)

    if changes:
        for c in changes[:5]:
            direction = "📈" if c['change'] > 0 else "📉"
            print(f"   {direction} {c['question'][:40]}...")
            print(f"      {c['old_price']:.2%} → {c['current_price']:.2%} ({c['change']:+.2%})")
    else:
        print("   No significant changes in the last hour")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
