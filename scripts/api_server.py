#!/usr/bin/env python3
"""
Oracle Sentinel — API Server
Serves prediction intelligence data from polymarket.db
Run: python3 api_server.py
Access: http://localhost:8099
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
from sports_data import SportsData
from news_fetcher import NewsFetcher
from polymarket_client import PolymarketClient

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.expanduser("~/oracle-sentinel/data/polymarket.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── DASHBOARD SUMMARY ───────────────────────────────────────
@app.route("/api/dashboard")
def dashboard_summary():
    """Main dashboard endpoint — returns everything the frontend needs."""
    db = get_db()
    try:
        # Active signals (opportunities with edge >= 3%)
        signals = db.execute("""
            SELECT o.id, o.market_id, o.type, o.ai_estimate, o.edge, o.confidence,
                   o.raw_data, o.status, o.created_at,
                   m.question, m.outcome_prices, m.volume, m.liquidity, m.slug,
                   m.polymarket_id
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            WHERE o.status = 'active'
              AND m.closed = 0
              AND (m.end_date IS NULL OR m.end_date > datetime('now'))
              AND o.id = (SELECT MAX(o2.id) FROM opportunities o2 WHERE o2.market_id = o.market_id)
            ORDER BY ABS(o.edge) DESC
        """).fetchall()

        active_signals = []
        for s in signals:
            raw = json.loads(s["raw_data"]) if s["raw_data"] else {}
            prices = json.loads(s["outcome_prices"]) if s["outcome_prices"] else []
            yes_price = float(prices[0]) if len(prices) > 0 else 0
            no_price = float(prices[1]) if len(prices) > 1 else 0

            signal_type = raw.get("llm_original_recommendation", "NO_TRADE")
            if signal_type in ("NO_TRADE", "SKIP"):
                continue

            active_signals.append({
                "id": s["id"],
                "market_id": s["market_id"],
                "polymarket_id": s["polymarket_id"],
                "question": s["question"],
                "signal_type": signal_type,
                "ai_probability": s["ai_estimate"],
                "market_yes_price": yes_price,
                "market_no_price": no_price,
                "edge": s["edge"],
                "confidence": raw.get("confidence", "MEDIUM"),
                "reasoning": raw.get("reasoning", ""),
                "recommendation": raw.get("recommendation", ""),
                "key_factors_for": raw.get("key_factors_for", []),
                "key_factors_against": raw.get("key_factors_against", []),
                "risks": raw.get("risks", ""),
                "volume": s["volume"],
                "liquidity": s["liquidity"],
                "slug": s["slug"],
                "created_at": s["created_at"],
            })

        # All markets overview
        markets = db.execute("""
            SELECT m.id, m.question, m.outcome_prices, m.volume, m.liquidity,
                   m.active, m.updated_at, m.slug, m.polymarket_id,
                   (SELECT COUNT(*) FROM opportunities WHERE market_id = m.id) as opp_count
            FROM markets m
            WHERE m.active = 1
            ORDER BY m.volume DESC
            LIMIT 50
        """).fetchall()

        markets_list = []
        for mk in markets:
            prices = json.loads(mk["outcome_prices"]) if mk["outcome_prices"] else []
            markets_list.append({
                "id": mk["id"],
                "question": mk["question"],
                "yes_price": float(prices[0]) if len(prices) > 0 else 0,
                "no_price": float(prices[1]) if len(prices) > 1 else 0,
                "volume": mk["volume"],
                "liquidity": mk["liquidity"],
                "updated_at": mk["updated_at"],
                "slug": mk["slug"],
                "polymarket_id": mk["polymarket_id"],
                "opportunity_count": mk["opp_count"],
            })

        # Prediction tracking
        predictions = db.execute("""
            SELECT pt.*, m.question
            FROM prediction_tracking pt
            JOIN markets m ON pt.market_id = m.id
            ORDER BY pt.created_at DESC
        """).fetchall()

        predictions_list = []
        for p in predictions:
            predictions_list.append({
                "id": p["id"],
                "opportunity_id": p["opportunity_id"],
                "question": p["question"],
                "signal_type": p["signal_type"],
                "ai_probability": p["ai_probability"],
                "market_price_at_signal": p["market_price_at_signal"],
                "edge_at_signal": p["edge_at_signal"],
                "confidence": p["confidence"],
                "price_after_1h": p["price_after_1h"],
                "price_after_6h": p["price_after_6h"],
                "price_after_24h": p["price_after_24h"],
                "direction_correct": p["direction_correct"],
                "final_resolution": p["final_resolution"],
                "hypothetical_pnl": p["hypothetical_pnl"],
                "created_at": p["created_at"],
                "market_end_date": p["market_end_date"],
            })

        # Accuracy stats
        accuracy = db.execute("SELECT * FROM accuracy_daily ORDER BY date DESC LIMIT 30").fetchall()
        accuracy_list = [dict(a) for a in accuracy]

        # Compute live accuracy from prediction_tracking
        acc_stats = db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN signal_type = 'BUY_YES' THEN 1 ELSE 0 END) as buy_yes,
                SUM(CASE WHEN signal_type = 'BUY_NO' THEN 1 ELSE 0 END) as buy_no,
                SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN final_resolution IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                AVG(edge_at_signal) as avg_edge
            FROM prediction_tracking
        """).fetchone()

        # Recent system logs (exclude ERROR)
        logs = db.execute("""
            SELECT * FROM system_logs
            WHERE level != 'ERROR'
            ORDER BY id DESC LIMIT 50
        """).fetchall()
        logs_list = [dict(l) for l in logs]

        # Stats
        total_markets = db.execute("SELECT COUNT(*) FROM markets WHERE active = 1").fetchone()[0]
        total_opps = db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        total_signals_count = db.execute("SELECT COUNT(*) FROM signals").fetchone()[0]

        # Last scan time
        last_scan = db.execute("""
            SELECT timestamp FROM system_logs
            WHERE component = 'price_updater' OR component = 'scanner'
            ORDER BY id DESC LIMIT 1
        """).fetchone()

        return jsonify({
            "active_signals": active_signals,
            "markets": markets_list,
            "predictions": predictions_list,
            "accuracy_daily": accuracy_list,
            "accuracy_stats": {
                "total": acc_stats["total"] or 0,
                "buy_yes": acc_stats["buy_yes"] or 0,
                "buy_no": acc_stats["buy_no"] or 0,
                "correct": acc_stats["correct"] or 0,
                "resolved": acc_stats["resolved"] or 0,
                "avg_edge": round(acc_stats["avg_edge"] or 0, 2),
                "accuracy_pct": round(
                    (acc_stats["correct"] / acc_stats["resolved"] * 100)
                    if acc_stats["resolved"] and acc_stats["resolved"] > 0
                    else 0, 1
                ),
            },
            "system_logs": logs_list,
            "stats": {
                "total_markets": total_markets,
                "total_opportunities": total_opps,
                "total_signals": total_signals_count,
                "total_predictions": acc_stats["total"] or 0,
                "last_scan": last_scan["timestamp"] if last_scan else None,
            },
            "server_time": datetime.utcnow().isoformat(),
        })
    finally:
        db.close()


