#!/usr/bin/env python3
"""
Polymarket Intelligence System - Simple Scheduler
Runs periodic updates for markets and prices
"""

import time
import schedule
from datetime import datetime
from polymarket_client import PolymarketClient
from price_updater import PriceUpdater
from opportunity_detector import OpportunityDetector


def sync_markets():
    """Sync markets every hour"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📊 Syncing markets...")
    client = PolymarketClient()
    result = client.sync_markets(limit=100)
    print(f"   Synced {result['synced']}/{result['fetched']} (skipped {result['skipped']})")
    if result['skip_reasons']:
        print(f"   📋 Skipped: {result['skip_reasons']}")


def update_prices():
    """Update prices every 5 minutes"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💰 Updating prices...")
    updater = PriceUpdater()
    result = updater.update_all_prices()
    print(f"   Updated {result['success']}/{result['total']} prices")


def detect_opportunities():
    """Run opportunity detection every 15 minutes"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ðŸ"Ž Running opportunity detection...")
    detector = OpportunityDetector()
    results = detector.run_all(save=True)
    s = results['summary']
    print(f"   Found {s['total']} opportunities")
    print(f"   Complement: {s['complement_mismatch']} | Spreads: {s['wide_spread']} | Momentum: {s['momentum']}")
    print(f"   Volume spikes: {s['volume_spike']} | Near-extreme: {s['near_extreme']}")


def show_status():
    """Show current status"""
    client = PolymarketClient()
    markets = client.get_all_markets()
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ðŸ"‹ Status:")
    print(f"   Active markets: {len(markets)}")
    
    # Top markets by volume
    print("   Top markets:")
    for m in markets[:3]:
        print(f"   â€¢ {m['question'][:40]}... (${m['volume_24h']:,.0f})")


def main():
    print("="*60)
    print("🤖 Polymarket Intelligence Scheduler")
    print("="*60)
    print("\nSchedule:")
    print("   • Market sync: Every 1 hour")
    print("   • Price update: Every 5 minutes")
    print("   • Opportunity scan: Every 15 minutes")
    print("   • Status check: Every 10 minutes")
    print("\nPress Ctrl+C to stop\n")
    
    # Initial run
    sync_markets()
    update_prices()
    detect_opportunities()
    show_status()
    
    # Schedule tasks
    schedule.every(1).hours.do(sync_markets)
    schedule.every(5).minutes.do(update_prices)
    schedule.every(15).minutes.do(detect_opportunities)
    schedule.every(10).minutes.do(show_status)
    
    # Run scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped")