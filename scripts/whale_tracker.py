#!/usr/bin/env python3
"""
Whale Tracker - On-chain Intelligence Layer
Detects whale activity via Jupiter Prediction API

Migrated from Polymarket CLOB to Jupiter Prediction Market
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timezone
from jupiter_prediction_client import JupiterPredictionClient

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

IMBALANCE_THRESHOLD = 0.65
MOMENTUM_THRESHOLD = 0.05
VOLUME_SPIKE_MULTIPLIER = 2.0


class WhaleTracker:

    def __init__(self):
        self.jupiter = JupiterPredictionClient()

    def _log(self, level, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [WHALE] [{level}] {msg}")

    # ═══════════════════════════════════════════════════════
    # 1. ORDER BOOK ANALYSIS (via Jupiter adapter)
    # ═══════════════════════════════════════════════════════

    def analyze_order_book(self, market_id):
        """Analyze orderbook using Jupiter API with Polymarket-format adapter"""
        book = self.jupiter.get_orderbook_polymarket_format(market_id)
        
        if not book:
            return {"bid_depth": 0, "ask_depth": 0, "imbalance_ratio": 0.5,
                    "top_bid_size": 0, "top_ask_size": 0, "spread": 0,
                    "bid_levels": 0, "ask_levels": 0, "whale_bids": 0, "whale_asks": 0}

        bids = book.get("bids", [])
        asks = book.get("asks", [])

        bid_depth = sum(float(b.get("price", 0)) * float(b.get("size", 0)) for b in bids)
        ask_depth = sum(float(a.get("price", 0)) * float(a.get("size", 0)) for a in asks)
        total = bid_depth + ask_depth
        imbalance = bid_depth / total if total > 0 else 0.5

        top_bid = max((float(b.get("size", 0)) for b in bids), default=0)
        top_ask = max((float(a.get("size", 0)) for a in asks), default=0)

        best_bid = max((float(b.get("price", 0)) for b in bids), default=0)
        best_ask = min((float(a.get("price", 0)) for a in asks), default=1)
        spread = best_ask - best_bid if best_ask > best_bid else 0

        # Whale orders: > $1000 value
        whale_bids = sum(1 for b in bids if float(b.get("price", 0)) * float(b.get("size", 0)) > 1000)
        whale_asks = sum(1 for a in asks if float(a.get("price", 0)) * float(a.get("size", 0)) > 1000)

        return {
            "bid_depth": round(bid_depth, 2), "ask_depth": round(ask_depth, 2),
            "imbalance_ratio": round(imbalance, 3),
            "top_bid_size": round(top_bid, 2), "top_ask_size": round(top_ask, 2),
            "spread": round(spread, 4),
            "bid_levels": len(bids), "ask_levels": len(asks),
            "whale_bids": whale_bids, "whale_asks": whale_asks
        }

    # ═══════════════════════════════════════════════════════
    # 2. PRICE MOMENTUM (from recent trades)
    # ═══════════════════════════════════════════════════════

    def analyze_momentum(self, market_id):
        """Analyze momentum from recent trades on Jupiter"""
        results = {"price_now": 0, "change_1h": 0, "change_6h": 0,
                   "change_24h": 0, "momentum_signal": "NEUTRAL", "volatility": "LOW"}
        
        try:
            # Get current market price
            market = self.jupiter.get_market_by_id(market_id)
            if market:
                pricing = market.get('pricing', {})
                yes_price = (pricing.get('buyYesPriceUsd', 0) or 0) / 1_000_000
                results["price_now"] = round(yes_price, 4)
            
            # Get recent trades for this market
            trades = self.jupiter.get_trades(limit=100)
            market_trades = [t for t in trades if t.get('marketId') == market_id]
            
            if len(market_trades) >= 2:
                # Calculate simple momentum from trade prices
                prices = []
                for t in market_trades:
                    price_usd = t.get('priceUsd', 0)
                    if price_usd:
                        prices.append(int(price_usd) / 1_000_000)
                
                if len(prices) >= 2:
                    # Newest vs oldest in sample
                    change = (prices[0] - prices[-1]) / prices[-1] if prices[-1] > 0 else 0
                    results["change_1h"] = round(change * 100, 2)
                    
                    # Volatility from price variance
                    if len(prices) >= 3:
                        returns = [(prices[i] - prices[i+1]) / prices[i+1] 
                                   for i in range(len(prices)-1) if prices[i+1] > 0]
                        if returns:
                            vol = (sum(r**2 for r in returns) / len(returns)) ** 0.5
                            if vol > 0.05:
                                results["volatility"] = "HIGH"
                            elif vol > 0.02:
                                results["volatility"] = "MEDIUM"
            
            # Determine momentum signal
            ch1 = results["change_1h"] / 100
            if abs(ch1) > MOMENTUM_THRESHOLD:
                results["momentum_signal"] = "STRONG_UP" if ch1 > 0 else "STRONG_DOWN"
            elif abs(ch1) > MOMENTUM_THRESHOLD / 2:
                results["momentum_signal"] = "UP" if ch1 > 0 else "DOWN"
                
        except Exception as e:
            self._log('WARN', f'Momentum analysis error: {e}')
        
        return results

    # ═══════════════════════════════════════════════════════
    # 3. VOLUME SPIKE (from Jupiter market data)
    # ═══════════════════════════════════════════════════════

    def detect_volume_spike(self, market_id, current_volume=0):
        """Detect volume spikes using Jupiter market data"""
        result = {"current_volume": current_volume, "volume_signal": "NORMAL",
                  "spike_multiplier": 1.0, "daily_avg_volume": 0}
        
        try:
            market = self.jupiter.get_market_by_id(market_id)
            if not market:
                return result
            
            pricing = market.get('pricing', {})
            total_volume = (pricing.get('volume', 0) or 0) / 1_000_000
            
            # Estimate daily average (assume market is ~30 days old if no creation date)
            close_time = market.get('closeTime', 0)
            if close_time:
                days_until_close = max((close_time - datetime.now().timestamp()) / 86400, 1)
                # Assume market has been running for similar duration
                estimated_days = max(30 - days_until_close, 7)
                daily_avg = total_volume / estimated_days
                result["daily_avg_volume"] = round(daily_avg, 2)
                
                if current_volume > 0 and daily_avg > 0:
                    spike = current_volume / daily_avg
                    result["spike_multiplier"] = round(spike, 2)
                    if spike >= VOLUME_SPIKE_MULTIPLIER * 2:
                        result["volume_signal"] = "EXTREME_SPIKE"
                    elif spike >= VOLUME_SPIKE_MULTIPLIER:
                        result["volume_signal"] = "SPIKE"
                        
        except Exception as e:
            self._log('WARN', f'Volume spike detection error: {e}')
        
        return result

    # ═══════════════════════════════════════════════════════
    # MASTER: Full Whale Analysis
    # ═══════════════════════════════════════════════════════

    def analyze_market_whales(self, market_id, question="", current_volume=0):
        """
        Full whale analysis for a Jupiter market.
        
        Args:
            market_id: Jupiter market ID (e.g., POLY-559652)
            question: Market question for logging
            current_volume: Current 24h volume
        """
        self._log('INFO', f'Analyzing: {question[:50]}...')

        # Orderbook analysis
        ob_data = self.analyze_order_book(market_id)
        time.sleep(0.3)
        
        # Momentum analysis
        momentum = self.analyze_momentum(market_id)
        time.sleep(0.3)
        
        # Volume spike detection
        volume_data = self.detect_volume_spike(market_id, current_volume)

        # Build signals
        signals = []
        
        # Orderbook imbalance signals
        yi = ob_data.get("imbalance_ratio", 0.5)
        if yi > IMBALANCE_THRESHOLD:
            signals.append(f"BULLISH: Book bid-heavy ({yi:.0%} buy vs {1-yi:.0%} sell)")
        elif yi < (1 - IMBALANCE_THRESHOLD):
            signals.append(f"BEARISH: Book ask-heavy ({yi:.0%} buy vs {1-yi:.0%} sell)")

        # Whale order signals
        if ob_data.get("whale_bids", 0) > 2:
            signals.append(f"BULLISH: {ob_data['whale_bids']} whale bids (>$1K)")
        if ob_data.get("whale_asks", 0) > 2:
            signals.append(f"BEARISH: {ob_data['whale_asks']} whale asks (>$1K)")

        # Momentum signals
        ms = momentum.get("momentum_signal", "NEUTRAL")
        if ms in ("STRONG_UP", "UP"):
            signals.append(f"BULLISH: Momentum {ms} ({momentum['change_1h']:+.1f}%)")
        elif ms in ("STRONG_DOWN", "DOWN"):
            signals.append(f"BEARISH: Momentum {ms} ({momentum['change_1h']:+.1f}%)")

        # Volume signals
        vs = volume_data.get("volume_signal", "NORMAL")
        if vs in ("SPIKE", "EXTREME_SPIKE"):
            signals.append(f"ALERT: Volume {vs} ({volume_data['spike_multiplier']:.1f}x daily avg)")

        # Volatility alert
        if momentum.get("volatility") == "HIGH":
            signals.append("ALERT: High price volatility")

        summary = "\n".join(f"  • {s}" for s in signals) if signals else "No significant whale activity."

        # Overall sentiment
        bull = sum(1 for s in signals if "BULLISH" in s)
        bear = sum(1 for s in signals if "BEARISH" in s)
        if bull > bear + 1: sentiment = "BULLISH"
        elif bear > bull + 1: sentiment = "BEARISH"
        elif bull > 0 or bear > 0: sentiment = "MIXED"
        else: sentiment = "NEUTRAL"

        self._log('INFO', f'  {len(signals)} signals, sentiment: {sentiment}')

        return {
            "summary": summary, "signals": signals, "signal_count": len(signals),
            "order_book": ob_data,
            "momentum": momentum, "volume": volume_data,
            "overall_sentiment": sentiment
        }

    def format_for_ai_prompt(self, whale_data):
        """Format whale data for AI consumption"""
        if not whale_data or whale_data.get("signal_count", 0) == 0:
            return "ON-CHAIN WHALE INTELLIGENCE:\nNo significant whale activity detected."

        ob = whale_data.get("order_book", {})
        mom = whale_data.get("momentum", {})
        vol = whale_data.get("volume", {})
        sentiment = whale_data.get("overall_sentiment", "NEUTRAL")

        lines = [
            "ON-CHAIN WHALE INTELLIGENCE (Jupiter):",
            f"Overall Whale Sentiment: {sentiment}",
            "",
            "Order Book Analysis:",
            f"  Bid depth: ${ob.get('bid_depth', 0):,.0f} | Ask depth: ${ob.get('ask_depth', 0):,.0f}",
            f"  Imbalance: {ob.get('imbalance_ratio', 0.5):.0%} buy / {1-ob.get('imbalance_ratio', 0.5):.0%} sell",
            f"  Whale orders: {ob.get('whale_bids', 0)} large bids, {ob.get('whale_asks', 0)} large asks",
            "",
            "Price Momentum:",
            f"  Recent change: {mom.get('change_1h', 0):+.1f}%",
            f"  Signal: {mom.get('momentum_signal', 'NEUTRAL')} | Volatility: {mom.get('volatility', 'LOW')}",
            "",
            f"Volume: {vol.get('volume_signal', 'NORMAL')} ({vol.get('spike_multiplier', 1):.1f}x daily avg)",
            "",
            "Whale Signals:",
            whale_data.get("summary", "None"),
        ]
        return "\n".join(lines)


def get_market_id_from_db(market_id):
    """Get Jupiter market ID from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT polymarket_id FROM markets WHERE id = ?', (market_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


