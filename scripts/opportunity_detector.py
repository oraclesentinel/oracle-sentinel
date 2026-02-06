#!/usr/bin/env python3
"""
Opportunity Detector - Core Analysis Engine
Detects mispriced markets and trading opportunities
"""

import sqlite3
import json
import os
import time
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class OpportunityDetector:
    """
    Analyzes Polymarket data to find opportunities:
    1. Extreme spreads (wide bid-ask = profit opportunity)
    2. Price momentum (rapid movement = trend signal)
    3. Mispriced complements (Yes + No != $1.00)
    4. Volume spikes (sudden interest = news catalyst)
    5. Near-expiry value (markets about to resolve with edge)
    """

    def __init__(self):
        self.min_liquidity = 10000      # $10k minimum liquidity
        self.min_volume = 50000         # $50k minimum volume
        self.spread_threshold = 0.03    # 3% spread = opportunity
        self.momentum_threshold = 0.05  # 5% price change = signal
        self.complement_threshold = 0.02 # 2% complement gap
        self.volume_spike_mult = 3.0    # 3x average volume

    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def _log(self, level, message):
        """Log to database and console"""
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'opportunity_detector', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    # =========================================================
    # DETECTOR 1: Complement Mismatch (Yes + No != $1.00)
    # =========================================================
    def detect_complement_mismatch(self):
        """
        If Yes=$0.60 and No=$0.35, total=$0.95
        That's $0.05 free money (buy both = guaranteed $1.00)
        
        If Yes=$0.55 and No=$0.50, total=$1.05
        That's $0.05 overpriced (sell both if possible)
        """
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT m.id, m.question, m.volume_24h, m.liquidity,
                   GROUP_CONCAT(t.outcome || ':' || t.price, '|') as token_data
            FROM markets m
            JOIN tokens t ON t.market_id = m.id
            WHERE m.active = 1 AND m.closed = 0
            GROUP BY m.id
            HAVING COUNT(t.id) = 2
        ''')

        opportunities = []
        for row in cursor.fetchall():
            market_id, question, volume, liquidity, token_data = row

            # Parse token data
            tokens = {}
            for td in token_data.split('|'):
                parts = td.split(':')
                if len(parts) == 2:
                    tokens[parts[0]] = float(parts[1])

            if len(tokens) < 2:
                continue

            total = sum(tokens.values())
            gap = abs(total - 1.0)

            if gap >= self.complement_threshold:
                direction = "UNDERPRICED" if total < 1.0 else "OVERPRICED"
                opportunities.append({
                    'market_id': market_id,
                    'type': 'complement_mismatch',
                    'question': question,
                    'tokens': tokens,
                    'total': round(total, 4),
                    'gap': round(gap, 4),
                    'direction': direction,
                    'edge_pct': round(gap * 100, 2),
                    'volume_24h': volume,
                    'liquidity': liquidity
                })

        conn.close()
        return sorted(opportunities, key=lambda x: x['gap'], reverse=True)

    # =========================================================
    # DETECTOR 2: Spread Analysis (Wide spread = opportunity)
    # =========================================================
    def detect_wide_spreads(self):
        """
        Wide bid-ask spread means market maker opportunity.
        Buy at bid, sell at ask = capture spread.
        """
        conn = self._get_db()
        cursor = conn.cursor()

        # Get latest spread data from prices table
        cursor.execute('''
            SELECT p.market_id, m.question, t.outcome, t.token_id,
                   p.price, p.bid, p.ask, p.spread,
                   m.volume_24h, m.liquidity
            FROM prices p
            JOIN markets m ON m.id = p.market_id
            JOIN tokens t ON t.token_id = p.token_id
            WHERE m.active = 1 AND m.closed = 0
              AND p.spread IS NOT NULL AND p.spread > 0
              AND p.id IN (
                  SELECT MAX(id) FROM prices GROUP BY token_id
              )
            ORDER BY p.spread DESC
        ''')

        opportunities = []
        for row in cursor.fetchall():
            market_id, question, outcome, token_id, price, bid, ask, spread, volume, liquidity = row

            if spread and spread >= self.spread_threshold:
                opportunities.append({
                    'market_id': market_id,
                    'type': 'wide_spread',
                    'question': question,
                    'outcome': outcome,
                    'price': price,
                    'bid': bid,
                    'ask': ask,
                    'spread': round(spread, 4),
                    'edge_pct': round(spread * 100, 2),
                    'volume_24h': volume,
                    'liquidity': liquidity
                })

        conn.close()
        return sorted(opportunities, key=lambda x: x['spread'], reverse=True)

    # =========================================================
    # DETECTOR 3: Price Momentum (Rapid price movement)
    # =========================================================
    def detect_momentum(self, hours=1):
        """
        Detect tokens with significant price movement.
        Could indicate news catalyst or market overreaction.
        """
        conn = self._get_db()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Get price changes from history
        cursor.execute('''
            SELECT t.market_id, m.question, t.outcome, t.token_id,
                   t.price as current_price,
                   (SELECT p2.price FROM prices p2 
                    WHERE p2.token_id = t.token_id 
                      AND p2.timestamp < ?
                    ORDER BY p2.timestamp DESC LIMIT 1) as old_price,
                   m.volume_24h, m.liquidity
            FROM tokens t
            JOIN markets m ON m.id = t.market_id
            WHERE m.active = 1 AND m.closed = 0
        ''', (cutoff,))

        opportunities = []
        for row in cursor.fetchall():
            market_id, question, outcome, token_id, current, old, volume, liquidity = row

            if old is None or old == 0 or current is None:
                continue

            change = current - old
            change_pct = abs(change) / old

            if change_pct >= self.momentum_threshold:
                direction = "UP" if change > 0 else "DOWN"
                opportunities.append({
                    'market_id': market_id,
                    'type': 'momentum',
                    'question': question,
                    'outcome': outcome,
                    'old_price': round(old, 4),
                    'current_price': round(current, 4),
                    'change': round(change, 4),
                    'change_pct': round(change_pct * 100, 2),
                    'direction': direction,
                    'edge_pct': round(change_pct * 100, 2),
                    'hours': hours,
                    'volume_24h': volume,
                    'liquidity': liquidity
                })

        conn.close()
        return sorted(opportunities, key=lambda x: abs(x['change_pct']), reverse=True)

    # =========================================================
    # DETECTOR 4: Volume Spike Detection
    # =========================================================
    def detect_volume_spikes(self):
        """
        Sudden increase in volume suggests news event or whale activity.
        Compare 24h volume vs liquidity ratio.
        """
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, question, volume_24h, liquidity, volume,
                   outcome_prices, slug
            FROM markets
            WHERE active = 1 AND closed = 0
              AND volume_24h > 0 AND liquidity > 0
            ORDER BY volume_24h DESC
        ''')

        opportunities = []
        for row in cursor.fetchall():
            market_id, question, vol24h, liquidity, total_vol, prices, slug = row

            # Volume-to-liquidity ratio (high = active trading relative to depth)
            vol_liq_ratio = vol24h / liquidity if liquidity > 0 else 0

            if vol_liq_ratio >= self.volume_spike_mult:
                opportunities.append({
                    'market_id': market_id,
                    'type': 'volume_spike',
                    'question': question,
                    'volume_24h': vol24h,
                    'liquidity': liquidity,
                    'vol_liq_ratio': round(vol_liq_ratio, 2),
                    'total_volume': total_vol,
                    'edge_pct': round(vol_liq_ratio, 2),
                    'slug': slug
                })

        conn.close()
        return sorted(opportunities, key=lambda x: x['vol_liq_ratio'], reverse=True)

    # =========================================================
    # DETECTOR 5: Near-Extreme Prices (Almost resolved)
    # =========================================================
    def detect_near_extremes(self):
        """
        Markets priced >$0.95 or <$0.05 that aren't resolved yet.
        Could be free money if resolution is certain,
        or overconfident if there's tail risk.
        """
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.market_id, m.question, t.outcome, t.price,
                   m.volume_24h, m.liquidity, m.end_date, m.slug
            FROM tokens t
            JOIN markets m ON m.id = t.market_id
            WHERE m.active = 1 AND m.closed = 0
              AND (t.price > 0.95 OR (t.price < 0.05 AND t.price > 0))
              AND m.liquidity > ?
        ''', (self.min_liquidity,))

        opportunities = []
        for row in cursor.fetchall():
            market_id, question, outcome, price, volume, liquidity, end_date, slug = row

            if price > 0.95:
                edge = round((1.0 - price) * 100, 2)
                risk_type = "HIGH_CONFIDENCE"
                note = f"Market {edge}% from resolution. Tail risk?"
            else:
                edge = round(price * 100, 2)
                risk_type = "LOW_CONFIDENCE"
                note = f"Only {edge}% chance. Contrarian opportunity?"

            opportunities.append({
                'market_id': market_id,
                'type': 'near_extreme',
                'question': question,
                'outcome': outcome,
                'price': price,
                'risk_type': risk_type,
                'edge_pct': edge,
                'note': note,
                'volume_24h': volume,
                'liquidity': liquidity,
                'end_date': end_date,
                'slug': slug
            })

        conn.close()
        return sorted(opportunities, key=lambda x: x['edge_pct'])

    # =========================================================
    # MASTER: Run All Detectors
    # =========================================================
    def run_all(self, save=True):
        """Run all opportunity detectors and return combined results"""
        self._log('INFO', 'Running opportunity detection...')
        
        all_opportunities = []
        
        # 1. Complement mismatch
        complements = self.detect_complement_mismatch()
        self._log('INFO', f'Complement mismatch: {len(complements)} found')
        all_opportunities.extend(complements)
        
        # 2. Wide spreads
        spreads = self.detect_wide_spreads()
        self._log('INFO', f'Wide spreads: {len(spreads)} found')
        all_opportunities.extend(spreads)
        
        # 3. Price momentum (1h and 6h)
        momentum_1h = self.detect_momentum(hours=1)
        momentum_6h = self.detect_momentum(hours=6)
        self._log('INFO', f'Momentum: {len(momentum_1h)} (1h), {len(momentum_6h)} (6h)')
        all_opportunities.extend(momentum_1h)
        
        # 4. Volume spikes
        volume = self.detect_volume_spikes()
        self._log('INFO', f'Volume spikes: {len(volume)} found')
        all_opportunities.extend(volume)
        
        # 5. Near-extreme prices
        extremes = self.detect_near_extremes()
        self._log('INFO', f'Near-extremes: {len(extremes)} found')
        all_opportunities.extend(extremes)
        
        # Save to database
        if save:
            self._save_opportunities(all_opportunities)
        
        # Summary
        summary = {
            'total': len(all_opportunities),
            'complement_mismatch': len(complements),
            'wide_spread': len(spreads),
            'momentum': len(momentum_1h),
            'volume_spike': len(volume),
            'near_extreme': len(extremes),
            'timestamp': datetime.now().isoformat()
        }
        
        self._log('INFO', f'Detection complete: {summary["total"]} total opportunities')
        
        return {
            'summary': summary,
            'opportunities': {
                'complement_mismatch': complements,
                'wide_spread': spreads,
                'momentum_1h': momentum_1h,
                'momentum_6h': momentum_6h,
                'volume_spike': volume,
                'near_extreme': extremes
            }
        }

    def _save_opportunities(self, opportunities):
        """Save detected opportunities to database"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        saved = 0
        for opp in opportunities:
            try:
                cursor.execute('''
                    INSERT INTO opportunities (
                        market_id, type, ai_estimate, edge, confidence, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    opp.get('market_id'),
                    opp.get('type', 'unknown'),
                    opp.get('current_price', opp.get('total', 0)),
                    opp.get('edge_pct', 0),
                    opp.get('vol_liq_ratio', opp.get('change_pct', 0)),
                    json.dumps(opp)
                ))
                saved += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        self._log('INFO', f'Saved {saved} opportunities to database')


