#!/usr/bin/env python3
"""
Market Categorizer - Detect category from market question
Categories: crypto, sports, politics, entertainment, science, economics, other
"""

import re


class MarketCategorizer:
    
    def __init__(self):
        # Keywords untuk setiap category
        self.categories = {
            'crypto': [
                'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'crypto',
                'token', 'coin', 'defi', 'nft', 'blockchain', 'binance', 'coinbase',
                'memecoin', 'dogecoin', 'doge', 'xrp', 'ripple', 'cardano', 'ada',
                'polygon', 'matic', 'avalanche', 'avax', 'chainlink', 'link',
                'uniswap', 'aave', 'maker', 'dao', 'web3', 'satoshi', 'halving',
                'stablecoin', 'usdt', 'usdc', 'tether', 'market cap'
            ],
            'sports': [
                'nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball',
                'baseball', 'hockey', 'tennis', 'golf', 'ufc', 'mma', 'boxing',
                'f1', 'formula 1', 'nascar', 'olympics', 'world cup', 'super bowl',
                'championship', 'playoff', 'finals', 'mvp', 'win the', 'beat',
                'lakers', 'celtics', 'warriors', 'chiefs', 'eagles', 'cowboys',
                'yankees', 'dodgers', 'premier league', 'la liga', 'champions league',
                'manchester', 'liverpool', 'arsenal', 'chelsea', 'real madrid',
                'barcelona', 'psg', 'serie a', 'bundesliga', 'tottenham', 'spurs'
            ],
            'politics': [
                'trump', 'biden', 'president', 'election', 'vote', 'congress',
                'senate', 'house', 'republican', 'democrat', 'gop', 'primary',
                'governor', 'mayor', 'political', 'legislation', 'bill', 'law',
                'executive order', 'impeach', 'supreme court', 'scotus', 'cabinet',
                'secretary', 'administration', 'white house', 'poll', 'approval',
                'parliamentary', 'prime minister', 'brexit', 'eu', 'nato', 'un',
                'sanctions', 'tariff', 'immigration', 'border', 'policy'
            ],
            'economics': [
                'fed', 'federal reserve', 'interest rate', 'inflation', 'cpi',
                'gdp', 'recession', 'unemployment', 'jobs report', 'fomc',
                'treasury', 'bond', 'yield', 'stock market', 's&p', 'dow jones',
                'nasdaq', 'ipo', 'earnings', 'revenue', 'profit', 'merger',
                'acquisition', 'bankruptcy', 'default', 'debt ceiling', 'stimulus',
                'quantitative easing', 'rate cut', 'rate hike', 'economic',
                'oil price', 'gold price', 'commodity', 'trade', 'export', 'import'
            ],
            'entertainment': [
                'oscar', 'emmy', 'grammy', 'golden globe', 'movie', 'film',
                'box office', 'netflix', 'disney', 'hbo', 'streaming', 'album',
                'song', 'artist', 'concert', 'tour', 'celebrity', 'kardashian',
                'taylor swift', 'beyonce', 'drake', 'kanye', 'elon musk', 'twitter',
                'x.com', 'meta', 'facebook', 'instagram', 'tiktok', 'youtube',
                'viral', 'influencer', 'podcast', 'joe rogan', 'tv show', 'series'
            ],
            'science': [
                'nasa', 'spacex', 'rocket', 'launch', 'moon', 'mars', 'asteroid',
                'satellite', 'space', 'orbit', 'ai', 'artificial intelligence',
                'gpt', 'openai', 'anthropic', 'google ai', 'deepmind', 'chatgpt',
                'climate', 'temperature', 'carbon', 'emission', 'renewable',
                'solar', 'nuclear', 'fusion', 'quantum', 'breakthrough', 'fda',
                'vaccine', 'drug', 'trial', 'cure', 'disease', 'pandemic', 'virus'
            ]
        }
    
    def categorize(self, question: str, description: str = "") -> str:
        """
        Categorize a market based on question and description.
        Returns: category string
        """
        text = f"{question} {description}".lower()
        
        scores = {}
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # Exact word match gets higher score
                    if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                        score += 2
                    else:
                        score += 1
            scores[category] = score
        
        # Get category with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return 'other'
    
    def categorize_batch(self, markets: list) -> dict:
        """
        Categorize multiple markets.
        Input: list of dicts with 'question' and optionally 'description'
        Output: dict of {market_id: category}
        """
        results = {}
        for market in markets:
            market_id = market.get('id') or market.get('market_id')
            question = market.get('question', '')
            description = market.get('description', '')
            results[market_id] = self.categorize(question, description)
        return results


# Test
if __name__ == "__main__":
    categorizer = MarketCategorizer()
    
    test_questions = [
        "Will Bitcoin hit $100k by March 2026?",
        "Will the Lakers win the NBA Championship?",
        "Will Trump win the 2028 election?",
        "Will the Fed cut interest rates in March?",
        "Will SpaceX land humans on Mars by 2030?",
        "Will Taylor Swift's album go platinum?",
        "Will it rain tomorrow in New York?",
        "Will Ethereum flip Bitcoin in market cap?",
        "Will Manchester United win the Premier League?",
        "Will Congress pass the immigration bill?"
    ]
    
    print("Market Categorization Test:")
    print("=" * 60)
    for q in test_questions:
        cat = categorizer.categorize(q)
        print(f"[{cat:12}] {q}")
