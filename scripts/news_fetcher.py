#!/usr/bin/env python3
"""
News Fetcher - Layer 2: Intelligence Gathering
Multi-source news search with full article extraction
"""

import os
import re
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

try:
    from duckduckgo_search import DDGS
except ImportError:
    print("Install: pip install duckduckgo-search")
    exit(1)

try:
    import trafilatura
except ImportError:
    print("Install: pip install trafilatura")
    exit(1)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class NewsFetcher:
    """
    Fetches and processes news for Polymarket markets.
    
    Flow per market:
    1. Generate multiple search queries (multi-angle)
    2. Search DuckDuckGo → collect URLs
    3. Filter & deduplicate
    4. Extract full article text via trafilatura
    5. Score by recency & source diversity
    6. Save to signals table
    """

    def __init__(self):
        self.max_queries_per_market = 3
        self.max_results_per_query = 5
        self.max_articles_to_fetch = 6
        self.seen_urls = set()
        self.seen_domains = {}

    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'news_fetcher', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    # =========================================================
    # STEP 1: Generate Search Queries (Multi-Angle)
    # =========================================================
    def generate_queries(self, question: str) -> list:
        """
        Generate multiple search queries from market question.
        Different angles for diverse coverage.
        """
        # Clean question
        q = question.strip().rstrip('?').strip()
        
        # Remove common Polymarket prefixes
        q = re.sub(r'^Will\s+', '', q, flags=re.IGNORECASE)
        q = re.sub(r'^Does\s+', '', q, flags=re.IGNORECASE)
        q = re.sub(r'^Is\s+', '', q, flags=re.IGNORECASE)
        q = re.sub(r'^Has\s+', '', q, flags=re.IGNORECASE)
        
        # Extract key entities/topics
        # Remove filler words for core topic
        core = re.sub(r'\b(the|a|an|by|in|on|at|to|for|of|with|and|or|this|that|before|after)\b', ' ', q, flags=re.IGNORECASE)
        core = ' '.join(core.split())  # Clean whitespace
        
        queries = []
        
        # Query 1: Direct question as search
        queries.append(f"{q} latest news 2026")
        
        # Query 2: Core topic + update
        queries.append(f"{core} update today")
        
        # Query 3: Analysis angle
        queries.append(f"{core} analysis prediction")
        
        return queries[:self.max_queries_per_market]

    # =========================================================
    # STEP 2: Search DuckDuckGo
    # =========================================================
    def search_news(self, queries: list) -> list:
        """
        Search DuckDuckGo with multiple queries.
        Returns deduplicated list of results.
        """
        all_results = []
        seen_urls = set()

        for query in queries:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.news(
                        keywords=query,
                        max_results=self.max_results_per_query,
                        region='wt-wt',       # Worldwide
                        safesearch='off'
                    ))

                    for r in results:
                        url = r.get('url', '')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append({
                                'title': r.get('title', ''),
                                'url': url,
                                'snippet': r.get('body', ''),
                                'source': r.get('source', ''),
                                'date': r.get('date', ''),
                                'query': query
                            })

            except Exception as e:
                self._log('WARN', f'Search failed for "{query}": {e}')
                continue

        return all_results

    # =========================================================
    # STEP 3: Filter & Score Results
    # =========================================================
    def filter_and_score(self, results: list) -> list:
        """
        Score and filter results by:
        - Recency (newer = higher score)
        - Source diversity (penalize same domain)
        - Relevance (snippet length as proxy)
        """
        domain_count = {}
        scored = []

        for r in results:
            score = 0.0
            url = r.get('url', '')

            # Extract domain
            domain = ''
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('www.', '')
            except:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else ''

            r['domain'] = domain

            # Recency score (0-40 points)
            date_str = r.get('date', '')
            if date_str:
                try:
                    # Try parse various date formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%a, %d %b %Y %H:%M:%S']:
                        try:
                            article_date = datetime.strptime(date_str[:19], fmt)
                            break
                        except:
                            continue
                    else:
                        article_date = None

                    if article_date:
                        age_hours = (datetime.now() - article_date).total_seconds() / 3600
                        if age_hours < 6:
                            score += 40
                        elif age_hours < 24:
                            score += 30
                        elif age_hours < 72:
                            score += 15
                        else:
                            score += 5
                        r['age_hours'] = round(age_hours, 1)
                except:
                    score += 10  # Unknown date, give average

            # Source diversity score (0-30 points)
            domain_count[domain] = domain_count.get(domain, 0) + 1
            if domain_count[domain] == 1:
                score += 30  # First from this domain
            elif domain_count[domain] == 2:
                score += 10  # Second from same domain
            else:
                score += 0   # Third+ from same domain, penalize

            # Trusted source bonus (0-20 points)
            trusted = ['reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk',
                       'bloomberg.com', 'nytimes.com', 'washingtonpost.com',
                       'theguardian.com', 'economist.com', 'ft.com',
                       'cnbc.com', 'wsj.com', 'politico.com', 'axios.com']
            if any(t in domain for t in trusted):
                score += 20

            # Snippet quality (0-10 points)
            snippet_len = len(r.get('snippet', ''))
            if snippet_len > 100:
                score += 10
            elif snippet_len > 50:
                score += 5

            r['score'] = score
            scored.append(r)

        # Sort by score descending
        scored.sort(key=lambda x: x['score'], reverse=True)

        return scored[:self.max_articles_to_fetch]

    # =========================================================
    # STEP 4: Extract Full Article Text
    # =========================================================
    def extract_article(self, url: str) -> dict:
        """
        Extract full article text from URL using trafilatura.
        Returns cleaned text, title, date.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None

            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
                favor_recall=True
            )

            if not text or len(text) < 100:
                return None

            # Also extract metadata
            metadata = trafilatura.extract(
                downloaded,
                output_format='json',
                include_comments=False,
                include_tables=False
            )

            meta = {}
            if metadata:
                try:
                    meta = json.loads(metadata)
                except:
                    pass

            return {
                'text': text,
                'title': meta.get('title', ''),
                'author': meta.get('author', ''),
                'date': meta.get('date', ''),
                'sitename': meta.get('sitename', ''),
                'word_count': len(text.split())
            }

        except Exception as e:
            return None

    # =========================================================
    # STEP 5: Save to Database
    # =========================================================
    def save_signals(self, market_id: int, articles: list):
        """Save fetched articles as signals in database"""
        conn = self._get_db()
        cursor = conn.cursor()

        saved = 0
        for article in articles:
            # Create unique hash to avoid duplicates
            url_hash = hashlib.md5(article.get('url', '').encode()).hexdigest()

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO signals (
                        market_id, source_type, source_name, title,
                        content, url, score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    market_id,
                    'news',
                    article.get('domain', article.get('source', '')),
                    article.get('title', ''),
                    article.get('full_text', article.get('snippet', '')),
                    article.get('url', ''),
                    article.get('score', 0)
                ))
                saved += 1
            except Exception as e:
                pass

        conn.commit()
        conn.close()
        return saved

    # =========================================================
    # MASTER: Fetch News for a Market
    # =========================================================
    def fetch_for_market(self, market_id: int, question: str) -> dict:
        """
        Complete pipeline: search → filter → extract → save
        
        Returns dict with articles and stats
        """
        self._log('INFO', f'Fetching news for: {question[:50]}...')

        # Step 1: Generate queries
        queries = self.generate_queries(question)
        self._log('INFO', f'  Queries: {queries}')

        # Step 2: Search
        results = self.search_news(queries)
        self._log('INFO', f'  Search results: {len(results)}')

        if not results:
            return {'articles': [], 'stats': {'searched': 0, 'fetched': 0, 'saved': 0}}

        # Step 3: Filter & score
        top_results = self.filter_and_score(results)
        self._log('INFO', f'  After filtering: {len(top_results)}')

        # Step 4: Extract full text
        articles_with_text = []
        for r in top_results:
            self._log('INFO', f'  Extracting: {r["domain"]}...')
            article = self.extract_article(r['url'])

            if article:
                r['full_text'] = article['text']
                r['word_count'] = article['word_count']
                r['extracted'] = True
                articles_with_text.append(r)
            else:
                # Keep snippet as fallback
                r['full_text'] = r.get('snippet', '')
                r['word_count'] = len(r.get('snippet', '').split())
                r['extracted'] = False
                articles_with_text.append(r)

        # Step 5: Save
        saved = self.save_signals(market_id, articles_with_text)
        self._log('INFO', f'  Saved {saved} signals to database')

        return {
            'articles': articles_with_text,
            'stats': {
                'queries': len(queries),
                'searched': len(results),
                'filtered': len(top_results),
                'extracted': sum(1 for a in articles_with_text if a.get('extracted')),
                'saved': saved
            }
        }

    # =========================================================
    # BATCH: Fetch News for Top Markets
    # =========================================================
    def fetch_for_top_markets(self, limit: int = 10, cooldown_hours: int = 4) -> dict:
        """
        Fetch news for top markets by volume.
        Skips markets that already have fresh news (within cooldown_hours).
        """
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT m.id, m.question, m.volume_24h, m.slug,
                   (SELECT MAX(s.timestamp) FROM signals s 
                    WHERE s.market_id = m.id
                   ) as last_news
            FROM markets m
            WHERE m.active = 1 AND m.closed = 0
            ORDER BY m.volume_24h DESC
            LIMIT ?
        ''', (limit,))

        markets = cursor.fetchall()
        conn.close()

        # Filter out markets with fresh news
        to_fetch = []
        skipped = 0
        for market_id, question, volume, slug, last_news in markets:
            if last_news:
                try:
                    last_dt = datetime.fromisoformat(last_news)
                    hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                    if hours_ago < cooldown_hours:
                        self._log('INFO', f'Skipping news (fresh {hours_ago:.1f}h ago): {question[:50]}...')
                        skipped += 1
                        continue
                except (ValueError, TypeError):
                    pass

            to_fetch.append((market_id, question, volume, slug))

        self._log('INFO', f'Fetching news for {len(to_fetch)} markets ({skipped} skipped, cooldown={cooldown_hours}h)')

        all_stats = []
        for market_id, question, volume, slug in to_fetch:
            result = self.fetch_for_market(market_id, question)
            all_stats.append({
                'market_id': market_id,
                'question': question[:50],
                'volume_24h': volume,
                **result['stats']
            })

            # Rate limit: pause between markets
            import time
            time.sleep(2)

        total_articles = sum(s['saved'] for s in all_stats)
        self._log('INFO', f'Total: {total_articles} articles saved for {len(to_fetch)} markets')

        return {
            'markets_processed': len(to_fetch),
            'markets_skipped': skipped,
            'total_articles': total_articles,
            'details': all_stats
        }


# =========================================================
# CLI
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("📰 Polymarket News Fetcher")
    print("=" * 60)
    print()

    fetcher = NewsFetcher()

    # Test with top 5 markets
    results = fetcher.fetch_for_top_markets(limit=5)

    print()
    print("=" * 60)
    print("📋 RESULTS")
    print("=" * 60)
    print(f"Markets processed: {results['markets_processed']}")
    print(f"Total articles: {results['total_articles']}")
    print()

    for s in results['details']:
        print(f"  {s['question']}...")
        print(f"    Searched: {s['searched']} | Extracted: {s['extracted']} | Saved: {s['saved']}")
        print()