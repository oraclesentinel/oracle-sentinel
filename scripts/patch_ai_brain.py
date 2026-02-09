#!/usr/bin/env python3
"""
Patch ai_brain.py to integrate with self-improvement config.
Run once to add self-improvement capabilities.
"""

import os
import re
import shutil
from datetime import datetime

AI_BRAIN_PATH = os.path.join(os.path.dirname(__file__), 'ai_brain.py')
BACKUP_PATH = AI_BRAIN_PATH + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'


def patch_file():
    # Read current file
    with open(AI_BRAIN_PATH, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'from agent_config_loader import' in content:
        print("ai_brain.py already patched!")
        return False
    
    # Backup original
    shutil.copy(AI_BRAIN_PATH, BACKUP_PATH)
    print(f"Backed up to: {BACKUP_PATH}")
    
    # =========================================================
    # PATCH 1: Add import at top
    # =========================================================
    old_import = "from sports_data import SportsData"
    new_import = """from sports_data import SportsData
from agent_config_loader import get_agent_config"""
    
    content = content.replace(old_import, new_import)
    print("✓ Added agent_config_loader import")
    
    # =========================================================
    # PATCH 2: Load config in __init__
    # =========================================================
    old_init = "self.sports_data = SportsData()"
    new_init = """self.sports_data = SportsData()
        self.agent_config = get_agent_config()  # Self-improvement config"""
    
    content = content.replace(old_init, new_init)
    print("✓ Added config loading in __init__")
    
    # =========================================================
    # PATCH 3: Modify _force_recommendation to use dynamic threshold
    # =========================================================
    # Find and replace the edge threshold logic
    old_force_rec = '''    def _force_recommendation(self, result: dict, market_yes_price: float) -> dict:
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
        new_rec = 'SKIP'  # default'''
    
    new_force_rec = '''    def _force_recommendation(self, result: dict, market_yes_price: float, category: str = None) -> dict:
        """
        Override LLM recommendation with dynamic rules from self-improvement config.
        Threshold and confidence adjustments come from agent_config.
        """
        ai_prob = result.get('probability', 0)
        confidence = result.get('confidence', 'LOW')
        
        # Apply probability dampening from self-improvement config
        if hasattr(self, 'agent_config') and self.agent_config.probability_dampening > 0:
            ai_prob = self.agent_config.apply_dampening(ai_prob)
            result['probability_dampened'] = ai_prob
        
        edge = (ai_prob - market_yes_price) * 100  # in percentage points
        
        # Get dynamic threshold from self-improvement config
        min_edge_threshold = 5.0  # default
        if hasattr(self, 'agent_config'):
            min_edge_threshold = self.agent_config.min_edge_threshold
            self._log('INFO', f'  Using dynamic edge threshold: {min_edge_threshold}% (config v{self.agent_config.version})')

        llm_rec = result.get('recommendation', 'SKIP')
        new_rec = 'SKIP'  # default'''
    
    content = content.replace(old_force_rec, new_force_rec)
    print("✓ Updated _force_recommendation header with dynamic config")
    
    # =========================================================
    # PATCH 4: Replace hardcoded edge thresholds
    # =========================================================
    # Replace "abs(edge) >= 10" with dynamic threshold check
    old_edge_check_10 = "elif abs(edge) >= 10 and confidence == 'HIGH':"
    new_edge_check_10 = "elif abs(edge) >= min_edge_threshold * 2 and confidence == 'HIGH':  # 2x threshold for high confidence"
    content = content.replace(old_edge_check_10, new_edge_check_10)
    
    # Replace "abs(edge) >= 5" with dynamic threshold
    old_edge_check_5 = "elif abs(edge) >= 5 and confidence == 'HIGH':"
    new_edge_check_5 = "elif abs(edge) >= min_edge_threshold and confidence == 'HIGH':  # Dynamic threshold"
    content = content.replace(old_edge_check_5, new_edge_check_5)
    
    # Replace "abs(edge) < 5" with dynamic threshold
    old_edge_small = "elif abs(edge) < 5:"
    new_edge_small = "elif abs(edge) < min_edge_threshold:  # Below dynamic threshold"
    content = content.replace(old_edge_small, new_edge_small)
    
    print("✓ Replaced hardcoded edge thresholds with dynamic values")
    
    # =========================================================
    # PATCH 5: Add lessons learned to system prompt
    # =========================================================
    old_system_prompt_end = '''You MUST respond in EXACTLY this JSON format and nothing else:
{{
    "probability": 0.XX,'''
    
    new_system_prompt_end = '''{lessons_section}

You MUST respond in EXACTLY this JSON format and nothing else:
{{
    "probability": 0.XX,'''
    
    content = content.replace(old_system_prompt_end, new_system_prompt_end)
    print("✓ Added lessons placeholder to system prompt")
    
    # Now add the lessons_section variable before system_prompt
    old_current_time = '''# Current time context (CRITICAL for timestamp awareness)
        current_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')'''
    
    new_current_time = '''# Current time context (CRITICAL for timestamp awareness)
        current_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        
        # Get lessons learned from self-improvement config
        lessons_section = ""
        if hasattr(self, 'agent_config'):
            lessons_section = self.agent_config.get_lessons_for_prompt()'''
    
    content = content.replace(old_current_time, new_current_time)
    print("✓ Added lessons_section generation")
    
    # =========================================================
    # PATCH 6: Pass category to _force_recommendation
    # =========================================================
    old_force_call = "result = self._force_recommendation(result, yes_price)"
    new_force_call = """# Detect category for self-improvement adjustments
            from market_categorizer import MarketCategorizer
            categorizer = MarketCategorizer()
            market_category = categorizer.categorize(question)
            
            result = self._force_recommendation(result, yes_price, category=market_category)"""
    
    content = content.replace(old_force_call, new_force_call)
    print("✓ Added category detection before force_recommendation")
    
    # =========================================================
    # Write patched file
    # =========================================================
    with open(AI_BRAIN_PATH, 'w') as f:
        f.write(content)
    
    print()
    print("=" * 50)
    print("✅ ai_brain.py successfully patched!")
    print(f"   Backup saved to: {BACKUP_PATH}")
    print()
    print("Self-improvement integration:")
    print("  - Dynamic edge threshold from config")
    print("  - Lessons learned injected into AI prompt")
    print("  - Probability dampening support")
    print("  - Category-aware recommendations")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    patch_file()
