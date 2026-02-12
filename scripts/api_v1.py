#!/usr/bin/env python3
"""
Oracle Sentinel API v1 - Protected endpoints with x402 + Token Gating
"""

import json
import sqlite3
import os
from flask import Blueprint, jsonify, request

from x402_middleware import x402_protected

# Create Blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

DB_PATH = os.path.expanduser("~/oracle-sentinel/data/polymarket.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# PROTECTED ENDPOINTS (require payment or $OSAI holding)
# ============================================================

@api_v1.route("/signal/<slug>")
@x402_protected
def get_signal(slug):
    """
    Get trading signal for a specific market.
    Price: $0.01 USDC (or free for $OSAI holders)
    """
    db = get_db()
    try:
        # Get market and latest opportunity
        row = db.execute("""
            SELECT o.id, o.type, o.ai_estimate, o.edge, o.confidence,
                   o.raw_data, o.created_at,
                   m.question, m.outcome_prices, m.volume, m.slug
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            WHERE m.slug = ? AND o.status = 'active'
            ORDER BY o.created_at DESC
            LIMIT 1
        """, (slug,)).fetchone()
        
        if not row:
            return jsonify({"error": "Market not found or no active signal"}), 404
        
        # Parse raw_data for recommendation
        raw_data = json.loads(row["raw_data"]) if row["raw_data"] else {}
        
        return jsonify({
            "slug": slug,
            "question": row["question"],
            "signal": raw_data.get("recommendation", "NO_TRADE"),
            "confidence": row["confidence"],
            "ai_probability": row["ai_estimate"],
            "edge": row["edge"],
            "market_prices": json.loads(row["outcome_prices"]) if row["outcome_prices"] else [],
            "volume": row["volume"],
            "updated_at": row["created_at"]
        })
    finally:
        db.close()


@api_v1.route("/analysis/<slug>")
@x402_protected
def get_analysis(slug):
    """
    Get full AI analysis for a market.
    Price: $0.03 USDC (or free for $OSAI holders)
    """
    db = get_db()
    try:
        # Get market with full analysis
        row = db.execute("""
            SELECT o.id, o.type, o.ai_estimate, o.edge, o.confidence,
                   o.raw_data, o.created_at,
                   m.question, m.outcome_prices, m.volume, m.liquidity,
                   m.slug, m.description, m.end_date
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            WHERE m.slug = ? AND o.status = 'active'
            ORDER BY o.created_at DESC
            LIMIT 1
        """, (slug,)).fetchone()
        
        if not row:
            return jsonify({"error": "Market not found or no active analysis"}), 404
        
        raw_data = json.loads(row["raw_data"]) if row["raw_data"] else {}
        
        return jsonify({
            "slug": slug,
            "question": row["question"],
            "description": row["description"],
            "signal": raw_data.get("recommendation", "NO_TRADE"),
            "confidence": row["confidence"],
            "ai_probability": row["ai_estimate"],
            "edge": row["edge"],
            "reasoning": raw_data.get("reasoning", ""),
            "factors_for": raw_data.get("factors_for", []),
            "factors_against": raw_data.get("factors_against", []),
            "market_prices": json.loads(row["outcome_prices"]) if row["outcome_prices"] else [],
            "volume": row["volume"],
            "liquidity": row["liquidity"],
            "end_date": row["end_date"],
            "updated_at": row["created_at"]
        })
    finally:
        db.close()


@api_v1.route("/whale/<slug>")
@x402_protected
def get_whale_activity(slug):
    """
    Get whale trading activity for a market.
    Price: $0.02 USDC (or free for $OSAI holders)
    """
    db = get_db()
    try:
        # Get market
        market = db.execute("""
            SELECT id, question, polymarket_id FROM markets WHERE slug = ?
        """, (slug,)).fetchone()
        
        if not market:
            return jsonify({"error": "Market not found"}), 404
        
        # Get whale trades from whale_trades_alerted table
        # Match by market_title containing part of the question
        question_search = "%" + market["question"][:50] + "%"
        whale_trades = db.execute("""
            SELECT tx_hash, market_title, trade_size, trade_side, outcome, price, trader_name, alerted_at
            FROM whale_trades_alerted
            WHERE market_title LIKE ?
            ORDER BY alerted_at DESC
            LIMIT 20
        """, (question_search,)).fetchall()
        trades = []
        for trade in whale_trades:
            trades.append({
                "trader": trade["trader_name"],
                "side": trade["trade_side"],
                "amount": trade["trade_size"],
                "outcome": trade["outcome"],
                "price": trade["price"],
                "timestamp": trade["alerted_at"],
                "tx_hash": trade["tx_hash"][:16] + "..."
            })
        # Calculate whale sentiment
        buy_volume = sum(t["amount"] for t in trades if t["side"] == "BUY")
        sell_volume = sum(t["amount"] for t in trades if t["side"] == "SELL")
        
        if buy_volume > sell_volume * 1.5:
            sentiment = "BULLISH"
        elif sell_volume > buy_volume * 1.5:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        return jsonify({
            "slug": slug,
            "question": market["question"],
            "whale_sentiment": sentiment,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "recent_trades": trades,
            "trade_count": len(trades)
        })
    finally:
        db.close()


@api_v1.route("/bulk")
@x402_protected
def get_bulk_signals():
    """
    Get top 10 active signals.
    Price: $0.08 USDC (or free for $OSAI holders)
    """
    db = get_db()
    try:
        rows = db.execute("""
            SELECT o.id, o.type, o.ai_estimate, o.edge, o.confidence,
                   o.raw_data, o.created_at,
                   m.question, m.outcome_prices, m.volume, m.slug
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            INNER JOIN (
                SELECT market_id, MAX(created_at) as max_created
                FROM opportunities
                WHERE status = 'active'
                GROUP BY market_id
            ) latest ON o.market_id = latest.market_id AND o.created_at = latest.max_created
            WHERE o.status = 'active'
            ORDER BY ABS(o.edge) DESC
            LIMIT 10
        """).fetchall()
        
        signals = []
        for row in rows:
            raw_data = json.loads(row["raw_data"]) if row["raw_data"] else {}
            signals.append({
                "slug": row["slug"],
                "question": row["question"][:100] + "..." if len(row["question"]) > 100 else row["question"],
                "signal": raw_data.get("recommendation", "NO_TRADE"),
                "confidence": row["confidence"],
                "edge": row["edge"],
                "volume": row["volume"]
            })
        
        return jsonify({
            "count": len(signals),
            "signals": signals
        })
    finally:
        db.close()


@api_v1.route("/analyze", methods=["POST"])
@x402_protected
def analyze_market():
    """
    Analyze any Polymarket URL on demand.
    Price: $0.05 USDC (or free for $OSAI holders)
    """
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    
    url = data["url"]
    
    # Extract slug from URL
    import re
    match = re.search(r'polymarket\.com/(?:event|sports/.+?)/([a-zA-Z0-9-]+)', url)
    if not match:
        return jsonify({"error": "Invalid Polymarket URL"}), 400
    
    slug = match.group(1)
    
    # Use existing AI brain to analyze
    try:
        from ai_brain import AIBrain
        from polymarket_client import PolymarketClient
        
        # Fetch market data
        pc = PolymarketClient()
        market_data = pc.get_market_or_event(slug)
        
        if not market_data["type"]:
            return jsonify({"error": "Market not found"}), 404
        
        return jsonify({
            "slug": slug,
            "type": market_data["type"],
            "question": market_data["question"],
            "outcomes": market_data["outcomes"][:10],
            "volume": market_data["volume"],
            "message": "Full AI analysis available via /api/chat endpoint"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# INFO ENDPOINT (free)
# ============================================================

@api_v1.route("/info")
def api_info():
    """API v1 information and pricing (free)"""
    return jsonify({
        "version": "v1",
        "description": "Oracle Sentinel Prediction Intelligence API",
        "authentication": {
            "methods": ["x402_payment", "token_gating"],
            "token": "$OSAI",
            "token_mint": "HuDBwWRsa4bu8ueaCb7PPgJrqBeZDkcyFqMW5bbXpump"
        },
        "endpoints": {
            "GET /api/v1/signal/<slug>": {
                "price": "$0.01",
                "description": "Trading signal for a market"
            },
            "GET /api/v1/analysis/<slug>": {
                "price": "$0.03",
                "description": "Full AI analysis with reasoning"
            },
            "GET /api/v1/whale/<slug>": {
                "price": "$0.02",
                "description": "Whale trading activity"
            },
            "GET /api/v1/bulk": {
                "price": "$0.08",
                "description": "Top 10 active signals"
            },
            "POST /api/v1/analyze": {
                "price": "$0.05",
                "description": "Analyze any Polymarket URL"
            }
        },
        "free_access": "Hold 1000+ $OSAI for unlimited free access"
    })


# Test
if __name__ == "__main__":
    print("✅ API v1 module ready")
    print("\nEndpoints:")
    print("  GET  /api/v1/signal/<slug>   - $0.01")
    print("  GET  /api/v1/analysis/<slug> - $0.03")
    print("  GET  /api/v1/whale/<slug>    - $0.02")
    print("  GET  /api/v1/bulk            - $0.08")
    print("  POST /api/v1/analyze         - $0.05")
    print("  GET  /api/v1/info            - FREE")
