#!/usr/bin/env python3
"""
AI Brain - Layer 3: LLM Analysis Engine
Two-stage analysis: Fact Extraction → Probability Assessment
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from whale_tracker import WhaleTracker, get_market_tokens
from sports_data import SportsData
from agent_config_loader import get_agent_config

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class AIBrain:
    """
    Two-stage LLM analysis per market:
    
    Stage 1 (Cheap - Haiku): Extract key facts from articles
        Input: raw article texts
        Output: list of unique, relevant facts
    
    Stage 2 (Smart - Sonnet): Probability assessment
        Input: market data + extracted facts
        Output: probability, confidence, reasoning, recommendation
    """

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in config/.env")
        
        # Model selection
        self.model_cheap = "anthropic/claude-3.5-haiku"     # Fast & cheap for fact extraction
        self.model_smart = "anthropic/claude-sonnet-4.5"  # Smart for analysis
        
        # Token limits
        self.max_article_tokens = 3000   # Per article, truncate if longer
        self.max_facts_tokens = 2000     # Facts summary sent to Stage 2
        self.whale_tracker = WhaleTracker()
        self.sports_data = SportsData()
        self.agent_config = get_agent_config()  # Self-improvement config

    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def _is_market_still_open(self, end_date_str: str) -> bool:
        """
        Check if market is still open for trading.
        Returns False if market has already closed.
        Provides 2-hour buffer to avoid analyzing markets about to close.
        """
        if not end_date_str or end_date_str == 'Unknown':
            return True  # Unknown end date, assume open
        
        try:
            # Parse end date (format: 2026-02-02T17:00:00Z)
            end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # Market must close at least 2 hours from now
            buffer_time = now + timedelta(hours=2)
            
            if end_dt <= now:
                return False  # Market already closed
            elif end_dt <= buffer_time:
                return False  # Market closes too soon (within 2 hours)
            else:
                return True  # Market still open with enough time
        except Exception as e:
            self._log('WARN', f'Failed to parse end_date "{end_date_str}": {e}')
            return True  # If parsing fails, don't skip (cautious approach)

    def _parse_resolution_criteria(self, description: str, question: str) -> dict:
        """
        Extract and highlight key resolution criteria from market description.
        Returns structured resolution info to make criteria crystal clear to AI.
        """
        if not description or description.strip() == '':
            return {
                'has_criteria': False,
                'summary': 'No explicit resolution criteria provided. Assess based on question wording.',
                'key_points': [],
                'resolution_source': 'Unknown',
                'special_cases': []
            }
        
        criteria = {
            'has_criteria': True,
            'summary': '',
            'key_points': [],
            'resolution_source': 'Unknown',
            'special_cases': []
        }
        
        desc_lower = description.lower()
        
        # Extract resolution source
        source_patterns = [
            r'resolution source[:\s]+([^.]+)',
            r'will resolve based on[:\s]+([^.]+)',
            r'official.*?from[:\s]+([^.]+)',
            r'according to[:\s]+([^.]+)',
        ]
        import re
        for pattern in source_patterns:
            match = re.search(pattern, desc_lower)
            if match:
                criteria['resolution_source'] = match.group(1).strip()
                break
        
        # Extract key phrases that define resolution
        key_phrases = []
        
        # "Will resolve to X if Y"
        resolve_if = re.findall(r'will resolve to ["\']?(\w+)["\']? if ([^.]+)', desc_lower)
        for outcome, condition in resolve_if:
            key_phrases.append(f"Resolves {outcome.upper()} if: {condition.strip()}")
        
        # "This market will resolve to..."
        resolve_to = re.findall(r'this market will resolve to[:\s]+([^.]+)', desc_lower)
        for resolution in resolve_to:
            key_phrases.append(f"Resolution: {resolution.strip()}")
        
        # Extract time ranges / measurement periods
        time_patterns = [
            r'from ([^to]+) to ([^.,]+)',
            r'between ([^and]+) and ([^.,]+)',
            r'during ([^.,]+)',
            r'by ([^.,]+)',
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, desc_lower)
            for match in matches:
                if isinstance(match, tuple):
                    time_info = ' to '.join(match)
                else:
                    time_info = match
                key_phrases.append(f"Time period: {time_info.strip()}")
        
        # Extract thresholds / numeric criteria
        threshold_patterns = [
            r'(\d+[+\-]?\s*(?:bps|basis points|percent|%|points|wins|goals))',
            r'(?:above|below|over|under|at least|more than|less than)\s+[\$€£]?(\d+[,\d]*(?:\.\d+)?[KMB]?)',
        ]
        for pattern in threshold_patterns:
            matches = re.findall(pattern, desc_lower)
            for threshold in matches:
                key_phrases.append(f"Threshold: {threshold}")
        
        # Detect special resolution cases
        special_keywords = [
            ('cancel', 'Market may resolve "Other" if event is canceled'),
            ('mathematically eliminated', 'Resolves NO if mathematically eliminated'),
            ('rounded', 'Values will be rounded before resolution'),
            ('earliest', 'Resolves based on earliest occurrence'),
            ('official', 'Requires official confirmation'),
        ]
        for keyword, explanation in special_keywords:
            if keyword in desc_lower:
                criteria['special_cases'].append(explanation)
        
        criteria['key_points'] = key_phrases[:5]  # Top 5 most important
        
        # Generate summary
        if key_phrases:
            criteria['summary'] = f"RESOLUTION CRITERIA: {'; '.join(key_phrases[:3])}"
        else:
            # Fallback: use first 200 chars of description
            criteria['summary'] = f"RESOLUTION: {description[:200].strip()}..."
        
        return criteria

    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'ai_brain', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    # =========================================================
    # OpenRouter API Call
    # =========================================================
    def _call_llm(self, model: str, system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
        """
        Call OpenRouter API
        Returns response text or None on failure
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://polymarket-intel.app",
            "X-Title": "Polymarket Intelligence System"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3  # Low temp for factual analysis
        }

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                self._log('ERROR', f'OpenRouter API error {response.status_code}: {response.text[:200]}')
                return None

            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Log usage
            usage = data.get('usage', {})
            self._log('INFO', f'  LLM [{model.split("/")[-1]}] tokens: {usage.get("prompt_tokens", 0)} in / {usage.get("completion_tokens", 0)} out')
            
            return content

        except Exception as e:
            self._log('ERROR', f'LLM call failed: {e}')
            return None

    # =========================================================
    # STAGE 1: Extract Key Facts (Cheap Model)
    # =========================================================
    def extract_facts(self, question: str, articles: list) -> str:
        """
        Stage 1: Use cheap model to extract key facts from articles.
        
        Input: market question + list of article texts
        Output: structured list of key facts
        """
        self._log('INFO', f'  Stage 1: Extracting facts...')

        # Build article text block (truncate each article)
        article_block = ""
        for i, article in enumerate(articles):
            title = article.get('title', 'Unknown')
            source = article.get('domain', article.get('source', 'Unknown'))
            text = article.get('full_text', article.get('snippet', ''))
            date = article.get('date', 'Unknown date')
            
            # Truncate long articles (~3000 chars ≈ 750 tokens)
            if len(text) > 3000:
                text = text[:3000] + "... [truncated]"
            
            article_block += f"\n--- ARTICLE {i+1} [{source}] ({date}) ---\n"
            article_block += f"Title: {title}\n"
            article_block += f"{text}\n"

        system_prompt = """You are a fact extraction engine for prediction market analysis.
Your job is to extract ONLY factual, verifiable information from news articles.
Do NOT include opinions, predictions, or speculation.
Focus on: dates, numbers, quotes from officials, confirmed events, official statements, voting results, deadlines.
Output as a numbered list of facts. Be concise - one fact per line.
Maximum 20 facts. Deduplicate - don't repeat the same fact from different sources."""

        user_prompt = f"""PREDICTION MARKET QUESTION: {question}

ARTICLES:
{article_block}

Extract the key facts relevant to answering this prediction market question.
Focus on facts that help determine the probability of this event happening.
Include the source for each fact."""

        response = self._call_llm(self.model_cheap, system_prompt, user_prompt, max_tokens=1000)
        
        if not response:
            self._log('WARN', '  Stage 1 failed - no response from LLM')
            # Fallback: use article snippets as facts
            fallback = "\n".join([
                f"- {a.get('title', '')} ({a.get('domain', '')}): {a.get('snippet', '')[:200]}"
                for a in articles[:5]
            ])
            return fallback
        
        return response

    # =========================================================
    # STAGE 2: Probability Assessment (Smart Model)
    # =========================================================
    def assess_probability(self, question: str, facts: str, market_data: dict, whale_text: str = "", sports_text: str = "") -> dict:
        """
        Stage 2: Use smart model to assess probability.
        Now includes on-chain whale intelligence, resolution rules, and live sports data.
        """
        self._log('INFO', f'  Stage 2: Assessing probability...')
        
        # VALIDATION 1: Check if market is still open
        end_date = market_data.get('end_date', 'Unknown')
        if not self._is_market_still_open(end_date):
            self._log('WARN', f'  Market already closed or closes too soon (end_date: {end_date}). Skipping analysis.')
            return {
                'probability': market_data.get('yes_price', 0.5),
                'confidence': 'SKIP',
                'reasoning': f'Market end date ({end_date}) has already passed or is within 2 hours. Cannot analyze closed markets.',
                'recommendation': 'SKIP',
                'key_factors_for': [],
                'key_factors_against': [],
                'risks': 'N/A - Market closed',
                'edge_assessment': 'N/A - Market closed',
                'whale_interpretation': 'N/A - Market closed'
            }
        
        # VALIDATION 2: Check if market has enough time (>24h)
        # Short-term markets (<24h) are too volatile and unpredictable
        if end_date and end_date != 'Unknown':
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                hours_remaining = (end_dt - now).total_seconds() / 3600
                
                if hours_remaining < 24:
                    self._log('WARN', f'  Market closes in {hours_remaining:.1f}h (<24h). Skipping short-term prediction.')
                    return {
                        'probability': market_data.get('yes_price', 0.5),
                        'confidence': 'SKIP',
                        'reasoning': f'Market closes in {hours_remaining:.1f} hours. Short-term markets (<24h) are too unpredictable for reliable analysis.',
                        'recommendation': 'SKIP',
                        'key_factors_for': [],
                        'key_factors_against': [],
                        'risks': 'N/A - Short-term market',
                        'edge_assessment': 'N/A - Insufficient timeframe',
                        'whale_interpretation': 'N/A - Short-term market'
                    }
            except Exception as e:
                self._log('WARN', f'Failed to check timeframe: {e}')
        
        # VALIDATION 3: Check liquidity threshold
        # Low liquidity markets are easily manipulated
        liquidity_threshold = 10000  # $10K minimum
        liquidity_val = market_data.get('liquidity', 0)
        
        if liquidity_val < liquidity_threshold:
            self._log('WARN', f'  Market liquidity ${liquidity_val:,.0f} below threshold ${liquidity_threshold:,.0f}. Skipping.')
            return {
                'probability': market_data.get('yes_price', 0.5),
                'confidence': 'SKIP',
                'reasoning': f'Market liquidity (${liquidity_val:,.0f}) is too low. Thin markets below ${liquidity_threshold:,.0f} are easily manipulated and unreliable.',
                'recommendation': 'SKIP',
                'key_factors_for': [],
                'key_factors_against': [],
                'risks': 'N/A - Low liquidity',
                'edge_assessment': 'N/A - Thin market',
                'whale_interpretation': 'N/A - Low liquidity'
            }

        # Market context
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        volume = market_data.get('volume_24h', 0)
        liquidity = market_data.get('liquidity', 0)
        end_date = market_data.get('end_date', 'Unknown')
        resolution_rules = market_data.get('description', '')
        
        # Parse resolution criteria for clarity
        resolution_info = self._parse_resolution_criteria(resolution_rules, question)
        
        # Detect market category for specialized handling
        question_lower = question.lower()
        is_crypto = any(word in question_lower for word in ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'solana', 'sol'])
        is_sports = any(word in question_lower for word in ['win', 'league', 'championship', 'match', 'game', 'score', 'nfl', 'nba', 'epl'])
        is_political = any(word in question_lower for word in ['president', 'election', 'government', 'congress', 'senate', 'fed', 'shutdown'])
        
        # Current time context (CRITICAL for timestamp awareness)
        current_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        
        # Get lessons learned from self-improvement config
        lessons_section = ""
        if hasattr(self, 'agent_config'):
            lessons_section = self.agent_config.get_lessons_for_prompt()

        system_prompt = f"""You are Oracle Sentinel, an elite prediction market analyst.
CURRENT TIME: {current_time_utc}
CRITICAL: If the market's end date has already passed, or if the event in question has already occurred based on the current time, you MUST output recommendation: "SKIP" with reasoning explaining the market is already closed or resolved.
You assess the probability of events based on factual evidence AND on-chain market intelligence.

RULES:
1. Base your probability on the provided facts AND whale/on-chain signals
2. Be calibrated - don't be overconfident. Consider tail risks and surprises
3. If facts are insufficient, lower your confidence, don't guess
4. Consider: base rates, track record of similar events, incentives of key actors
5. Account for the difference between "likely" and "certain"
5a. RESPECT MARKET PRICE AS BASELINE: The market price reflects thousands of bettors with real money at stake. Your probability should START from the market price and ADJUST based on your evidence. A deviation of >15% from market price requires VERY strong, specific evidence. If you cannot improve on the market price, output a probability close to it.
5b. AVOID DEFAULT PROBABILITIES: Never output 0.35 or 0.50 as a lazy default. Always reason from specific evidence. If unsure, your probability should be close to the market price, not an arbitrary round number.
6. Whale signals provide ADDITIONAL context:
   - BULLISH whale + supporting news = higher confidence in YES
   - BEARISH whale + contradicting news = lower confidence in YES
   - Whale signals contradicting news = lower overall confidence
   - No whale signals = rely more on news analysis
7. SPORTS DATA provides REAL-TIME intelligence:
   - League standings show current position and points gap to leader
   - Recent form (last 10 matches) reveals momentum and consistency
   - Betting streaks show patterns (goals, clean sheets, etc)
   - Fan predictions show crowd sentiment
   - Previous match stats reveal playing style (possession, shots, xG)
   - Use ALL sports data to calibrate probability — don't rely on reputation alone

SPORTS MARKET CALIBRATION (CRITICAL):
- Season winner markets: Position gap to leader matters hugely. 10+ pts gap = very unlikely
- A team on bad form (3+ losses in 5) is less likely regardless of reputation
- Fan predictions with 30K+ votes are meaningful crowd signals
- Pre-match ratings below 6.5 indicate poor recent performance
- Over 2.5 goals streaks affect match outcome analysis
- NFL/NBA: Win-loss record is the primary indicator

POLITICAL EVENT CALIBRATION (CRITICAL):
- Politicians often delay, extend deadlines, or find last-minute compromises
- Government shutdowns usually get resolved with temporary measures
- "Will X happen by date Y" → Consider historical patterns of delays
- Announced intentions ≠ actual outcomes
- Political brinkmanship often goes to the wire then resolves
- When in doubt about political timing, lean toward MEDIUM confidence, not HIGH

CRYPTO/BITCOIN MARKET CALIBRATION (CRITICAL):
- Bitcoin can swing 5-10% in a single day (high volatility asset)
- Short-term price predictions (<48h) are extremely difficult
- "Bitcoin above $X" → Consider recent 24h volatility, not just current price
- Crypto markets operate 24/7, price can move dramatically overnight
- Sentiment shifts rapidly with news (Fed policy, institutional buying, regulatory changes)
- Don't be overconfident on small percentage moves (1-3%) in short timeframes
- Historical volatility: BTC averages 3-5% daily swings in normal conditions, 10%+ in volatile periods

MARKET PRICE ZONES:
- Price 45-55%: This is a coin-flip. Unless you have VERY strong evidence, confidence should be MEDIUM at best
- Price >90% or <10%: Near-resolved. Small remaining probability is usually real tail risk
- Respect market wisdom - large liquid markets are often efficient

RECOMMENDATION RULES:
- BUY_YES: Your probability is HIGHER than market price by 5%+ AND you have HIGH confidence
- BUY_NO: Your probability is LOWER than market price by 5%+ AND you have HIGH confidence
- NO_TRADE: Edge is less than 5%, OR confidence is not HIGH
- SKIP: Insufficient data to form a reliable estimate

CONFIDENCE GUIDE:
- HIGH: Multiple confirming sources, clear factual basis, no major unknowns
- MEDIUM: Some supporting evidence but significant uncertainty remains
- LOW: Mostly speculation, conflicting information, or insufficient data

Example: Market YES=$0.60, your estimate=0.75, HIGH confidence → edge +15% → BUY_YES
Example: Market YES=$0.80, your estimate=0.50, HIGH confidence → edge -30% → BUY_NO
Example: Market YES=$0.60, your estimate=0.68, MEDIUM confidence → edge +8% → NO_TRADE (need HIGH confidence)
Example: Market YES=$0.50, your estimate=0.65 → coin-flip zone → NO_TRADE

{lessons_section}

You MUST respond in EXACTLY this JSON format and nothing else:
{{
    "probability": 0.XX,
    "confidence": "LOW|MEDIUM|HIGH",
    "reasoning": "2-3 sentence explanation of your assessment",
    "key_factors_for": ["factor supporting YES", "factor 2"],
    "key_factors_against": ["factor supporting NO", "factor 2"],
    "risks": "What could make this assessment wrong?",
    "recommendation": "BUY_YES|BUY_NO|NO_TRADE|SKIP",
    "edge_assessment": "Is there an edge vs market price? Explain.",
    "whale_interpretation": "How do on-chain signals align with your analysis?"
}}"""

        # Build whale section
        whale_section = ""
        if whale_text and "No significant whale activity" not in whale_text:
            whale_section = f"\n{whale_text}\n"

        # Build resolution rules section with parsed criteria
        rules_section = ""
        if resolution_info['has_criteria']:
            criteria_bullets = '\n'.join([f"  • {point}" for point in resolution_info['key_points']])
            special_cases = '\n'.join([f"  ⚠️ {case}" for case in resolution_info['special_cases']]) if resolution_info['special_cases'] else ''
            
            rules_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ RESOLUTION CRITERIA (CRITICAL - READ FIRST) ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 SUMMARY: {resolution_info['summary']}