def format_dollar(amount):
    """Format number as dollar string"""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.1f}K"
    else:
        return f"${amount:.2f}"


# =========================================================
# CLI: Run and display results
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🔍 Polymarket Opportunity Detector")
    print("=" * 60)
    print()

    detector = OpportunityDetector()
    results = detector.run_all(save=True)
    summary = results['summary']
    opps = results['opportunities']

    # --- Complement Mismatch ---
    print(f"\n🧩 COMPLEMENT MISMATCH ({summary['complement_mismatch']})")
    print("-" * 50)
    if opps['complement_mismatch']:
        for o in opps['complement_mismatch'][:5]:
            print(f"  {o['question'][:55]}...")
            print(f"    Tokens: {o['tokens']}")
            print(f"    Total: ${o['total']} ({o['direction']}, gap: {o['edge_pct']}%)")
            print(f"    Volume: {format_dollar(o['volume_24h'])}")
            print()
    else:
        print("  None detected")

    # --- Wide Spreads ---
    print(f"\n📊 WIDE SPREADS ({summary['wide_spread']})")
    print("-" * 50)
    if opps['wide_spread']:
        for o in opps['wide_spread'][:5]:
            print(f"  {o['question'][:55]}...")
            print(f"    {o['outcome']}: bid=${o['bid']} / ask=${o['ask']} (spread: {o['edge_pct']}%)")
            print(f"    Volume: {format_dollar(o['volume_24h'])}")
            print()
    else:
        print("  None detected (need more price history)")

    # --- Momentum ---
    print(f"\n🚀 PRICE MOMENTUM - 1h ({summary['momentum']})")
    print("-" * 50)
    if opps['momentum_1h']:
        for o in opps['momentum_1h'][:5]:
            arrow = "↑" if o['direction'] == 'UP' else "↓"
            print(f"  {arrow} {o['question'][:50]}...")
            print(f"    {o['outcome']}: ${o['old_price']} → ${o['current_price']} ({o['direction']} {o['change_pct']}%)")
            print()
    else:
        print("  None detected (need more price history)")

    # --- Volume Spikes ---
    print(f"\n📈 VOLUME SPIKES ({summary['volume_spike']})")
    print("-" * 50)
    if opps['volume_spike']:
        for o in opps['volume_spike'][:5]:
            print(f"  {o['question'][:55]}...")
            print(f"    24h Volume: {format_dollar(o['volume_24h'])} / Liquidity: {format_dollar(o['liquidity'])}")
            print(f"    Ratio: {o['vol_liq_ratio']}x (hot market)")
            print()
    else:
        print("  None detected")

    # --- Near-Extreme ---
    print(f"\n⚡ NEAR-EXTREME PRICES ({summary['near_extreme']})")
    print("-" * 50)
    if opps['near_extreme']:
        for o in opps['near_extreme'][:10]:
            print(f"  {o['question'][:55]}...")
            print(f"    {o['outcome']}: ${o['price']} [{o['risk_type']}]")
            print(f"    {o['note']}")
            print()
    else:
        print("  None detected")

    # --- Summary ---
    print("=" * 60)
    print(f"📋 SUMMARY")
    print(f"   Total opportunities: {summary['total']}")
    print(f"   Complement mismatch: {summary['complement_mismatch']}")
    print(f"   Wide spreads:        {summary['wide_spread']}")
    print(f"   Momentum signals:    {summary['momentum']}")
    print(f"   Volume spikes:       {summary['volume_spike']}")
    print(f"   Near-extreme:        {summary['near_extreme']}")
    print("=" * 60)