#!/usr/bin/env python3
"""
Self Improvement Engine - Automatically apply fixes from diagnosis
This is the final piece: agent improves itself without human intervention
"""

import sqlite3
import os
import json
import shutil
from datetime import datetime
from self_diagnosis import SelfDiagnosis

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.json')
AI_BRAIN_PATH = os.path.join(os.path.dirname(__file__), 'ai_brain.py')


class SelfImprovement:
    
    def __init__(self):
        self.db_path = DB_PATH
        self.diagnosis = SelfDiagnosis()
        self.config = self._load_config()
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
    
    def _load_config(self) -> dict:
        """Load agent configuration."""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            # Default config
            return {
                'min_edge_threshold': 3.0,
                'confidence_multipliers': {},
                'probability_dampening': 0.0,
                'min_news_sources': 3,
                'lessons_learned': [],
                'version': 1,
                'last_updated': None
            }
    
    def _save_config(self):
        """Save agent configuration."""
        self.config['last_updated'] = datetime.now().isoformat()
        self.config['version'] = self.config.get('version', 0) + 1
        
        # Backup old config
        if os.path.exists(CONFIG_PATH):
            backup_path = CONFIG_PATH + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy(CONFIG_PATH, backup_path)
            self._log('INFO', f"Backed up config to {backup_path}")
        
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        self._log('INFO', f"Saved config version {self.config['version']}")
    
    # =========================================================
    # Apply individual fix types
    # =========================================================
    def apply_threshold_adjustment(self, fix_params: dict) -> bool:
        """Apply edge threshold adjustment."""
        param = fix_params.get('parameter', 'min_edge_threshold')
        new_value = fix_params.get('proposed_value', 5)
        
        old_value = self.config.get(param, 3)
        self.config[param] = new_value
        
        self._log('INFO', f"Adjusted {param}: {old_value} -> {new_value}")
        return True
    
    def apply_category_confidence_adjustment(self, fix_params: dict) -> bool:
        """Apply confidence multiplier for specific category."""
        category = fix_params.get('category')
        multiplier = fix_params.get('confidence_multiplier', 0.8)
        
        if 'confidence_multipliers' not in self.config:
            self.config['confidence_multipliers'] = {}
        
        self.config['confidence_multipliers'][category] = multiplier
        
        self._log('INFO', f"Set confidence multiplier for {category}: {multiplier}")
        return True
    
    def apply_probability_dampening(self, fix_params: dict) -> bool:
        """Apply probability dampening factor."""
        dampening = fix_params.get('dampening_factor', 0.1)
        
        self.config['probability_dampening'] = dampening
        
        self._log('INFO', f"Set probability dampening: {dampening}")
        return True
    
    def apply_data_requirement(self, fix_params: dict) -> bool:
        """Apply minimum data requirements."""
        min_sources = fix_params.get('min_news_sources', 5)
        
        self.config['min_news_sources'] = min_sources
        
        self._log('INFO', f"Set minimum news sources: {min_sources}")
        return True
    
    def apply_prompt_enhancement(self, fix_params: dict) -> bool:
        """Add lessons learned to configuration."""
        lessons = fix_params.get('lessons', [])
        
        if 'lessons_learned' not in self.config:
            self.config['lessons_learned'] = []
        
        # Add new lessons (avoid duplicates)
        for lesson in lessons:
            if lesson not in self.config['lessons_learned']:
                self.config['lessons_learned'].append(lesson)
        
        self._log('INFO', f"Added {len(lessons)} lessons to config")
        return True
    
    # =========================================================
    # Main apply function
    # =========================================================
    def apply_fix(self, proposal: dict) -> bool:
        """Apply a single fix based on its type."""
        fix_type = proposal.get('fix_type')
        fix_params = proposal.get('fix_params', {})
        
        # Parse fix_params if it's a string
        if isinstance(fix_params, str):
            try:
                fix_params = json.loads(fix_params)
            except:
                fix_params = {}
        
        self._log('INFO', f"Applying fix: {fix_type}")
        
        if fix_type == 'threshold_adjustment':
            return self.apply_threshold_adjustment(fix_params)
        elif fix_type == 'category_confidence_adjustment':
            return self.apply_category_confidence_adjustment(fix_params)
        elif fix_type == 'probability_dampening':
            return self.apply_probability_dampening(fix_params)
        elif fix_type == 'data_requirement':
            return self.apply_data_requirement(fix_params)
        elif fix_type == 'prompt_enhancement':
            return self.apply_prompt_enhancement(fix_params)
        else:
            self._log('WARN', f"Unknown fix type: {fix_type}")
            return False
    
    # =========================================================
    # Apply all pending proposals
    # =========================================================
    def apply_all_pending(self) -> dict:
        """Apply all pending improvement proposals."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get pending proposals
        cursor.execute('''
            SELECT * FROM self_improvement_log
            WHERE status = 'proposed'
            ORDER BY created_at ASC
        ''')
        
        proposals = [dict(row) for row in cursor.fetchall()]
        
        if not proposals:
            self._log('INFO', "No pending proposals to apply")
            return {'applied': 0, 'failed': 0}
        
        self._log('INFO', f"Found {len(proposals)} pending proposals")
        
        applied = 0
        failed = 0
        
        for p in proposals:
            # Build fix_params from proposal
            fix_params = {}
            if p['fix_type'] == 'threshold_adjustment':
                fix_params = {'parameter': 'min_edge_threshold', 'proposed_value': 10}
            elif p['fix_type'] == 'prompt_enhancement':
                # Get lessons from error analysis
                error_patterns = self.diagnosis.error_analyzer.get_error_patterns()
                fix_params = {'lessons': error_patterns.get('lessons_learned', [])}
            
            success = self.apply_fix({
                'fix_type': p['fix_type'],
                'fix_params': fix_params
            })
            
            if success:
                cursor.execute('''
                    UPDATE self_improvement_log
                    SET status = 'applied', applied_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (p['id'],))
                applied += 1
            else:
                cursor.execute('''
                    UPDATE self_improvement_log
                    SET status = 'failed'
                    WHERE id = ?
                ''', (p['id'],))
                failed += 1
        
        conn.commit()
        conn.close()
        
        # Save updated config
        self._save_config()
        
        return {'applied': applied, 'failed': failed}
    
    # =========================================================
    # Run full self-improvement cycle
    # =========================================================
    def run_improvement_cycle(self) -> dict:
        """
        Run complete self-improvement cycle:
        1. Analyze errors
        2. Run diagnosis
        3. Apply fixes
        """
        self._log('INFO', "=" * 50)
        self._log('INFO', "STARTING SELF-IMPROVEMENT CYCLE")
        self._log('INFO', "=" * 50)
        
        # Step 1: Analyze any new errors
        self._log('INFO', "\n[Step 1] Analyzing errors...")
        self.diagnosis.error_analyzer.analyze_all_errors()
        
        # Step 2: Run diagnosis (this saves new proposals)
        self._log('INFO', "\n[Step 2] Running diagnosis...")
        proposals = self.diagnosis.diagnose()
        if proposals:
            self.diagnosis.save_proposals(proposals)
        
        # Step 3: Apply all pending fixes
        self._log('INFO', "\n[Step 3] Applying fixes...")
        results = self.apply_all_pending()
        
        # Summary
        self._log('INFO', "\n" + "=" * 50)
        self._log('INFO', "SELF-IMPROVEMENT CYCLE COMPLETE")
        self._log('INFO', f"Applied: {results['applied']} | Failed: {results['failed']}")
        self._log('INFO', "=" * 50)
        
        return results
    
    # =========================================================
    # Print current config
    # =========================================================
    def print_config(self):
        """Print current agent configuration."""
        print("\n" + "=" * 60)
        print("ORACLE SENTINEL - AGENT CONFIGURATION")
        print("=" * 60)
        print(f"Version: {self.config.get('version', 1)}")
        print(f"Last Updated: {self.config.get('last_updated', 'Never')}")
        print()
        print(f"📊 THRESHOLDS")
        print(f"   Min Edge Threshold: {self.config.get('min_edge_threshold', 3)}%")
        print(f"   Min News Sources: {self.config.get('min_news_sources', 3)}")
        print(f"   Probability Dampening: {self.config.get('probability_dampening', 0)}")
        print()
        
        multipliers = self.config.get('confidence_multipliers', {})
        if multipliers:
            print(f"📁 CONFIDENCE MULTIPLIERS BY CATEGORY")
            for cat, mult in multipliers.items():
                print(f"   {cat}: {mult}x")
            print()
        
        lessons = self.config.get('lessons_learned', [])
        if lessons:
            print(f"📝 LESSONS LEARNED ({len(lessons)})")
            for i, lesson in enumerate(lessons[:5], 1):
                print(f"   {i}. {lesson[:80]}...")
            if len(lessons) > 5:
                print(f"   ... and {len(lessons) - 5} more")
        
        print("=" * 60)


def main():
    import sys
    
    improvement = SelfImprovement()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        # Run full improvement cycle
        improvement.run_improvement_cycle()
    elif len(sys.argv) > 1 and sys.argv[1] == '--config':
        # Just show config
        improvement.print_config()
    else:
        # Show help
        print("Oracle Sentinel Self-Improvement Engine")
        print()
        print("Usage:")
        print("  python3 self_improvement.py --apply    Run full improvement cycle")
        print("  python3 self_improvement.py --config   Show current configuration")
        print()
        print("Current pending proposals:")
        
        pending = improvement.diagnosis.get_pending_proposals()
        if pending:
            for p in pending:
                print(f"  - [{p['severity'] if 'severity' in p else 'N/A'}] {p['diagnosis_type']}: {p['proposed_fix'][:50]}...")
        else:
            print("  No pending proposals")


if __name__ == "__main__":
    main()
