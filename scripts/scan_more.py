#!/usr/bin/env python3
"""
Scan More Markets - Expand analysis to find bigger edges
Focus on mid-volume markets where inefficiency is more likely
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from polymarket_client import PolymarketClient
from price_updater import PriceUpdater
from news_fetcher import NewsFetcher
from ai_brain import AIBrain
from accuracy_tracker import AccuracyTracker


import requests as req

from config_loader import BOT_TOKEN, CHAT_IDS

def send_telegram(text):
    """Send formatted message to all registered Telegram chats"""
    for chat_id in CHAT_IDS:
        try:
            req.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10
            )
        except Exception as e:
            print(f"   ⚠️ Telegram send failed: {e}")

def format_signal_message(analyzed, high_edge, buy_yes, buy_no, tracked_count):
    """Build consistent, professional Telegram notification"""
    lines = []
    lines.append("🔥 <b>ORACLE SENTINEL — Signal Report</b>")
    lines.append(f"⏱ Scan: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    lines.append(f"📊 Markets analyzed: {len(analyzed)}")
    lines.append(f"🎯 Predictions tracked: {tracked_count}")
    lines.append("")

    if high_edge:
        lines.append(f"⚡ <b>{len(high_edge)} Actionable Signals:</b>")
        lines.append("")
        for i, r in enumerate(high_edge[:8]):
            q = r.get('question', '')[:50]
            e = r.get('edge', 0)
            ai = r.get('ai_probability', 0) * 100
            conf = r.get('confidence', '?')
            rec = r.get('recommendation', '?')
            emoji = "🟢" if rec == "BUY_YES" else "🔴"
            lines.append(f"{emoji} <b>{i+1}. {q}</b>")
            lines.append(f"   Edge: {e:+.1f}% | AI: {ai:.0f}% | Conf: {conf}")
            lines.append(f"   Signal: <b>{rec}</b>")
            lines.append("")
    else:
        lines.append("✅ No actionable signals detected this cycle.")
        lines.append("")

    lines.append(f"📈 BUY_YES: {len(buy_yes)} | 📉 BUY_NO: {len(buy_no)}")
    lines.append("")
    lines.append("🤖 <i>Oracle Sentinel — Autonomous Prediction Intelligence</i>")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("🔍 Oracle Sentinel - Extended Market Scan")
    print("=" * 60)

    # Initialize tracker
    tracker = AccuracyTracker()

    # Step 1: Sync more markets
    print("\n📊 Step 1: Syncing 100 markets...")
    client = PolymarketClient()
    result = client.sync_markets(limit=100)
    print(f"   Synced {result['synced']}/{result['fetched']} (skipped {result['skipped']})")
    if result['skip_reasons']:
        print(f"   📋 Skipped: {result['skip_reasons']}")

    # Step 2: Update all prices
    print("\n💰 Step 2: Updating prices...")
    updater = PriceUpdater()
    price_result = updater.update_all_prices()
    print(f"   Updated {price_result['success']}/{price_result['total']} prices")

    # Step 2.5: Update accuracy snapshots
    print("\n📸 Step 2.5: Updating accuracy snapshots...")
    snap_result = tracker.update_snapshots()
    print(f"   Snapshots updated: {snap_result['updated']}")
    print(f"   Newly resolved: {snap_result['resolved']}")
    print(f"   Total tracked: {snap_result['total_tracked']}")

    # Step 3: Fetch news for more markets (top 20 by volume)
    print("\n📰 Step 3: Fetching news for top 20 markets...")
    fetcher = NewsFetcher()
    news_result = fetcher.fetch_for_top_markets(limit=20)
    print(f"   Processed {news_result['markets_processed']} markets (skipped {news_result.get('markets_skipped', 0)} with fresh news)")
    print(f"   Total articles: {news_result['total_articles']}")

    # Step 4: AI Analysis on all markets with articles
    print("\n🧠 Step 4: Running AI analysis...")
    brain = AIBrain()
    results = brain.analyze_top_markets(limit=20)

    # Step 5: Track BUY signals (with coin-flip filter)
    print("\n📊 Step 5: Recording predictions for accuracy tracking...")
    tracked_count = 0
    skipped_coinflip = 0

    for r in results:
        # Skip coin-flip markets (price 45-55%)
        market_price = r.get('market_price', 0.5)
        if 0.45 <= market_price <= 0.55:
            skipped_coinflip += 1
            continue
        
        if r.get('recommendation') in ('BUY_YES', 'BUY_NO') and r.get('opportunity_id'):
            # Skip if market already tracked
            db_check = tracker._get_db()
            already = db_check.execute(
                "SELECT COUNT(*) FROM prediction_tracking WHERE market_id = ?",
                (r['market_id'],)
            ).fetchone()[0]
            db_check.close()
            if already > 0:
                continue

            track_id = tracker.record_prediction(
                opportunity_id=r['opportunity_id'],
                market_id=r['market_id'],
                result=r
            )
            if track_id:
                tracked_count += 1

    print(f"   New predictions tracked: {tracked_count}")
    print(f"   Skipped (coin-flip zone): {skipped_coinflip}")

    # =========================================================
    # RESULTS
    # =========================================================
    print()
    print("=" * 60)
    print("📋 FULL ANALYSIS REPORT")
    print("=" * 60)

    # Sort by absolute edge
    analyzed = [r for r in results if r.get('status') == 'analyzed']
    analyzed.sort(key=lambda x: abs(x.get('edge', 0)), reverse=True)

    # Print all results
    for i, r in enumerate(analyzed):
        question = r.get('question', 'Unknown')[:55]
        market = r.get('market_price', 0) * 100
        ai = r.get('ai_probability', 0) * 100
        edge = r.get('edge', 0)
        conf = r.get('confidence', '?')
        rec = r.get('recommendation', '?')

        # Edge indicator
        if abs(edge) >= 10:
            indicator = "🔴"
        elif abs(edge) >= 5:
            indicator = "🟡"
        elif abs(edge) >= 3:
            indicator = "🟢"
        else:
            indicator = "⚪"

        print(f"\n  {indicator} #{i+1} {question}...")
        print(f"     Market: {market:.1f}% | AI: {ai:.1f}% | Edge: {edge:+.1f}%")
        print(f"     Confidence: {conf} | Rec: {rec}")
        
        reasoning = r.get('reasoning', '')[:100]
        if reasoning:
            print(f"     {reasoning}")

        # Show key factors for high-edge opportunities
        if abs(edge) >= 3:
            factors_for = r.get('key_factors_for', [])
            factors_against = r.get('key_factors_against', [])
            if factors_for:
                print(f"     FOR:  {', '.join(str(f)[:40] for f in factors_for[:3])}")
            if factors_against:
                print(f"     AGAINST: {', '.join(str(f)[:40] for f in factors_against[:3])}")

    # =========================================================
    # SUMMARY STATS
    # =========================================================
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    total = len(analyzed)
    edges = [abs(r.get('edge', 0)) for r in analyzed]
    
    buy_yes = [r for r in analyzed if r.get('recommendation') == 'BUY_YES']
    buy_no = [r for r in analyzed if r.get('recommendation') == 'BUY_NO']
    no_trade = [r for r in analyzed if r.get('recommendation') == 'NO_TRADE']
    skip = [r for r in analyzed if r.get('recommendation') == 'SKIP']
    
    high_edge = [r for r in analyzed if abs(r.get('edge', 0)) >= 5 and r.get('recommendation') in ('BUY_YES', 'BUY_NO')]
    med_edge = [r for r in analyzed if 3 <= abs(r.get('edge', 0)) < 5]
    low_edge = [r for r in analyzed if abs(r.get('edge', 0)) < 3]

    print(f"  Total markets analyzed: {total}")
    print(f"  Avg absolute edge:     {sum(edges)/len(edges):.1f}%" if edges else "")
    print(f"  Max edge:              {max(edges):.1f}%" if edges else "")
    print()
    print(f"  🔴 High edge (>5%):    {len(high_edge)}")
    print(f"  🟡 Medium edge (3-5%): {len(med_edge)}")
    print(f"  ⚪ Low edge (<3%):     {len(low_edge)}")
    print()
    print(f"  Recommendations:")
    print(f"    BUY_YES:  {len(buy_yes)}")
    print(f"    BUY_NO:   {len(buy_no)}")
    print(f"    NO_TRADE: {len(no_trade)}")
    print(f"    SKIP:     {len(skip)}")

    if high_edge:
        print(f"\n  🏆 TOP OPPORTUNITIES:")
        for r in high_edge[:5]:
            q = r.get('question', '')[:45]
            e = r.get('edge', 0)
            rec = r.get('recommendation', '?')
            print(f"    [{rec}] {q}... (edge: {e:+.1f}%)")

    print(f"\n{'='*60}")

    # Send Telegram notification
    print("\n📱 Sending Telegram notification...")
    try:
        msg = format_signal_message(analyzed, high_edge, buy_yes, buy_no, tracked_count)
        send_telegram(msg)
        print("   ✅ Telegram notification sent!")
    except Exception as e:
        print(f"   ⚠️ Telegram failed: {e}")

    # Print accuracy report
    tracker.print_report()


if __name__ == '__main__':
    main()