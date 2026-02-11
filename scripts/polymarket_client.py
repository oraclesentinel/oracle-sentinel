#!/usr/bin/env python3
"""
Polymarket Intelligence System - Polymarket API Client
Based on official Polymarket documentation and py-clob-client

API Endpoints:
- Gamma API: https://gamma-api.polymarket.com (market metadata)
- CLOB API: https://clob.polymarket.com (prices, orderbook)
"""

import requests
import sqlite3
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')

# Official Polymarket API endpoints
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"


class PolymarketClient:
    """
    Client for Polymarket APIs
    
    Uses:
    - Gamma API for market metadata (no auth required)
    - CLOB API for prices and orderbook (no auth for read-only)
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.gamma_url = GAMMA_API_BASE
        self.clob_url = CLOB_API_BASE
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'PolymarketIntel/1.0'
        })
    
    def _get_db(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _log(self, level: str, message: str):
        """Log to console and database"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'polymarket_client', message)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # Don't fail if logging fails
    
    # ================================================================
    # GAMMA API - Market Metadata (Read-only, no auth)
    # Reference: https://docs.polymarket.com/developers/gamma-markets-api/
    # ================================================================
    
    def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
        order: str = "volume24hr",
        ascending: bool = False
    ) -> List[Dict]:
        """
        Fetch markets from Gamma API
        
        Args:
            limit: Max markets to return (default 100)
            offset: Pagination offset
            active: Only active markets
            closed: Include closed markets
            order: Sort field (volume24hr, liquidity, startDate, endDate)
            ascending: Sort direction
        
        Returns:
            List of market dictionaries
        """
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'active': str(active).lower(),
                'closed': str(closed).lower(),
                'order': order,
                'ascending': str(ascending).lower()
            }
            
            response = self.session.get(
                f"{self.gamma_url}/markets",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            markets = response.json()
            self._log('INFO', f"Fetched {len(markets)} markets from Gamma API")
            return markets
            
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch markets: {e}")
            return []
    
    def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """Fetch single market by ID"""
        try:
            response = self.session.get(
                f"{self.gamma_url}/markets/{market_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch market {market_id}: {e}")
            return None
    
    def get_market_by_slug(self, slug: str) -> Optional[Dict]:
        """Fetch single market by slug"""
        try:
            response = self.session.get(
                f"{self.gamma_url}/markets",
                params={'slug': slug},
                timeout=30
            )
            response.raise_for_status()
            markets = response.json()
            return markets[0] if markets else None
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch market by slug {slug}: {e}")
            return None
    
    def get_events(self, limit: int = 50, active: bool = True) -> List[Dict]:
        """Fetch events (groups of related markets)"""
        try:
            params = {
                'limit': limit,
                'active': str(active).lower()
            }
            response = self.session.get(
                f"{self.gamma_url}/events",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch events: {e}")
            return []
    
    # ================================================================
    # CLOB API - Prices & Orderbook (Read-only, no auth)
    # Reference: https://docs.polymarket.com/developers/CLOB/
    # ================================================================
    
    def get_midpoint(self, token_id: str) -> Optional[float]:
        """
        Get midpoint price for a token
        
        Args:
            token_id: The token/condition ID
            
        Returns:
            Midpoint price as float, or None
        """
        try:
            response = self.session.get(
                f"{self.clob_url}/midpoint",
                params={'token_id': token_id},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get('mid', 0))
        except Exception as e:
            self._log('ERROR', f"Failed to get midpoint for {token_id}: {e}")
            return None
    
    def get_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """
        Get best price for a token
        
        Args:
            token_id: The token/condition ID
            side: "BUY" or "SELL"
            
        Returns:
            Best price as float, or None
        """
        try:
            response = self.session.get(
                f"{self.clob_url}/price",
                params={'token_id': token_id, 'side': side},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get('price', 0))
        except Exception as e:
            self._log('ERROR', f"Failed to get price for {token_id}: {e}")
            return None
    
    def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """
        Get full orderbook for a token
        
        Args:
            token_id: The token/condition ID
            
        Returns:
            Orderbook dict with 'bids' and 'asks'
        """
        try:
            response = self.session.get(
                f"{self.clob_url}/book",
                params={'token_id': token_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._log('ERROR', f"Failed to get orderbook for {token_id}: {e}")
            return None
    
    def get_spread(self, token_id: str) -> Optional[Dict]:
        """Get bid-ask spread for a token"""
        try:
            response = self.session.get(
                f"{self.clob_url}/spread",
                params={'token_id': token_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._log('ERROR', f"Failed to get spread for {token_id}: {e}")
            return None
    
    # ================================================================
    # Database Operations
    # ================================================================
    
    def save_market(self, market: Dict) -> int:
        """
        Save or update market in database
        
        Returns:
            Database ID of the market
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Extract fields from Gamma API response
        polymarket_id = str(market.get('id', ''))
        condition_id = market.get('conditionId', '')
        slug = market.get('slug', '')
        question = market.get('question', 'Unknown')
        description = market.get('description', '')
        
        # Outcomes and prices - API returns as JSON strings
        raw_outcomes = market.get('outcomes', '[]')
        raw_prices = market.get('outcomePrices', '[]')
        
        # Normalize to JSON string for storage
        if isinstance(raw_outcomes, list):
            outcomes = json.dumps(raw_outcomes)
        else:
            outcomes = str(raw_outcomes)
        
        if isinstance(raw_prices, list):
            outcome_prices = json.dumps(raw_prices)
        else:
            outcome_prices = str(raw_prices)
        
        resolution_source = market.get('resolutionSource', '')
        end_date = market.get('endDate', '')
        volume = float(market.get('volume', 0) or 0)
        volume_24h = float(market.get('volume24hr', 0) or 0)
        liquidity = float(market.get('liquidity', 0) or 0)
        active = 1 if market.get('active', True) else 0
        closed = 1 if market.get('closed', False) else 0
        
        # Upsert market
        cursor.execute('''
            INSERT INTO markets (
                polymarket_id, condition_id, slug, question, description,
                outcomes, outcome_prices, resolution_source, end_date,
                volume, volume_24h, liquidity, active, closed, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(polymarket_id) DO UPDATE SET
                condition_id = excluded.condition_id,
                slug = excluded.slug,
                question = excluded.question,
                description = excluded.description,
                outcomes = excluded.outcomes,
                outcome_prices = excluded.outcome_prices,
                resolution_source = excluded.resolution_source,
                end_date = excluded.end_date,
                volume = excluded.volume,
                volume_24h = excluded.volume_24h,
                liquidity = excluded.liquidity,
                active = excluded.active,
                closed = excluded.closed,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            polymarket_id, condition_id, slug, question, description,
            outcomes, outcome_prices, resolution_source, end_date,
            volume, volume_24h, liquidity, active, closed
        ))
        
        conn.commit()
        
        # Get market ID
        cursor.execute(
            'SELECT id FROM markets WHERE polymarket_id = ?',
            (polymarket_id,)
        )
        market_db_id = cursor.fetchone()[0]
        
        # ============================================
        # Parse clobTokenIds - ALWAYS a JSON string from API
        # e.g. '["52607315...", "10898827..."]'
        # ============================================
        raw_tokens = market.get('clobTokenIds', '')
        
        # Parse to list
        token_ids = []
        if isinstance(raw_tokens, str) and raw_tokens.startswith('['):
            try:
                token_ids = json.loads(raw_tokens)
            except json.JSONDecodeError:
                token_ids = []
        elif isinstance(raw_tokens, list):
            token_ids = raw_tokens
        
        # Parse outcomes to list
        outcomes_list = []
        if isinstance(raw_outcomes, str) and raw_outcomes.startswith('['):
            try:
                outcomes_list = json.loads(raw_outcomes)
            except:
                outcomes_list = []
        elif isinstance(raw_outcomes, list):
            outcomes_list = raw_outcomes
        
        # Parse outcome prices to list
        prices_list = []
        if isinstance(raw_prices, str) and raw_prices.startswith('['):
            try:
                prices_list = json.loads(raw_prices)
            except:
                prices_list = []
        elif isinstance(raw_prices, list):
            prices_list = raw_prices
        
        # Save each token
        for i, token_id in enumerate(token_ids):
            if token_id and isinstance(token_id, str) and len(token_id) > 10:
                outcome = outcomes_list[i] if i < len(outcomes_list) else f"Outcome {i}"
                
                price = 0.0
                if i < len(prices_list):
                    try:
                        price = float(prices_list[i])
                    except (ValueError, TypeError):
                        price = 0.0
                
                cursor.execute('''
                    INSERT INTO tokens (market_id, token_id, outcome, price)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(token_id) DO UPDATE SET
                        outcome = excluded.outcome,
                        price = excluded.price
                ''', (market_db_id, token_id, outcome, price))
        
        conn.commit()
        conn.close()
        
        return market_db_id
    
    def save_price(self, market_id: int, token_id: str, price: float, 
                   bid: float = None, ask: float = None, volume_24h: float = None):
        """Save price snapshot"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        spread = (ask - bid) if (ask and bid) else None
        
        cursor.execute('''
            INSERT INTO prices (market_id, token_id, price, bid, ask, spread, volume_24h)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (market_id, token_id, price, bid, ask, spread, volume_24h))
        
        conn.commit()
        conn.close()
    
    def get_all_markets(self, active_only: bool = True) -> List[Dict]:
        """Get all markets from database"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, polymarket_id, slug, question, outcome_prices, 
                   volume_24h, liquidity, active
            FROM markets
        '''
        if active_only:
            query += ' WHERE active = 1'
        query += ' ORDER BY volume_24h DESC'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'polymarket_id': row[1],
                'slug': row[2],
                'question': row[3],
                'outcome_prices': json.loads(row[4]) if row[4] else [],
                'volume_24h': row[5],
                'liquidity': row[6],
                'active': bool(row[7])
            }
            for row in rows
        ]
    
    # ================================================================
    # High-Level Operations
    # ================================================================
    
    # ================================================================
    # Market Filters
    # ================================================================

    # Skip keywords — daily sports matches, trivial daily markets
    SKIP_PATTERNS = [
        # Daily sports matches (specific games, not futures/championships)
        r'\bvs\.?\b',                    # "Team A vs Team B"
        r'\bversus\b',
        r'\bmoneyline\b',
        r'\bspread\b.*\bgame\b',
        r'\bover/under\b',
        r'\btotal points\b',
        r'\bwho will win .+ game\b',
        # Daily match with date: "Will X win on 2026-02-01?"
        r'\bwin on \d{4}-\d{2}-\d{2}\b',
        # BO3/BO5 esports matches
        r'\(BO\d\)',
        # Daily weather / trivial
        r'\btemperature\b.*\btoday\b',
        r'\brain today\b',
        # Daily token price (short-term noise)
        r'\bprice of .+ (today|tonight|by end of day)\b',
    ]

    # Skip categories/tags from Gamma API
    SKIP_TAGS = {
        'nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball',
        'baseball', 'hockey', 'tennis', 'mma', 'ufc', 'boxing',
        'cricket', 'rugby', 'golf', 'f1', 'nascar',
    }

    def _should_skip_market(self, market: Dict) -> str:
        """
        Check if market should be skipped.
        Returns skip reason string, or empty string if OK.
        """
        # --- Filter 1: Already resolved / closed ---
        if market.get('closed', False):
            return 'closed'

        if not market.get('active', True):
            return 'inactive'

        # --- Filter 2: Expired (end_date in the past) ---
        end_date_str = market.get('endDate', '')
        if end_date_str:
            try:
                # Polymarket uses ISO format: "2025-12-31T23:59:59Z"
                end_clean = end_date_str.replace('Z', '+00:00')
                end_dt = datetime.fromisoformat(end_clean)
                # Compare as naive (strip tz)
                end_naive = end_dt.replace(tzinfo=None)
                if end_naive < datetime.now():
                    return f'expired ({end_date_str[:10]})'
            except (ValueError, TypeError):
                pass  # Can't parse, keep the market

        # --- Filter 3: Daily sports / trivial by question text ---
        question = market.get('question', '').lower()
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, question, re.IGNORECASE):
                return f'skip_pattern ({pattern})'

        # --- Filter 4: Sports category by tags ---
        # Gamma API may return 'tags' as list of dicts or strings
        raw_tags = market.get('tags', [])
        if isinstance(raw_tags, list):
            for tag in raw_tags:
                tag_label = ''
                if isinstance(tag, dict):
                    tag_label = tag.get('label', tag.get('slug', '')).lower()
                elif isinstance(tag, str):
                    tag_label = tag.lower()
                if tag_label in self.SKIP_TAGS:
                    return f'skip_tag ({tag_label})'

        # Also check slug for sports keywords
        slug = market.get('slug', '').lower()
        for sport in self.SKIP_TAGS:
            if sport in slug:
                return f'skip_slug ({sport})'

        return ''  # OK, don't skip

    def sync_markets(self, limit: int = 100) -> dict:
        """
        Sync markets from Polymarket to local database.
        Filters out expired, resolved, and daily sports markets.

        Returns:
            dict with synced/skipped/fetched counts
        """
        self._log('INFO', f"Starting market sync (limit={limit})...")

        markets = self.get_markets(limit=limit, active=True)

        if not markets:
            self._log('WARN', "No markets fetched")
            return {'fetched': 0, 'synced': 0, 'skipped': 0, 'skip_reasons': {}}

        saved = 0
        skipped = 0
        skip_reasons = {}

        for market in markets:
            # Apply filters
            reason = self._should_skip_market(market)
            if reason:
                skipped += 1
                bucket = reason.split(' ')[0]  # e.g. 'closed', 'expired', 'skip_pattern'
                skip_reasons[bucket] = skip_reasons.get(bucket, 0) + 1
                continue

            try:
                self.save_market(market)
                saved += 1
            except Exception as e:
                self._log('ERROR', f"Failed to save market: {e}")

        # Update last sync time
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES ('last_sync', ?, CURRENT_TIMESTAMP)
        ''', (datetime.now().isoformat(),))
        conn.commit()
        conn.close()

        self._log('INFO', f"Synced {saved}/{len(markets)} markets (skipped {skipped})")
        if skip_reasons:
            self._log('INFO', f"Skip breakdown: {skip_reasons}")

        return {
            'fetched': len(markets),
            'synced': saved,
            'skipped': skipped,
            'skip_reasons': skip_reasons
        }


    # ================================================================
    # Multi-outcome Market Support (Events)
    # ================================================================

    def get_event_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Fetch event by slug (for multi-outcome markets)
        
        Events contain multiple markets, each with their own outcomes.
        Example: "In which month will SpaceX IPO?" has markets for each month.
        """
        try:
            response = self.session.get(
                f"{self.gamma_url}/events",
                params={'slug': slug},
                timeout=30
            )
            response.raise_for_status()
            events = response.json()
            
            if events and len(events) > 0:
                event = events[0]
                self._log('INFO', f"Fetched event '{slug}' with {len(event.get('markets', []))} markets")
                return event
            return None
            
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch event by slug {slug}: {e}")
            return None

    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Fetch event by ID"""
        try:
            response = self.session.get(
                f"{self.gamma_url}/events/{event_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._log('ERROR', f"Failed to fetch event {event_id}: {e}")
            return None

    def get_market_or_event(self, slug: str) -> Dict:
        """
        Smart fetch: Try market first, then event.
        Returns unified structure for both binary and multi-outcome markets.
        
        Returns:
            Dict with:
            - type: 'binary' or 'multi_outcome' or None
            - question: Main question
            - description: Resolution rules
            - outcomes: List of {name, price, probability} dicts
            - volume: Total volume
            - liquidity: Total liquidity
            - end_date: End date
            - raw: Original API response
        """
        result = {
            'type': None,
            'question': None,
            'description': None,
            'outcomes': [],
            'volume': 0,
            'liquidity': 0,
            'end_date': None,
            'raw': None
        }
        
        # Try as single market first
        market = self.get_market_by_slug(slug)
        if market:
            result['type'] = 'binary'
            result['question'] = market.get('question', '')
            result['description'] = market.get('description', '')
            result['volume'] = float(market.get('volume', 0) or 0)
            result['liquidity'] = float(market.get('liquidity', 0) or 0)
            result['end_date'] = market.get('endDate', '')
            result['raw'] = market
            
            # Parse outcomes and prices
            outcomes = market.get('outcomes', '[]')
            prices = market.get('outcomePrices', '[]')
            
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except:
                    outcomes = ['YES', 'NO']
            
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except:
                    prices = [0, 0]
            
            for i, outcome in enumerate(outcomes):
                price = float(prices[i]) if i < len(prices) else 0
                result['outcomes'].append({
                    'name': outcome,
                    'price': price,
                    'probability': price * 100
                })
            
            return result
        
        # Try as event (multi-outcome)
        event = self.get_event_by_slug(slug)
        if event:
            result['type'] = 'multi_outcome'
            result['question'] = event.get('title', event.get('question', ''))
            result['description'] = event.get('description', '')
            result['end_date'] = event.get('endDate', '')
            result['raw'] = event
            
            total_volume = 0
            total_liquidity = 0
            markets = event.get('markets', [])
            
            for mkt in markets:
                mkt_volume = float(mkt.get('volume', 0) or 0)
                mkt_liquidity = float(mkt.get('liquidity', 0) or 0)
                total_volume += mkt_volume
                total_liquidity += mkt_liquidity
                
                # Each market in event is an "outcome"
                mkt_question = mkt.get('question', mkt.get('groupItemTitle', 'Unknown'))
                
                # Get YES price for this outcome
                prices = mkt.get('outcomePrices', '[]')
                if isinstance(prices, str):
                    try:
                        prices = json.loads(prices)
                    except:
                        prices = [0]
                
                yes_price = float(prices[0]) if prices else 0
                
                result['outcomes'].append({
                    'name': mkt_question,
                    'price': yes_price,
                    'probability': yes_price * 100,
                    'volume': mkt_volume,
                    'liquidity': mkt_liquidity,
                    'market_id': mkt.get('id', ''),
                    'slug': mkt.get('slug', '')
                })
            
            # Sort by probability descending
            result['outcomes'].sort(key=lambda x: x['probability'], reverse=True)
            result['volume'] = total_volume
            result['liquidity'] = total_liquidity
            
            return result
        
        # Nothing found
        return result



def test_connection():
    """Test Polymarket API connection"""
    print("="*60)
    print("🧪 Testing Polymarket API Connection")
    print("="*60)
    
    client = PolymarketClient()
    
    # Test 1: Gamma API - Get Markets
    print("\n📊 Test 1: Fetching markets from Gamma API...")
    markets = client.get_markets(limit=5)
    
    if markets:
        print(f"   ✅ Got {len(markets)} markets")
        print("\n   Sample markets:")
        for m in markets[:3]:
            question = m.get('question', 'Unknown')[:60]
            volume = m.get('volume24hr', 0) or 0
            prices = m.get('outcomePrices', [])
            print(f"   • {question}...")
            print(f"     Volume 24h: ${volume:,.0f}")
            print(f"     Prices: {prices}")
    else:
        print("   ❌ Failed to fetch markets")
        return False
    
    # Test 2: Get token ID and price (FIXED)
    print("\n💰 Test 2: Fetching price from CLOB API...")
    
    # Find a market with valid token IDs
    token_id = None
    for m in markets:
        # clobTokenIds bisa berupa string JSON atau list
        raw_tokens = m.get('clobTokenIds')
        
        if isinstance(raw_tokens, str):
            # Parse JSON string jika perlu
            try:
                import json
                token_ids = json.loads(raw_tokens)
            except:
                token_ids = []
        elif isinstance(raw_tokens, list):
            token_ids = raw_tokens
        else:
            token_ids = []
        
        # Cari token ID yang valid (panjang > 10 karakter)
        for tid in token_ids:
            if tid and len(str(tid)) > 10:
                token_id = str(tid)
                break
        
        if token_id:
            break
    
    if token_id:
        print(f"   Token ID: {token_id[:40]}...")
        
        # Test midpoint
        mid = client.get_midpoint(token_id)
        if mid is not None:
            print(f"   ✅ Midpoint price: ${mid:.4f}")
        else:
            print("   ⚠️ Midpoint not available")
        
        # Test spread
        spread = client.get_spread(token_id)
        if spread:
            print(f"   ✅ Spread: {spread}")
        else:
            print("   ⚠️ Spread not available")
        
        # Test orderbook
        book = client.get_orderbook(token_id)
        if book:
            bids = len(book.get('bids', []))
            asks = len(book.get('asks', []))
            print(f"   ✅ Orderbook: {bids} bids, {asks} asks")
    else:
        print("   ⚠️ No valid token IDs found in markets")
    
    # Test 3: Sync to database
    print("\n💾 Test 3: Syncing to database...")
    result = client.sync_markets(limit=20)
    print(f"   ✅ Synced {result['synced']}/{result['fetched']} markets (skipped {result['skipped']})")
    if result['skip_reasons']:
        print(f"   📋 Skip reasons: {result['skip_reasons']}")
    
    # Show database contents
    print("\n📋 Database contents (top 5 by volume):")
    db_markets = client.get_all_markets()
    for m in db_markets[:5]:
        print(f"   • [{m['id']}] {m['question'][:50]}...")
        print(f"     Prices: {m['outcome_prices']}, Vol: ${m['volume_24h']:,.0f}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    
    return True


if __name__ == '__main__':
    test_connection()