if __name__ == '__main__':
    print("=" * 60)
    print("🐋 Oracle Sentinel - Whale Tracker (Jupiter)")
    print("=" * 60)

    tracker = WhaleTracker()

    # Get top markets from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, polymarket_id, question, volume_24h FROM markets
        WHERE active = 1 AND closed = 0
          AND polymarket_id LIKE 'POLY-%'
        ORDER BY volume_24h DESC LIMIT 5
    ''')
    markets = cursor.fetchall()
    conn.close()

    if not markets:
        print("No Jupiter markets found in database. Run price_updater.py first.")
    else:
        for mid, jupiter_id, q, vol in markets:
            print(f"\n{'─'*60}")
            print(f"Market: {q[:55]}...")
            print(f"Jupiter ID: {jupiter_id}")
            
            data = tracker.analyze_market_whales(jupiter_id, q, vol or 0)
            print(tracker.format_for_ai_prompt(data))


def get_market_tokens(market_id):
    """Get token IDs for a market from database (legacy compatibility)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get polymarket_id (which is now Jupiter market ID)
    cursor.execute('SELECT polymarket_id, condition_id FROM markets WHERE id = ?', (market_id,))
    row = cursor.fetchone()
    
    result = {
        "condition_id": row[1] if row else "",
        "jupiter_market_id": row[0] if row else ""
    }
    
    # For legacy compatibility - tokens table may have token IDs
    cursor.execute('SELECT token_id, outcome FROM tokens WHERE market_id = ?', (market_id,))
    tokens = cursor.fetchall()
    conn.close()
    
    for token_id, outcome in tokens:
        if outcome and outcome.lower() in ('yes', 'true', '1'):
            result["token_id_yes"] = token_id
        elif outcome and outcome.lower() in ('no', 'false', '0'):
            result["token_id_no"] = token_id
    
    return result
