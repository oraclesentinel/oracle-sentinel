#!/usr/bin/env python3
"""
Error Analyzer - Analyze why predictions went wrong
Identifies patterns, root causes, and lessons learned
"""

import sqlite3
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class ErrorAnalyzer:
    
    def __init__(self):
        self.db_path = DB_PATH
        self.api_key = OPENROUTER_API_KEY
        self.model = "anthropic/claude-3.5-haiku"  # Use cheap model for analysis
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for error analysis."""
        if not self.api_key:
            return "API key not configured"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an error analysis engine for a prediction market AI agent.
Your job is to analyze why a prediction was wrong and identify:
1. The type of error (overconfidence, wrong data, misinterpretation, timing, etc.)
2. What information was missed or misweighted
3. Specific lessons for future predictions

Be concise and actionable. Output as JSON."""
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"API error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    # =========================================================
    # Get wrong predictions that haven't been analyzed
    # =========================================================
    def get_unanalyzed_errors(self) -> list:
        """Get wrong predictions that haven't been analyzed yet."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pt.*, o.raw_data as reasoning_json
            FROM prediction_tracking pt
            LEFT JOIN opportunities o ON pt.opportunity_id = o.id
            LEFT JOIN error_analysis ea ON pt.id = ea.prediction_id
            WHERE pt.direction_correct = 0
            AND ea.id IS NULL
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # =========================================================
    # Analyze a single wrong prediction
    # =========================================================
    def analyze_error(self, prediction: dict) -> dict:
        """Analyze why a single prediction was wrong."""
        
        # Parse reasoning if available
        reasoning = {}
        if prediction.get('reasoning_json'):
            try:
                reasoning = json.loads(prediction['reasoning_json'])
            except:
                pass
        
        # Build analysis prompt
        prompt = f"""WRONG PREDICTION ANALYSIS

Question: {prediction.get('question', 'Unknown')}
Category: {prediction.get('category', 'Unknown')}

Our Prediction:
- Signal: {prediction.get('signal_type', 'Unknown')}
- AI Probability: {prediction.get('ai_probability', 'Unknown')}
- Market Price at Signal: {prediction.get('market_price_at_signal', 'Unknown')}
- Edge Claimed: {prediction.get('edge_at_signal', 'Unknown')}%
- Confidence: {prediction.get('confidence', 'Unknown')}

Actual Outcome: {prediction.get('final_resolution', 'Unknown')}

Our Reasoning at Time of Prediction:
{reasoning.get('reasoning', 'No reasoning recorded')}

Key Factors We Considered FOR:
{reasoning.get('key_factors_for', [])}

Key Factors We Considered AGAINST:
{reasoning.get('key_factors_against', [])}