# ─── INDIVIDUAL ENDPOINTS ────────────────────────────────────
@app.route("/api/signals")
def get_signals():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT o.id, o.market_id, o.type, o.ai_estimate, o.edge, o.confidence,
                   o.raw_data, o.created_at, m.question, m.outcome_prices, m.volume
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            WHERE o.status = 'active'
              AND o.id = (SELECT MAX(o2.id) FROM opportunities o2 WHERE o2.market_id = o.market_id)
            ORDER BY ABS(o.edge) DESC
        """).fetchall()
        results = []
        for r in rows:
            raw = json.loads(r["raw_data"]) if r["raw_data"] else {}
            results.append({
                "id": r["id"],
                "question": r["question"],
                "signal_type": raw.get("llm_original_recommendation", "NO_TRADE"),
                "ai_probability": r["ai_estimate"],
                "edge": r["edge"],
                "confidence": raw.get("confidence", "MEDIUM"),
                "reasoning": raw.get("reasoning", ""),
                "created_at": r["created_at"],
            })
        return jsonify(results)
    finally:
        db.close()


@app.route("/api/markets")
def get_markets():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT * FROM markets WHERE active = 1 ORDER BY volume DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@app.route("/api/predictions")
def get_predictions():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT pt.*, m.question FROM prediction_tracking pt
            JOIN markets m ON pt.market_id = m.id
            ORDER BY pt.created_at DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@app.route("/api/logs")
def get_logs():
    limit = request.args.get("limit", 100, type=int)
    db = get_db()
    try:
        rows = db.execute("""
            SELECT * FROM system_logs ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


