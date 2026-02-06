#!/usr/bin/env python3
"""
Polymarket Intelligence System - Price Updater
Fetches latest prices for all tracked markets
"""

import sqlite3
import os
import json
import time
from datetime import datetime
from polymarket_client import PolymarketClient

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class PriceUpdater:
    """Updates prices for tracked markets"""
    
    def __init__(self):
        self.client = PolymarketClient()
        self.db_path = DB_PATH
    
    def _get_db(self):
        return sqlite3.connect(self.db_path)
    
    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
            (level, 'price_updater', message)
        )
        conn.commit()
        conn.close()
    
    def get_tokens_to_update(self) -> list:
        """Get all token IDs from database"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.market_id, t.token_id, t.outcome, m.question
            FROM tokens t
            JOIN markets m ON t.market_id = m.id
            WHERE m.active = 1 AND t.token_id IS NOT NULL AND t.token_id != ''
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'market_id': row[1],
                'token_id': row[2],
                'outcome': row[3],
                'question': row[4]
            }
            for row in rows
        ]
    
    def update_token_price(self, token: dict) -> bool:
        """Update price for a single token"""
        token_id = token['token_id']
        
        # Skip invalid token IDs
        if not token_id or len(str(token_id)) < 20:
            return False
        
        try:
            # Get midpoint price
            mid = self.client.get_midpoint(token_id)
            
            if mid is None or mid == 0:
                # Coba get price sebagai alternatif
                mid = self.client.get_price(token_id, "BUY")
            
            if mid is None:
                return False
            
            # Get spread if available
            bid = None
            ask = None
            try:
                spread_data = self.client.get_spread(token_id)
                if spread_data:
                    bid = float(spread_data.get('bid', 0) or 0)
                    ask = float(spread_data.get('ask', 0) or 0)
            except:
                pass  # Spread optional
            
            # Save to database
            conn = self._get_db()
            cursor = conn.cursor()
            
            # Update token current price
            cursor.execute(
                'UPDATE tokens SET price = ? WHERE id = ?',
                (mid, token['id'])
            )
            
            # Save price history
            spread = (ask - bid) if (ask and bid and ask > 0 and bid > 0) else None
            cursor.execute('''
                INSERT INTO prices (market_id, token_id, price, bid, ask, spread)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (token['market_id'], token_id, mid, bid, ask, spread))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            # Uncomment untuk debug:
            # print(f"   Debug error for {token_id[:20]}: {e}")
            return False
    
    def update_all_prices(self) -> dict:
        """Update prices for all tracked tokens"""
        self._log('INFO', "Starting price update...")
        
        tokens = self.get_tokens_to_update()
        self._log('INFO', f"Found {len(tokens)} tokens to update")
        
        success = 0
        failed = 0
        
        for i, token in enumerate(tokens):
            if self.update_token_price(token):
                success += 1
            else:
                failed += 1
            
            # Rate limiting - don't hammer the API
            if (i + 1) % 10 == 0:
                self._log('INFO', f"Progress: {i+1}/{len(tokens)}")
                time.sleep(1)  # Pause every 10 requests
        
        self._log('INFO', f"Price update complete: {success} success, {failed} failed")
        
        return {
            'total': len(tokens),
            'success': success,
            'failed': failed,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_price_changes(self, hours: int = 1) -> list:
        """Get markets with significant price changes"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get latest vs older prices
        cursor.execute('''
            WITH latest AS (
                SELECT market_id, token_id, price, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY token_id ORDER BY timestamp DESC) as rn
                FROM prices
            ),
            older AS (
                SELECT market_id, token_id, price, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY token_id ORDER BY timestamp DESC) as rn
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
            JOIN older o ON l.token_id = o.token_id AND o.rn = 1
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
    print("💰 Polymarket Price Updater")
    print("="*60)
    
    updater = PriceUpdater()
    
    # First sync markets if needed
    client = PolymarketClient()
    markets = client.get_all_markets()
    
    if len(markets) < 10:
        print("\n📊 Syncing markets first...")
        client.sync_markets(limit=50)
    
    # Update prices
    print("\n💵 Updating prices...")
    result = updater.update_all_prices()
    
    print(f"\n📈 Results:")
    print(f"   Total tokens: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    
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