Analyze this error and respond with JSON:
{{
    "error_type": "one of: overconfidence, underconfidence, wrong_data, misinterpretation, timing, market_manipulation, black_swan, insufficient_data",
    "error_magnitude": "how wrong were we (0-1 scale)",
    "what_we_missed": ["list of things we should have considered"],
    "root_cause": "single sentence explaining main reason",
    "lesson_learned": "specific actionable lesson for future",
    "category_specific_insight": "insight specific to this market category"
}}"""

        self._log('INFO', f"Analyzing error for: {prediction.get('question', 'Unknown')[:50]}...")
        
        response = self._call_llm(prompt)
        
        # Parse response
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                json_str = response[response.find('{'):response.rfind('}')+1]
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "error_type": "unknown",
                    "error_magnitude": 0.5,
                    "what_we_missed": ["Could not parse analysis"],
                    "root_cause": response[:200],
                    "lesson_learned": "Improve error analysis parsing",
                    "category_specific_insight": "N/A"
                }
        except json.JSONDecodeError:
            analysis = {
                "error_type": "unknown",
                "error_magnitude": 0.5,
                "what_we_missed": ["JSON parse failed"],
                "root_cause": response[:200],
                "lesson_learned": "N/A",
                "category_specific_insight": "N/A"
            }
        
        return analysis
    
    # =========================================================
    # Save error analysis to database
    # =========================================================
    def save_analysis(self, prediction_id: int, prediction: dict, analysis: dict):
        """Save error analysis to database."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_analysis (
                prediction_id, category, predicted_probability, actual_outcome,
                error_type, error_magnitude, possible_causes, reasoning_at_prediction,
                what_was_missed, lessons_learned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id,
            prediction.get('category'),
            prediction.get('ai_probability'),
            1 if prediction.get('final_resolution') == 'YES' else 0,
            analysis.get('error_type'),
            analysis.get('error_magnitude'),
            analysis.get('root_cause'),
            prediction.get('reasoning_json', '')[:1000],
            json.dumps(analysis.get('what_we_missed', [])),
            analysis.get('lesson_learned')
        ))
        
        conn.commit()
        conn.close()
        self._log('INFO', f"Saved analysis for prediction {prediction_id}")
    
    # =========================================================
    # Analyze all unanalyzed errors
    # =========================================================
    def analyze_all_errors(self):
        """Analyze all wrong predictions that haven't been analyzed."""
        errors = self.get_unanalyzed_errors()
        
        if not errors:
            self._log('INFO', "No unanalyzed errors found")
            return []
        
        self._log('INFO', f"Found {len(errors)} unanalyzed wrong predictions")
        
        results = []
        for pred in errors:
            analysis = self.analyze_error(pred)
            self.save_analysis(pred['id'], pred, analysis)
            results.append({
                'prediction_id': pred['id'],
                'question': pred.get('question', '')[:50],
                'analysis': analysis
            })
        
        return results
    
    # =========================================================
    # Get error patterns (aggregate insights)
    # =========================================================
    def get_error_patterns(self) -> dict:
        """Aggregate error analyses to find patterns."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Count by error type
        cursor.execute('''
            SELECT error_type, COUNT(*) as count
            FROM error_analysis
            GROUP BY error_type
            ORDER BY count DESC
        ''')
        by_type = {row['error_type']: row['count'] for row in cursor.fetchall()}
        
        # Count by category
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM error_analysis
            GROUP BY category
            ORDER BY count DESC
        ''')
        by_category = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Get all lessons
        cursor.execute('SELECT lessons_learned FROM error_analysis WHERE lessons_learned IS NOT NULL')
        lessons = [row['lessons_learned'] for row in cursor.fetchall()]
        
        # Average error magnitude
        cursor.execute('SELECT AVG(error_magnitude) as avg_mag FROM error_analysis')
        avg_magnitude = cursor.fetchone()['avg_mag'] or 0
        
        conn.close()
        
        return {
            'total_errors_analyzed': sum(by_type.values()),
            'by_error_type': by_type,
            'by_category': by_category,
            'avg_error_magnitude': round(avg_magnitude, 3),
            'lessons_learned': lessons
        }
    
    # =========================================================
    # Print error analysis report
    # =========================================================
    def print_report(self):
        """Print error analysis report."""
        patterns = self.get_error_patterns()
        
        print("\n" + "=" * 60)
        print("ORACLE SENTINEL - ERROR ANALYSIS REPORT")
        print("=" * 60)
        
        print(f"\n📊 TOTAL ERRORS ANALYZED: {patterns['total_errors_analyzed']}")
        print(f"   Average Error Magnitude: {patterns['avg_error_magnitude']}")
        
        if patterns['by_error_type']:
            print("\n🔴 ERRORS BY TYPE")
            print("-" * 40)
            for error_type, count in patterns['by_error_type'].items():
                print(f"   {error_type}: {count}")
        
        if patterns['by_category']:
            print("\n📁 ERRORS BY CATEGORY")
            print("-" * 40)
            for category, count in patterns['by_category'].items():
                print(f"   {category}: {count}")
        
        if patterns['lessons_learned']:
            print("\n📝 LESSONS LEARNED")
            print("-" * 40)
            for i, lesson in enumerate(patterns['lessons_learned'][:5], 1):
                print(f"   {i}. {lesson}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    analyzer = ErrorAnalyzer()
    
    # Analyze all unanalyzed errors
    print("Analyzing wrong predictions...")
    results = analyzer.analyze_all_errors()
    
    if results:
        print(f"\nAnalyzed {len(results)} predictions:")
        for r in results:
            print(f"  - {r['question']}...")
            print(f"    Error type: {r['analysis'].get('error_type')}")
            print(f"    Lesson: {r['analysis'].get('lesson_learned')}")
    
    # Print aggregate report
    analyzer.print_report()