@app.route("/api/market/<int:market_id>")
def get_market_detail(market_id):
    db = get_db()
    try:
        market = db.execute("SELECT * FROM markets WHERE id = ?", (market_id,)).fetchone()
        if not market:
            return jsonify({"error": "Market not found"}), 404

        opps = db.execute("""
            SELECT * FROM opportunities WHERE market_id = ? ORDER BY created_at DESC
        """, (market_id,)).fetchall()

        signals = db.execute("""
            SELECT * FROM signals WHERE market_id = ? ORDER BY timestamp DESC LIMIT 20
        """, (market_id,)).fetchall()

        prices = db.execute("""
            SELECT * FROM prices WHERE market_id = ? ORDER BY timestamp DESC LIMIT 50
        """, (market_id,)).fetchall()

        return jsonify({
            "market": dict(market),
            "opportunities": [dict(o) for o in opps],
            "signals": [dict(s) for s in signals],
            "price_history": [dict(p) for p in prices],
        })
    finally:
        db.close()

# ─── PREDICTION DETAIL ───────────────────────────────────────
@app.route("/api/prediction/<int:opp_id>")
def get_prediction_detail(opp_id):
    """Detailed view of a single prediction/opportunity."""
    db = get_db()
    try:
        opp = db.execute("""
            SELECT o.*, m.question, m.description, m.outcome_prices, m.volume,
                   m.liquidity, m.slug, m.polymarket_id, m.end_date, m.resolution_source
            FROM opportunities o
            JOIN markets m ON o.market_id = m.id
            WHERE o.id = ?
        """, (opp_id,)).fetchone()
        if not opp:
            return jsonify({"error": "Prediction not found"}), 404

        raw = json.loads(opp["raw_data"]) if opp["raw_data"] else {}
        prices = json.loads(opp["outcome_prices"]) if opp["outcome_prices"] else []

        tracking = db.execute("""
            SELECT * FROM prediction_tracking WHERE opportunity_id = ?
        """, (opp_id,)).fetchone()

        news = db.execute("""
            SELECT * FROM signals WHERE market_id = ? ORDER BY timestamp DESC LIMIT 5
        """, (opp["question"],)).fetchall()

        whales = db.execute("""
            SELECT * FROM whale_trades_alerted
            WHERE market_title = ? ORDER BY alerted_at DESC LIMIT 10
        """, (opp["question"],)).fetchall()

        # Prioritize prediction_tracking signal if exists (whale_confirmed, etc)
        if tracking:
            final_signal = tracking["signal_type"]
            final_ai_prob = tracking["ai_probability"]
            signal_source = tracking["signal_source"] or "scan"
            whale_trader = tracking["whale_trader"]
            whale_trade_size = tracking["whale_trade_size"]
        else:
            final_signal = raw.get("llm_original_recommendation", "NO_TRADE")
            final_ai_prob = opp["ai_estimate"]
            signal_source = "scan"
            whale_trader = None
            whale_trade_size = None

        return jsonify({
            "id": opp["id"],
            "market_id": opp["market_id"],
            "question": opp["question"],
            "description": opp["description"],
            "signal_type": final_signal,
            "signal_source": signal_source,
            "whale_trader": whale_trader,
            "whale_trade_size": whale_trade_size,
            "ai_probability": final_ai_prob,
            "edge": opp["edge"],
            "confidence": raw.get("confidence", "MEDIUM"),
            "reasoning": raw.get("reasoning", ""),
            "recommendation": raw.get("recommendation", ""),
            "key_factors_for": raw.get("key_factors_for", []),
            "key_factors_against": raw.get("key_factors_against", []),
            "risks": raw.get("risks", ""),
            "market_yes_price": float(prices[0]) if len(prices) > 0 else 0,
            "market_no_price": float(prices[1]) if len(prices) > 1 else 0,
            "volume": opp["volume"],
            "liquidity": opp["liquidity"],
            "slug": opp["slug"],
            "polymarket_id": opp["polymarket_id"],
            "end_date": opp["end_date"],
            "resolution_source": opp["resolution_source"],
            "created_at": opp["created_at"],
            "tracking": dict(tracking) if tracking else None,
            "news": [dict(n) for n in news],
            "whales": [dict(w) for w in whales],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# ─── WHALE CORNER ────────────────────────────────────────────
@app.route("/api/whales")
def get_whales():
    """Whale trades data for Whale Corner dashboard."""
    db = get_db()
    try:
        # Recent whale trades (last 50)
        trades = db.execute("""
            SELECT tx_hash, market_title, trade_size, trade_side, 
                   outcome, price, trader_name, alerted_at
            FROM whale_trades_alerted
            ORDER BY alerted_at DESC
            LIMIT 50
        """).fetchall()
        
        trades_list = []
        for t in trades:
            trades_list.append({
                "tx_hash": t["tx_hash"],
                "market": t["market_title"],
                "size": t["trade_size"],
                "side": t["trade_side"],
                "outcome": t["outcome"],
                "price": t["price"],
                "trader": t["trader_name"],
                "time": t["alerted_at"],
            })
        
        # Stats (24h)
        stats = db.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(trade_size) as total_volume,
                AVG(trade_size) as avg_size,
                SUM(CASE WHEN trade_side = 'BUY' THEN 1 ELSE 0 END) as buys,
                SUM(CASE WHEN trade_side = 'SELL' THEN 1 ELSE 0 END) as sells
            FROM whale_trades_alerted
            WHERE alerted_at >= datetime('now', '-24 hours')
        """).fetchone()
        
        # Top markets by whale volume (24h)
        top_markets = db.execute("""
            SELECT market_title, SUM(trade_size) as volume, COUNT(*) as trades
            FROM whale_trades_alerted
            WHERE alerted_at >= datetime('now', '-24 hours')
            GROUP BY market_title
            ORDER BY volume DESC
            LIMIT 5
        """).fetchall()
        
        return jsonify({
            "trades": trades_list,
            "stats": {
                "total_trades": stats["total_trades"] or 0,
                "total_volume": round(stats["total_volume"] or 0, 2),
                "avg_size": round(stats["avg_size"] or 0, 2),
                "buys": stats["buys"] or 0,
                "sells": stats["sells"] or 0,
            },
            "top_markets": [
                {"market": m["market_title"], "volume": round(m["volume"], 2), "trades": m["trades"]}
                for m in top_markets
            ],
        })
    finally:
        db.close()
@app.route("/api/logs/stream")
def stream_logs():
    """SSE endpoint - streams new log entries in real-time."""
    last_id = request.args.get("last_id", 0, type=int)
    def generate():
        nonlocal last_id
        if last_id == 0:
            try:
                db = get_db()
                rows = db.execute(
                    "SELECT * FROM system_logs WHERE level != 'ERROR' ORDER BY id DESC LIMIT 80"
                ).fetchall()
                db.close()
                rows = list(reversed(rows))
                for r in rows:
                    data = json.dumps(dict(r))
                    yield f"data: {data}\n\n"
                    last_id = r["id"]
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        while True:
            try:
                time.sleep(2)
                db = get_db()
                rows = db.execute(
                    "SELECT * FROM system_logs WHERE id > ? AND level != 'ERROR' ORDER BY id ASC LIMIT 50",
                    (last_id,)
                ).fetchall()
                db.close()
                for r in rows:
                    data = json.dumps(dict(r))
                    yield f"data: {data}\n\n"
                    last_id = r["id"]
            except GeneratorExit:
                return
            except Exception:
                time.sleep(5)
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

@app.route("/api/health")
def health():
    try:
        db = get_db()
        db.execute("SELECT 1")
        db.close()
        return jsonify({"status": "ok", "db": "connected", "time": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── AI AGENT CHAT ───────────────────────────────────────────
import requests as http_requests
from dotenv import load_dotenv

# Load API key
load_dotenv(os.path.expanduser("~/oracle-sentinel/config/.env"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route("/api/chat", methods=["POST"])
def ai_chat():
    """AI Agent chat with real-time sports data + news fetching."""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_message = data["message"]
        conversation_history = data.get("history", [])

        # ─── AUTO-FETCH: Sports Data + News ──────────────────
        live_context = ""
        data_sources = []
        market_question = user_message  # default: use raw message

        # Check if message contains Polymarket URL → fetch market data
        try:
            url_match = re.search(r'polymarket\.com/(?:event|sports/.+?)/([a-zA-Z0-9-]+)(?:\?|$|\s)', user_message + ' ')
            if url_match:
                slug = url_match.group(1)
                pc = PolymarketClient()
                market = pc.get_market_by_slug(slug)
                if market:
                    question = market.get('question', '')
                    description = market.get('description', '')
                    outcomes = market.get('outcomes', '')
                    prices = market.get('outcomePrices', '')
                    volume = market.get('volume', 0)
                    liquidity = market.get('liquidity', 0)
                    end_date = market.get('endDate', '')

                    # Parse prices
                    try:
                        price_list = json.loads(prices) if isinstance(prices, str) else prices
                        yes_price = float(price_list[0]) if price_list else 0
                        no_price = float(price_list[1]) if len(price_list) > 1 else 0
                    except:
                        yes_price, no_price = 0, 0

                    # Parse outcome names
                    try:
                        outcome_list = json.loads(outcomes) if isinstance(outcomes, str) else outcomes
                        outcome1 = outcome_list[0] if outcome_list else 'YES'
                        outcome2 = outcome_list[1] if len(outcome_list) > 1 else 'NO'
                    except:
                        outcome1, outcome2 = 'YES', 'NO'

                    live_context += f"""
POLYMARKET DATA (live from API):
  Question: {question}
  {outcome1} Price: ${yes_price:.4f} ({yes_price*100:.1f}%)
  {outcome2} Price: ${no_price:.4f} ({no_price*100:.1f}%)
  Volume: ${float(volume):,.0f}
  Liquidity: ${float(liquidity):,.0f}
  End Date: {end_date}

RESOLUTION RULES:
{description}
"""
                    market_question = question  # use actual market question
                    data_sources.append(f"Polymarket API (slug: {slug})")
        except Exception as e:
            live_context += f"\n[Polymarket fetch error: {e}]"

        # Check if message is about sports
        try:
            if SportsData.is_sports_market(market_question):
                sd = SportsData()
                sports_result = sd.get_data_for_market(market_question)
                if sports_result:
                    live_context += sports_result.get('prompt_text', '')
                    data_sources.append(f"SofaSport API ({sports_result['api_requests']} calls)")
        except Exception as e:
            live_context += f"\n[Sports data fetch error: {e}]"

        # Fetch fresh news (search + extract, no DB save)
        try:
            keywords = ['will ', 'predict', 'probability', 'chance', 'win ', 'price ', 'above ', 'below ']
            if any(kw in market_question.lower() for kw in keywords):
                nf = NewsFetcher()
                queries = nf.generate_queries(market_question)
                results = nf.search_news(queries)
                if results:
                    top_results = nf.filter_and_score(results)
                    news_text = "\n\nRECENT NEWS:\n"
                    count = 0
                    for r in top_results[:5]:
                        article = nf.extract_article(r['url'])
                        title = r.get('title', '?')
                        source = r.get('domain', '?')
                        if article and article.get('text'):
                            text = article['text'][:500]
                        else:
                            text = r.get('snippet', '')[:300]
                        news_text += f"\n--- [{source}] {title} ---\n{text}\n"
                        count += 1
                    if count > 0:
                        live_context += news_text
                        data_sources.append(f"News ({count} articles, full text)")
        except Exception as e:
            live_context += f"\n[News fetch error: {e}]"

        # ─── FETCH DATABASE STATS ────────────────────────────
        db_context = ""
        try:
            db = get_db()
            # Accuracy stats
            acc = db.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN signal_type = 'BUY_YES' THEN 1 ELSE 0 END) as buy_yes,
                    SUM(CASE WHEN signal_type = 'BUY_NO' THEN 1 ELSE 0 END) as buy_no,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN direction_correct = 0 THEN 1 ELSE 0 END) as wrong,
                    SUM(CASE WHEN direction_correct IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                    AVG(edge_at_signal) as avg_edge
                FROM prediction_tracking
            """).fetchone()
            
            # Recent predictions
            recent_preds = db.execute("""
                SELECT pt.signal_type, pt.ai_probability, pt.edge_at_signal, 
                       pt.confidence, pt.direction_correct, m.question
                FROM prediction_tracking pt
                JOIN markets m ON pt.market_id = m.id
                ORDER BY pt.created_at DESC LIMIT 5
            """).fetchall()
            
            # Confidence breakdown
            conf_stats = db.execute("""
                SELECT confidence,
                    COUNT(*) as total,
                    SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN direction_correct IS NOT NULL THEN 1 ELSE 0 END) as resolved
                FROM prediction_tracking
                GROUP BY confidence
            """).fetchall()
            total = acc['total'] or 0
            resolved = acc['resolved'] or 0
            correct = acc['correct'] or 0
            wrong = acc['wrong'] or 0
            accuracy_pct = round((correct / resolved * 100), 1) if resolved > 0 else 0
            
            db_context = f"""
ORACLE SENTINEL INTERNAL DATABASE:

ACCURACY STATS:
- Total Predictions: {total}
- Resolved: {resolved}
- Correct: {correct}
- Wrong: {wrong}
- Accuracy: {accuracy_pct}%
- Average Edge: {round(acc['avg_edge'] or 0, 2)}%

SIGNAL BREAKDOWN:
- BUY_YES Signals: {acc['buy_yes'] or 0}
- BUY_NO Signals: {acc['buy_no'] or 0}

CONFIDENCE BREAKDOWN:
"""
            for c in conf_stats:
                conf_resolved = c['resolved'] or 0
                conf_correct = c['correct'] or 0
                conf_acc = round((conf_correct / conf_resolved * 100), 1) if conf_resolved > 0 else 0
                db_context += f"- {c['confidence']}: {c['total']} predictions, {conf_resolved} resolved, {conf_acc}% accuracy\n"
            
            db_context += "\nRECENT PREDICTIONS:\n"
            for p in recent_preds:
                status = "CORRECT" if p['direction_correct'] == 1 else ("WRONG" if p['direction_correct'] == 0 else "TRACKING")
                db_context += f"- {p['signal_type']} | {p['question'][:50]}... | Edge: {p['edge_at_signal']}% | {status}\n"
            

            # Whale trades data
            whale_stats = db.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(trade_size) as total_volume,
                    AVG(trade_size) as avg_size,
                    SUM(CASE WHEN trade_side = 'BUY' THEN 1 ELSE 0 END) as buys,
                    SUM(CASE WHEN trade_side = 'SELL' THEN 1 ELSE 0 END) as sells
                FROM whale_trades_alerted
            """).fetchone()
            
            whale_24h = db.execute("""
                SELECT COUNT(*) as cnt, SUM(trade_size) as vol
                FROM whale_trades_alerted
                WHERE alerted_at >= datetime('now', '-24 hours')
            """).fetchone()
            
            recent_whales = db.execute("""
                SELECT market_title, trade_size, trade_side, outcome, trader_name, alerted_at
                FROM whale_trades_alerted
                ORDER BY alerted_at DESC LIMIT 5
            """).fetchall()
            
            large_whales = db.execute("""
                SELECT market_title, trade_size, trade_side, outcome, trader_name
                FROM whale_trades_alerted
                WHERE trade_size >= 10000
                ORDER BY trade_size DESC LIMIT 10
            """).fetchall()
            
            # Active signals
            active_sigs = db.execute("""
                SELECT m.question, json_extract(o.raw_data, '$.llm_original_recommendation') as signal,
                       o.edge, json_extract(o.raw_data, '$.confidence') as conf
                FROM opportunities o
                JOIN markets m ON o.market_id = m.id
                WHERE o.status = 'active'
                  AND m.closed = 0
                  AND (m.end_date IS NULL OR m.end_date > datetime('now'))
                  AND json_extract(o.raw_data, '$.llm_original_recommendation') IN ('BUY_YES', 'BUY_NO')
                  AND o.id = (SELECT MAX(o2.id) FROM opportunities o2 WHERE o2.market_id = o.market_id)
                ORDER BY ABS(o.edge) DESC LIMIT 10
            """).fetchall()
            
            # Market stats
            market_stats = db.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active
                FROM markets
            """).fetchone()
            
            db_context += f"""
WHALE TRADING DATA:
- Total Whale Trades (all time): {whale_stats['total_trades'] or 0}
- Total Whale Volume: ${whale_stats['total_volume'] or 0:,.0f}
- Average Trade Size: ${whale_stats['avg_size'] or 0:,.0f}
- Buy Trades: {whale_stats['buys'] or 0}
- Sell Trades: {whale_stats['sells'] or 0}
- Trades Last 24h: {whale_24h['cnt'] or 0}
- Volume Last 24h: ${whale_24h['vol'] or 0:,.0f}

RECENT WHALE TRADES (last 5):
"""
            for w in recent_whales:
                db_context += f"- {w['trader_name']}: ${w['trade_size']:,.0f} {w['trade_side']} {w['outcome']} on {w['market_title'][:40]}...\n"
            
            if large_whales:
                db_context += "\nLARGE WHALE TRADES (>$10,000):\n"
                for w in large_whales:
                    db_context += f"- {w['trader_name']}: ${w['trade_size']:,.0f} {w['trade_side']} {w['outcome']} on {w['market_title'][:40]}...\n"
            
            db_context += """
ACTIVE TRADING SIGNALS:
"""
            for s in active_sigs:
                db_context += f"- {s['signal']} | {s['question'][:45]}... | Edge: {s['edge']}% | {s['conf']}\n"
            
            db_context += f"""
MARKET COVERAGE:
- Total Markets in Database: {market_stats['total'] or 0}
- Active Markets Monitored: {market_stats['active'] or 0}
"""

            live_context = db_context + live_context
            db.close()
            data_sources.insert(0, "Oracle Sentinel Database")
        except Exception as e:
            live_context += f"\n[Database fetch error: {e}]"

        # ─── SYSTEM PROMPT ───────────────────────────────────
        current_time_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        system_prompt = f"""You are Oracle Sentinel AI Agent.
CURRENT TIME: {current_time_utc}
CRITICAL: Use this current time to calculate how far away events are. Do NOT assume you are in 2025 - check the current time above. You are powered by Claude Sonnet 4.5 via OpenRouter. When asked about yourself or your model, always identify as "Oracle Sentinel powered by Claude Sonnet 4.5". Never mention other version numbers. You are an expert prediction market analyst with access to REAL-TIME data.

Your capabilities:
1. Analyze Polymarket markets with LIVE sports data (standings, form, streaks, stats)
2. Analyze markets with FRESH news articles fetched in real-time
3. Check resolution rules carefully for edge cases and loopholes
4. Assess probability based on facts and data, not speculation
5. Provide trading signals (BUY_YES, BUY_NO, NO_TRADE)
6. Calculate edge vs market price
7. Explain your reasoning clearly

SPORTS ANALYSIS RULES:
- Use league standings, recent form, and betting streaks from live data
- Position gap to leader matters hugely for season winner markets
- Recent form (last 10 matches) reveals momentum
- Fan predictions with 30K+ votes are meaningful crowd signals
- Don't rely on team reputation alone — use the DATA

GENERAL RULES:
- Read resolution rules FIRST
- Be calibrated - don't be overconfident
- Consider tail risks and surprises
- Provide confidence level (HIGH/MEDIUM/LOW)

FORMATTING RULES (STRICT):
- NEVER use markdown: no #, ##, **, *, ```, or any markdown syntax
- NEVER use emojis or special symbols
- Use plain text only with clear section headers in UPPERCASE
- Use dashes (-) for bullet points
- Use line breaks to separate sections

Format your analysis with these plain text sections:

MARKET OVERVIEW
(market details here)

RESOLUTION RULES
(if available)

LIVE SPORTS DATA
(if sports market)

NEWS SUMMARY
(key findings)

FACTORS FOR
- factor 1
- factor 2

FACTORS AGAINST
- factor 1
- factor 2

AI PROBABILITY ASSESSMENT
(your calibrated estimate with reasoning)

EDGE VS MARKET PRICE
(comparison and edge calculation)

SIGNAL: BUY_YES / BUY_NO / NO_TRADE
(recommendation with confidence level)

RISKS
- risk 1
- risk 2

Keep responses concise but data-driven. Plain text only, no formatting."""

        # ─── BUILD MESSAGES ──────────────────────────────────
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Append live context to user message
        if live_context:
            enhanced_message = f"{user_message}\n\n--- LIVE DATA (fetched just now) ---{live_context}"
        else:
            enhanced_message = user_message

        messages.append({"role": "user", "content": enhanced_message})

        # ─── CALL LLM ───────────────────────────────────────
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://oraclesentinel.xyz",
            "X-Title": "Oracle Sentinel AI Agent"
        }

        payload = {
            "model": "anthropic/claude-sonnet-4.5",
            "messages": messages,
            "max_tokens": 2500,
            "temperature": 0.3
        }

        response = http_requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            return jsonify({
                "error": "AI service unavailable",
                "details": response.text[:200]
            }), 503

        result = response.json()
        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "No response from AI")

        return jsonify({
            "response": ai_response,
            "data_sources": data_sources,
            "timestamp": datetime.utcnow().isoformat()
        })

    except http_requests.exceptions.Timeout:
        return jsonify({"error": "AI request timed out. Please try again."}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to AI service. Please try again later."}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  ORACLE SENTINEL — API Server")
    print(f"  Database: {DB_PATH}")
    print(f"  URL: http://localhost:8099")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8099, debug=False)