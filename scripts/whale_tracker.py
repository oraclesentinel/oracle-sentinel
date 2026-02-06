#!/usr/bin/env python3
"""
Whale Tracker - On-chain Intelligence Layer
Detects whale activity via Polymarket CLOB public API
"""

import os
import json
import time
import sqlite3
import requests
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
CLOB_BASE = "https://clob.polymarket.com"
GAMMA_BASE = "https://gamma-api.polymarket.com"

IMBALANCE_THRESHOLD = 0.65
MOMENTUM_THRESHOLD = 0.05
VOLUME_SPIKE_MULTIPLIER = 2.0


class WhaleTracker:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'OracleSentinel/2.0'
        })

    def _log(self, level, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [WHALE] [{level}] {msg}")

    def _get(self, url, params=None, timeout=10):
        for attempt in range(3):
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    self._log('WARN', f'Rate limited, waiting {wait}s...')
                    time.sleep(wait)
                else:
                    return None
            except requests.exceptions.Timeout:
                time.sleep(1)
            except Exception as e:
                self._log('ERROR', f'Request failed: {e}')
                return None
        return None

    # ═══════════════════════════════════════════════════════
    # 1. ORDER BOOK ANALYSIS
    # ═══════════════════════════════════════════════════════

    def analyze_order_book(self, token_id):
        book = self._get(f"{CLOB_BASE}/book", params={"token_id": token_id})
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
    # 2. PRICE MOMENTUM
    # ═══════════════════════════════════════════════════════

    def analyze_momentum(self, token_id):
        results = {"price_now": 0, "change_1h": 0, "change_6h": 0,
                   "change_24h": 0, "momentum_signal": "NEUTRAL", "volatility": "LOW"}

        for interval, key in [("1h", "change_1h"), ("6h", "change_6h"), ("1d", "change_24h")]:
            fidelity = {"1h": 60, "6h": 300, "1d": 3600}[interval]
            data = self._get(f"{CLOB_BASE}/prices-history",
                             params={"token_id": token_id, "interval": interval, "fidelity": fidelity})
            if not data:
                continue
            history = data.get("history", [])
            prices = [float(h.get("p", 0)) for h in history if h.get("p")]
            if len(prices) >= 2:
                change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
                results[key] = round(change * 100, 2)
                if key == "change_1h":
                    results["price_now"] = round(prices[-1], 4)
                    returns = [(prices[i] - prices[i-1]) / prices[i-1]
                               for i in range(1, len(prices)) if prices[i-1] > 0]
                    vol = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0
                    if vol > 0.05:
                        results["volatility"] = "HIGH"
                    elif vol > 0.02:
                        results["volatility"] = "MEDIUM"
            time.sleep(0.2)

        ch1 = results["change_1h"] / 100
        ch6 = results["change_6h"] / 100
        if abs(ch1) > MOMENTUM_THRESHOLD:
            results["momentum_signal"] = "STRONG_UP" if ch1 > 0 else "STRONG_DOWN"
        elif abs(ch6) > MOMENTUM_THRESHOLD:
            results["momentum_signal"] = "UP" if ch6 > 0 else "DOWN"

        return results

    # ═══════════════════════════════════════════════════════
    # 3. VOLUME SPIKE
    # ═══════════════════════════════════════════════════════

    def detect_volume_spike(self, condition_id, current_volume):
        result = {"current_volume": current_volume, "volume_signal": "NORMAL",
                  "spike_multiplier": 1.0, "daily_avg_volume": 0}

        market_data = self._get(f"{GAMMA_BASE}/markets/{condition_id}")
        if not market_data:
            return result

        total_volume = float(market_data.get("volumeNum", 0) or 0)
        created = market_data.get("createdAt", "")
        if created and total_volume > 0:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days = max((datetime.now(timezone.utc) - created_dt).days, 1)
                daily_avg = total_volume / days
                result["daily_avg_volume"] = round(daily_avg, 2)

                if current_volume > 0 and daily_avg > 0:
                    spike = current_volume / daily_avg
                    result["spike_multiplier"] = round(spike, 2)
                    if spike >= VOLUME_SPIKE_MULTIPLIER * 2:
                        result["volume_signal"] = "EXTREME_SPIKE"
                    elif spike >= VOLUME_SPIKE_MULTIPLIER:
                        result["volume_signal"] = "SPIKE"
            except (ValueError, TypeError):
                pass

        return result

    # ═══════════════════════════════════════════════════════
    # MASTER: Full Whale Analysis
    # ═══════════════════════════════════════════════════════

    def analyze_market_whales(self, token_id_yes, token_id_no, question,
                               condition_id="", current_volume=0):
        self._log('INFO', f'Analyzing: {question[:50]}...')

        ob_yes = self.analyze_order_book(token_id_yes)
        time.sleep(0.3)
        ob_no = self.analyze_order_book(token_id_no)
        time.sleep(0.3)
        momentum = self.analyze_momentum(token_id_yes)
        time.sleep(0.3)
        volume_data = self.detect_volume_spike(condition_id, current_volume)

        # Build signals
        signals = []
        yi = ob_yes.get("imbalance_ratio", 0.5)
        if yi > IMBALANCE_THRESHOLD:
            signals.append(f"BULLISH: YES book bid-heavy ({yi:.0%} buy vs {1-yi:.0%} sell)")
        elif yi < (1 - IMBALANCE_THRESHOLD):
            signals.append(f"BEARISH: YES book ask-heavy ({yi:.0%} buy vs {1-yi:.0%} sell)")

        ni = ob_no.get("imbalance_ratio", 0.5)
        if ni > IMBALANCE_THRESHOLD:
            signals.append(f"BEARISH: NO token strong buying interest ({ni:.0%})")

        if ob_yes.get("whale_bids", 0) > 2:
            signals.append(f"BULLISH: {ob_yes['whale_bids']} whale bids (>$1K) on YES")
        if ob_yes.get("whale_asks", 0) > 2:
            signals.append(f"BEARISH: {ob_yes['whale_asks']} whale asks (>$1K) on YES")
        if ob_no.get("whale_bids", 0) > 2:
            signals.append(f"BEARISH: {ob_no['whale_bids']} whale bids on NO")

        ms = momentum.get("momentum_signal", "NEUTRAL")
        if ms in ("STRONG_UP", "UP"):
            signals.append(f"BULLISH: Momentum {ms} (1h:{momentum['change_1h']:+.1f}% 6h:{momentum['change_6h']:+.1f}%)")
        elif ms in ("STRONG_DOWN", "DOWN"):
            signals.append(f"BEARISH: Momentum {ms} (1h:{momentum['change_1h']:+.1f}% 6h:{momentum['change_6h']:+.1f}%)")

        vs = volume_data.get("volume_signal", "NORMAL")
        if vs in ("SPIKE", "EXTREME_SPIKE"):
            signals.append(f"ALERT: Volume {vs} ({volume_data['spike_multiplier']:.1f}x daily avg)")

        if momentum.get("volatility") == "HIGH":
            signals.append("ALERT: High price volatility")

        summary = "\n".join(f"  • {s}" for s in signals) if signals else "No significant whale activity."

        # Sentiment
        bull = sum(1 for s in signals if "BULLISH" in s)
        bear = sum(1 for s in signals if "BEARISH" in s)
        if bull > bear + 1: sentiment = "BULLISH"
        elif bear > bull + 1: sentiment = "BEARISH"
        elif bull > 0 or bear > 0: sentiment = "MIXED"
        else: sentiment = "NEUTRAL"

        self._log('INFO', f'  {len(signals)} signals, sentiment: {sentiment}')

        return {
            "summary": summary, "signals": signals, "signal_count": len(signals),
            "order_book_yes": ob_yes, "order_book_no": ob_no,
            "momentum": momentum, "volume": volume_data,
            "overall_sentiment": sentiment
        }

    def format_for_ai_prompt(self, whale_data):
        if not whale_data or whale_data.get("signal_count", 0) == 0:
            return "ON-CHAIN WHALE INTELLIGENCE:\nNo significant whale activity detected."

        ob_yes = whale_data.get("order_book_yes", {})
        mom = whale_data.get("momentum", {})
        vol = whale_data.get("volume", {})
        sentiment = whale_data.get("overall_sentiment", "NEUTRAL")

        lines = [
            "ON-CHAIN WHALE INTELLIGENCE:",
            f"Overall Whale Sentiment: {sentiment}",
            "",
            "Order Book (YES token):",
            f"  Bid depth: ${ob_yes.get('bid_depth', 0):,.0f} | Ask depth: ${ob_yes.get('ask_depth', 0):,.0f}",
            f"  Imbalance: {ob_yes.get('imbalance_ratio', 0.5):.0%} buy / {1-ob_yes.get('imbalance_ratio', 0.5):.0%} sell",
            f"  Whale orders: {ob_yes.get('whale_bids', 0)} large bids, {ob_yes.get('whale_asks', 0)} large asks",
            "",
            "Price Momentum:",
            f"  1h: {mom.get('change_1h', 0):+.1f}% | 6h: {mom.get('change_6h', 0):+.1f}% | 24h: {mom.get('change_24h', 0):+.1f}%",
            f"  Signal: {mom.get('momentum_signal', 'NEUTRAL')} | Volatility: {mom.get('volatility', 'LOW')}",
            "",
            f"Volume: {vol.get('volume_signal', 'NORMAL')} ({vol.get('spike_multiplier', 1):.1f}x daily avg)",
            "",
            "Whale Signals:",
            whale_data.get("summary", "None"),
        ]
        return "\n".join(lines)


def get_market_tokens(market_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT condition_id FROM markets WHERE id = ?', (market_id,))
    row = cursor.fetchone()
    condition_id = row[0] if row else ""

    cursor.execute('SELECT token_id, outcome FROM tokens WHERE market_id = ?', (market_id,))
    tokens = cursor.fetchall()
    conn.close()

    result = {"condition_id": condition_id or ""}
    for token_id, outcome in tokens:
        if outcome and outcome.lower() in ('yes', 'true', '1'):
            result["token_id_yes"] = token_id
        elif outcome and outcome.lower() in ('no', 'false', '0'):
            result["token_id_no"] = token_id
    return result


if __name__ == '__main__':
    print("=" * 60)
    print("🐋 Oracle Sentinel - Whale Tracker")
    print("=" * 60)

    tracker = WhaleTracker()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, question, volume_24h FROM markets
        WHERE active = 1 AND closed = 0
        ORDER BY volume_24h DESC LIMIT 5
    ''')
    markets = cursor.fetchall()
    conn.close()

    for mid, q, vol in markets:
        print(f"\n{'─'*60}")
        print(f"Market: {q[:55]}...")
        tokens = get_market_tokens(mid)
        if not tokens.get("token_id_yes") or not tokens.get("token_id_no"):
            print("  ⚠ Missing token IDs")
            continue
        data = tracker.analyze_market_whales(
            tokens["token_id_yes"], tokens["token_id_no"],
            q, tokens.get("condition_id", ""), vol
        )
        print(tracker.format_for_ai_prompt(data))
        time.sleep(1)