🔑 KEY RESOLUTION POINTS:
{criteria_bullets}

📊 RESOLUTION SOURCE: {resolution_info['resolution_source']}

{special_cases}

⚠️ YOUR PROBABILITY MUST BE BASED ON THESE EXACT CRITERIA, NOT THE QUESTION TITLE ALONE.

FULL RESOLUTION RULES:
{resolution_rules}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            # Fallback if no criteria parsed
            rules_section = f"""
RESOLUTION RULES:
{resolution_info['summary']}
"""

        # Build sports section
        sports_section = ""
        if sports_text:
            sports_section = f"\n{sports_text}\n"

        # Add category-specific context
        category_context = ""
        if is_crypto:
            category_context = "\n🔶 CRYPTO MARKET DETECTED: Remember Bitcoin/crypto volatility is HIGH. Small percentage moves can happen in hours. Don't underestimate short-term price swings.\n"
        elif is_sports:
            category_context = "\n⚽ SPORTS MARKET DETECTED: Focus on recent form, league standings, and live match statistics over reputation.\n"
        elif is_political:
            category_context = "\n🏛️ POLITICAL MARKET DETECTED: Politicians often delay. Consider base rates of similar events, not just announcements.\n"
        
        user_prompt = f"""PREDICTION MARKET ANALYSIS

QUESTION: {question}
{category_context}
CURRENT MARKET DATA:
- YES price: ${yes_price} (market implies {yes_price*100:.1f}% probability)
- NO price: ${no_price}
- 24h Volume: ${volume:,.0f}
- Liquidity: ${liquidity:,.0f}
- End date: {end_date}
{rules_section}
EXTRACTED FACTS:
{facts}
{whale_section}{sports_section}
Based on the RESOLUTION RULES, facts, on-chain whale intelligence, AND live sports data, what is the TRUE probability?
IMPORTANT: Your probability assessment MUST be based on the exact resolution criteria above, not general assumptions about the question.
Compare your assessment with the current market price.

Respond ONLY with the JSON object, no other text."""

        response = self._call_llm(self.model_smart, system_prompt, user_prompt, max_tokens=1500)
        
        if not response:
            self._log('WARN', '  Stage 2 failed - no response from LLM')
            return self._default_assessment(yes_price)

        # Parse JSON response
        try:
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[1]  # Remove first line
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
                elif '```' in cleaned:
                    cleaned = cleaned[:cleaned.rfind('```')]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            
            # Validate required fields
            required = ['probability', 'confidence', 'reasoning', 'recommendation']
            for field in required:
                if field not in result:
                    result[field] = self._default_assessment(yes_price).get(field)
            
            # Ensure probability is float between 0 and 1
            prob = float(result['probability'])
            result['probability'] = max(0.01, min(0.99, prob))
            
            # ==============================================
            # FORCE RECOMMENDATION RULES AT CODE LEVEL
            # Don't trust LLM's recommendation — recalculate
            # ==============================================
            # Detect category for self-improvement adjustments
            from market_categorizer import MarketCategorizer
            categorizer = MarketCategorizer()
            market_category = categorizer.categorize(question)
            
            result = self._force_recommendation(result, yes_price, category=market_category)
            
            return result

        except (json.JSONDecodeError, ValueError) as e:
            self._log('WARN', f'  Failed to parse LLM response: {e}')
            self._log('WARN', f'  Raw response: {response[:200]}')
            return self._default_assessment(yes_price)

    def _force_recommendation(self, result: dict, market_yes_price: float) -> dict:
        """
        Override LLM recommendation with hard-coded rules.
        This ensures consistent logic regardless of what the LLM outputs.
        
        Rules (evaluated in order):
        1. confidence LOW                            → SKIP
        2. market_price > 0.97 or < 0.03            → NO_TRADE (truly near-resolved)
        3. market_price 0.45-0.55 (coin-flip zone)  → NO_TRADE (too uncertain)
        4. edge >= +10% AND confidence HIGH          → BUY_YES
        5. edge <= -10% AND confidence HIGH          → BUY_NO
        6. edge >= +5% AND confidence HIGH           → BUY_YES
        7. edge <= -5% AND confidence HIGH           → BUY_NO
        8. abs(edge) < 5%                            → NO_TRADE
        9. confidence MEDIUM + edge >= 15%           → BUY (only very high edge)
        10. confidence MEDIUM + edge < 15%           → NO_TRADE
        """
        ai_prob = result.get('probability', 0)
        confidence = result.get('confidence', 'LOW')
        edge = (ai_prob - market_yes_price) * 100  # in percentage points

        llm_rec = result.get('recommendation', 'SKIP')
        new_rec = 'SKIP'  # default

        # Rule 1: Low confidence → always SKIP
        if confidence == 'LOW':
            new_rec = 'SKIP'

        # Rule 2: Near-resolved markets → NO_TRADE
        elif market_yes_price > 0.97 or market_yes_price < 0.03:
            new_rec = 'NO_TRADE'

        # Rule 3: Coin-flip zone (45-55%) → NO_TRADE
        elif 0.45 <= market_yes_price <= 0.55:
            new_rec = 'NO_TRADE'
            self._log('INFO', f'  ⚠️ Coin-flip zone ({market_yes_price*100:.1f}%) → NO_TRADE')

        # Rule 4-5: Big edge (>=10%) with HIGH confidence
        elif abs(edge) >= min_edge_threshold * 2 and confidence == 'HIGH':  # 2x threshold for high confidence
            new_rec = 'BUY_YES' if edge > 0 else 'BUY_NO'

        # Rule 6-7: Moderate edge (>=5%) with HIGH confidence only
        elif abs(edge) >= min_edge_threshold and confidence == 'HIGH':  # Dynamic threshold
            new_rec = 'BUY_YES' if edge > 0 else 'BUY_NO'

        # Rule 8: Small edge → not worth it
        elif abs(edge) < min_edge_threshold:  # Below dynamic threshold
            new_rec = 'NO_TRADE'

        # Rule 9-10: MEDIUM confidence → NO_TRADE always
        # MEDIUM confidence means significant uncertainty — not enough to bet
        elif confidence == 'MEDIUM':
            new_rec = 'NO_TRADE'

        # Default
        else:
            new_rec = 'NO_TRADE'

        # Log if we overrode the LLM
        if new_rec != llm_rec:
            self._log('INFO', f'  ⚡ Recommendation override: LLM said {llm_rec} → forced {new_rec} (edge={edge:+.1f}%, conf={confidence}, price={market_yes_price*100:.1f}%)')

        result['recommendation'] = new_rec
        result['llm_original_recommendation'] = llm_rec  # keep for debugging
        result['forced_edge'] = round(edge, 2)
        return result

    def _default_assessment(self, market_price: float) -> dict:
        """Fallback assessment when LLM fails"""
        return {
            'probability': market_price,
            'confidence': 'LOW',
            'reasoning': 'Unable to perform AI analysis. Using market price as estimate.',
            'key_factors_for': [],
            'key_factors_against': [],
            'risks': 'No AI analysis available.',
            'recommendation': 'SKIP',
            'edge_assessment': 'No edge detected - analysis failed.'
        }

    # =========================================================
    # GET ARTICLES FROM DATABASE
    # =========================================================
    def get_market_articles(self, market_id: int) -> list:
        """Get stored articles/signals for a market"""
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT source_name, title, content, url, score, timestamp
            FROM signals
            WHERE market_id = ?
            ORDER BY score DESC
            LIMIT 8
        ''', (market_id,))

        articles = []
        for row in cursor.fetchall():
            articles.append({
                'domain': row[0],
                'title': row[1],
                'full_text': row[2] or '',
                'url': row[3],
                'score': row[4],
                'date': row[5]
            })

        conn.close()
        return articles

    # =========================================================
    # GET MARKET DATA
    # =========================================================
    def get_market_data(self, market_id: int) -> dict:
        """Get market data + token prices from database"""
        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT m.question, m.slug, m.volume_24h, m.liquidity, 
                   m.end_date, m.volume, m.outcome_prices, m.outcomes, m.description
            FROM markets m
            WHERE m.id = ?
        ''', (market_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}

        question, slug, vol24h, liquidity, end_date, volume, raw_prices, raw_outcomes, description = row

        # Parse prices
        yes_price = 0
        no_price = 0
        try:
            prices = json.loads(raw_prices) if isinstance(raw_prices, str) else raw_prices
            if prices and len(prices) >= 2:
                yes_price = float(prices[0])
                no_price = float(prices[1])
        except:
            pass

        conn.close()

        return {
            'market_id': market_id,
            'question': question,
            'slug': slug,
            'volume_24h': vol24h or 0,
            'liquidity': liquidity or 0,
            'end_date': end_date or '',
            'total_volume': volume or 0,
            'yes_price': yes_price,
            'no_price': no_price,
            'description': description or ''
        }

    # =========================================================
    # SAVE AI ASSESSMENT
    # =========================================================
    def save_assessment(self, market_id: int, market_data: dict, assessment: dict) -> int:
        """Save AI assessment as opportunity in database"""
        conn = self._get_db()
        cursor = conn.cursor()

        ai_prob = assessment.get('probability', 0)
        market_prob = market_data.get('yes_price', 0)
        edge = round((ai_prob - market_prob) * 100, 2)
        
        # Confidence to number
        confidence_map = {'LOW': 0.3, 'MEDIUM': 0.6, 'HIGH': 0.9}
        confidence = confidence_map.get(assessment.get('confidence', 'LOW'), 0.3)

        # Determine type
        recommendation = assessment.get('recommendation', 'SKIP')
        if abs(edge) > 5 and confidence >= 0.6:
            opp_type = 'ai_high_edge'
        elif abs(edge) > 2:
            opp_type = 'ai_edge'
        else:
            opp_type = 'ai_no_edge'

        raw_data = json.dumps({
            **assessment,
            'market_question': market_data.get('question', ''),
            'market_yes_price': market_prob,
            'ai_probability': ai_prob,
            'edge_pct': edge,
            'analysis_timestamp': datetime.now().isoformat()
        })

        try:
            cursor.execute('''
                INSERT INTO opportunities (
                    market_id, type, ai_estimate, edge, confidence, raw_data, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                market_id, opp_type, ai_prob, abs(edge), confidence, raw_data, 'active'
            ))
            conn.commit()
            opp_id = cursor.lastrowid
        except Exception as e:
            self._log('ERROR', f'Failed to save assessment: {e}')
            opp_id = 0

        conn.close()
        return opp_id

    # =========================================================
    # MASTER: Analyze Single Market
    # =========================================================
    def analyze_market(self, market_id: int) -> dict:
        """
        Full analysis pipeline for one market:
        1. Get market data
        2. Get articles from DB
        3. Stage 1: Extract facts
        4. Stage 2: Assess probability
        5. Calculate edge
        6. Save to DB
        """
        self._log('INFO', f'Analyzing market ID: {market_id}')

        # Get market data
        market_data = self.get_market_data(market_id)
        if not market_data:
            self._log('ERROR', f'Market {market_id} not found')
            return {}

        question = market_data['question']
        self._log('INFO', f'  Market: {question[:50]}...')
        self._log('INFO', f'  Current price: YES=${market_data["yes_price"]}, NO=${market_data["no_price"]}')

        # Get articles
        articles = self.get_market_articles(market_id)
        self._log('INFO', f'  Articles in DB: {len(articles)}')

        if not articles:
            self._log('WARN', f'  No articles found - skipping AI analysis')
            return {
                'market_id': market_id,
                'question': question,
                'status': 'skipped',
                'reason': 'No articles available'
            }

        # Stage 1: Extract facts
        facts = self.extract_facts(question, articles)
        self._log('INFO', f'  Facts extracted: {len(facts.split(chr(10)))} lines')

        # Stage 1.5: Whale Intelligence
        whale_text = ""
        try:
            tokens = get_market_tokens(market_id)
            if tokens.get("token_id_yes") and tokens.get("token_id_no"):
                whale_data = self.whale_tracker.analyze_market_whales(
                    token_id_yes=tokens["token_id_yes"],
                    token_id_no=tokens["token_id_no"],
                    question=question,
                    condition_id=tokens.get("condition_id", ""),
                    current_volume=market_data.get("volume_24h", 0)
                )
                whale_text = self.whale_tracker.format_for_ai_prompt(whale_data)
                self._log('INFO', f'  Whale signals: {whale_data.get("signal_count", 0)}, sentiment: {whale_data.get("overall_sentiment", "NEUTRAL")}')
            else:
                self._log('WARN', '  No token IDs — skipping whale analysis')
        except Exception as e:
            self._log('WARN', f'  Whale tracker error: {e}')

        # Stage 1.6: Sports Intelligence
        sports_text = ""
        try:
            if SportsData.is_sports_market(question):
                self._log('INFO', f'  🏟️ Sports market detected — fetching live data...')
                sports_result = self.sports_data.get_data_for_market(question)
                if sports_result:
                    sports_text = sports_result.get('prompt_text', '')
                    self._log('INFO', f'  Sports data: {sports_result["sport_info"]["sport"]} / {sports_result["sport_info"]["league"]} ({sports_result["api_requests"]} API calls)')
                else:
                    self._log('WARN', f'  Sports market detected but no data returned')
            else:
                self._log('INFO', f'  Not a sports market — skipping sports data')
        except Exception as e:
            self._log('WARN', f'  Sports data error: {e}')

        # Stage 2: Assess probability (now with whale data + sports data)
        assessment = self.assess_probability(question, facts, market_data, whale_text, sports_text)

        # Calculate edge
        ai_prob = assessment.get('probability', 0)
        market_prob = market_data['yes_price']
        edge = round((ai_prob - market_prob) * 100, 2)

        self._log('INFO', f'  AI Probability: {ai_prob*100:.1f}%')
        self._log('INFO', f'  Market Price:   {market_prob*100:.1f}%')
        self._log('INFO', f'  Edge:           {edge:+.2f}%')
        self._log('INFO', f'  Confidence:     {assessment.get("confidence", "?")}')
        self._log('INFO', f'  Recommendation: {assessment.get("recommendation", "?")}')

        # Save
        opp_id = self.save_assessment(market_id, market_data, assessment)
        self._log('INFO', f'  Saved as opportunity #{opp_id}')

        return {
            'market_id': market_id,
            'question': question,
            'market_price': market_prob,
            'ai_probability': ai_prob,
            'edge': edge,
            'confidence': assessment.get('confidence'),
            'recommendation': assessment.get('recommendation'),
            'reasoning': assessment.get('reasoning'),
            'key_factors_for': assessment.get('key_factors_for', []),
            'key_factors_against': assessment.get('key_factors_against', []),
            'risks': assessment.get('risks', ''),
            'opportunity_id': opp_id,
            'status': 'analyzed'
        }

    # =========================================================
    # BATCH: Analyze Top Markets
    # =========================================================
    def analyze_top_markets(self, limit: int = 10, cooldown_hours: int = 6) -> list:
        """
        Analyze top markets by volume that have articles.
        Skips markets already analyzed within cooldown_hours.
        """
        conn = self._get_db()
        cursor = conn.cursor()

        # Get markets that have signals (articles)
        # LEFT JOIN to check last analysis time
        cursor.execute('''
            SELECT DISTINCT m.id, m.question, m.volume_24h,
                   (SELECT MAX(o.created_at) FROM opportunities o 
                    WHERE o.market_id = m.id 
                      AND o.type IN ('ai_high_edge', 'ai_edge', 'ai_no_edge')
                   ) as last_analyzed
            FROM markets m
            JOIN signals s ON s.market_id = m.id
            WHERE m.active = 1 
              AND m.closed = 0
              AND (m.end_date IS NULL OR m.end_date > datetime('now'))
            ORDER BY m.volume_24h DESC
            LIMIT ?
        ''', (limit,))

        markets = cursor.fetchall()
        conn.close()

        # Filter out recently analyzed markets
        to_analyze = []
        skipped = 0
        cutoff = datetime.now().isoformat()

        for market_id, question, volume, last_analyzed in markets:
            if last_analyzed:
                try:
                    last_dt = datetime.fromisoformat(last_analyzed)
                    hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                    if hours_ago < cooldown_hours:
                        self._log('INFO', f'Skipping (analyzed {hours_ago:.1f}h ago): {question[:50]}...')
                        skipped += 1
                        continue
                except (ValueError, TypeError):
                    pass  # Can't parse, analyze anyway

            to_analyze.append((market_id, question, volume))

        self._log('INFO', f'Analyzing {len(to_analyze)} markets ({skipped} skipped, cooldown={cooldown_hours}h)')

        results = []
        for market_id, question, volume in to_analyze:
            result = self.analyze_market(market_id)
            results.append(result)
            print()  # Spacing between markets

        return results


# =========================================================
# CLI
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🧠 Oracle Sentinel - AI Brain")
    print("=" * 60)
    print()

    brain = AIBrain()

    # Analyze top markets that have news articles
    results = brain.analyze_top_markets(limit=5)

    print()
    print("=" * 60)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 60)

    for r in results:
        if r.get('status') == 'skipped':
            print(f"\n  ⏭  {r['question'][:50]}...")
            print(f"     Skipped: {r.get('reason', 'Unknown')}")
            continue

        question = r.get('question', 'Unknown')[:50]
        market = r.get('market_price', 0) * 100
        ai = r.get('ai_probability', 0) * 100
        edge = r.get('edge', 0)
        conf = r.get('confidence', '?')
        rec = r.get('recommendation', '?')

        # Edge indicator
        if abs(edge) > 5:
            indicator = "🔴" if edge < 0 else "🟢"
        elif abs(edge) > 2:
            indicator = "🟡"
        else:
            indicator = "⚪"

        print(f"\n  {indicator} {question}...")
        print(f"     Market: {market:.1f}% | AI: {ai:.1f}% | Edge: {edge:+.1f}%")
        print(f"     Confidence: {conf} | Rec: {rec}")
        print(f"     {r.get('reasoning', '')[:80]}")

    # Summary stats
    analyzed = [r for r in results if r.get('status') == 'analyzed']
    edges = [r.get('edge', 0) for r in analyzed]
    high_edge = [r for r in analyzed if abs(r.get('edge', 0)) > 5]

    print(f"\n{'='*60}")
    print(f"  Markets analyzed: {len(analyzed)}")
    print(f"  High edge (>5%):  {len(high_edge)}")
    if edges:
        print(f"  Avg edge:         {sum(abs(e) for e in edges)/len(edges):.1f}%")
    print(f"{'='*60}")