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
    # BACKTEST: Simulate fix before applying
    # =========================================================

    def apply_near_resolved_threshold(self, fix_params: dict) -> bool:
        """Apply near-resolved threshold adjustment to ai_brain.py"""
        old_threshold = fix_params.get('old_threshold', 0.97)
        new_threshold = fix_params.get('new_threshold', 0.90)
        
        ai_brain_path = os.path.join(os.path.dirname(__file__), 'ai_brain.py')
        
        try:
            with open(ai_brain_path, 'r') as f:
                ai_content = f.read()
            
            # Update the threshold in _force_recommendation
            old_pattern = f'market_yes_price > {old_threshold} or market_yes_price < {1-old_threshold}'
            new_pattern = f'market_yes_price > {new_threshold} or market_yes_price < {round(1-new_threshold, 2)}'
            
            if old_pattern in ai_content:
                ai_content = ai_content.replace(old_pattern, new_pattern)
                
                with open(ai_brain_path, 'w') as f:
                    f.write(ai_content)
                
                self._log('INFO', f"Updated near-resolved threshold: {old_threshold} -> {new_threshold}")
                return True
            else:
                self._log('WARN', f"Pattern not found in ai_brain.py, trying alternative...")
                # Try alternative pattern (might have different formatting)
                import re
                pattern = r'market_yes_price > 0\.9\d+ or market_yes_price < 0\.0\d+'
                if re.search(pattern, ai_content):
                    ai_content = re.sub(pattern, new_pattern, ai_content)
                    with open(ai_brain_path, 'w') as f:
                        f.write(ai_content)
                    self._log('INFO', f"Updated near-resolved threshold via regex")
                    return True
                    
                self._log('WARN', "Could not find threshold pattern to update")
                return False
                
        except Exception as e:
            self._log('ERROR', f"Failed to update ai_brain.py: {e}")
            return False


    def backtest_fix(self, proposal: dict) -> dict:
        """
        Simulate what accuracy would have been if this fix was applied earlier.
        Returns: {'before': accuracy_before, 'after': accuracy_after, 'improvement': pct_change}
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        fix_type = proposal.get('fix_type')
        fix_params = proposal.get('fix_params', {})
        
        # Get all resolved predictions
        cursor.execute("""
            SELECT id, signal_type, ai_probability, market_price_at_signal, 
                   edge_at_signal, confidence, direction_correct, category
            FROM prediction_tracking 
            WHERE direction_correct IS NOT NULL
        """)
        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if len(predictions) < 3:
            self._log('WARN', "Not enough data for backtest (need at least 3 resolved)")
            return {'before': None, 'after': None, 'improvement': None, 'skip_reason': 'insufficient_data'}
        
        # Calculate current accuracy (before fix)
        correct_before = sum(1 for p in predictions if p['direction_correct'] == 1)
        total_before = len(predictions)
        accuracy_before = (correct_before / total_before) * 100 if total_before > 0 else 0
        
        # Simulate: which predictions would have been SKIPPED with this fix?
        skipped_with_fix = 0
        correct_after = 0
        total_after = 0
        
        for p in predictions:
            would_skip = False
            
            # Simulate threshold_adjustment
            if fix_type == 'threshold_adjustment':
                new_threshold = fix_params.get('proposed_value', 10)
                edge = abs(p['edge_at_signal'] or 0)
                if edge < new_threshold:
                    would_skip = True
            
            # Simulate category_confidence_adjustment
            elif fix_type == 'category_confidence_adjustment':
                target_category = fix_params.get('category')
                multiplier = fix_params.get('confidence_multiplier', 0.8)
                if p['category'] == target_category:
                    # With lower multiplier, need more edge
                    current_threshold = self.config.get('min_edge_threshold', 10)
                    adjusted_threshold = current_threshold / multiplier
                    edge = abs(p['edge_at_signal'] or 0)
                    if edge < adjusted_threshold:
                        would_skip = True
            
            # Simulate data_requirement
            elif fix_type == 'data_requirement':
                # Can't backtest this without article count data
                pass
            
            # Simulate probability_dampening
            elif fix_type == 'probability_dampening':
                # Dampening doesn't skip, just adjusts probability
                # Hard to backtest without re-running the signal logic
                pass
            
            if not would_skip:
                total_after += 1
                if p['direction_correct'] == 1:
                    correct_after += 1
            else:
                skipped_with_fix += 1
        
        accuracy_after = (correct_after / total_after) * 100 if total_after > 0 else 0
        improvement = accuracy_after - accuracy_before
        
        self._log('INFO', f"  📊 Backtest: {accuracy_before:.1f}% → {accuracy_after:.1f}% ({improvement:+.1f}%)")
        self._log('INFO', f"     Predictions: {total_before} → {total_after} (skipped {skipped_with_fix})")
        
        return {
            'before': round(accuracy_before, 2),
            'after': round(accuracy_after, 2),
            'improvement': round(improvement, 2),
            'total_before': total_before,
            'total_after': total_after,
            'skipped': skipped_with_fix
        }
    
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
        elif fix_type == 'near_resolved_threshold':
            return self.apply_near_resolved_threshold(fix_params)
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
            elif p['fix_type'] == 'category_confidence_adjustment':
                fix_params = {'category': p.get('category_affected'), 'confidence_multiplier': 0.8}
            elif p['fix_type'] == 'probability_dampening':
                fix_params = {'dampening_factor': 0.1}
            elif p['fix_type'] == 'data_requirement':
                fix_params = {'min_news_sources': 5}
            elif p['fix_type'] == 'prompt_enhancement':
                # Get lessons from error analysis
                error_patterns = self.diagnosis.error_analyzer.get_error_patterns()
                fix_params = {'lessons': error_patterns.get('lessons_learned', [])}

            # =========================================================
            # BACKTEST VALIDATION: Only apply if improvement > 0
            # =========================================================
            backtest_result = self.backtest_fix({
                'fix_type': p['fix_type'],
                'fix_params': fix_params
            })
            
            # Skip backtest for certain fix types (always beneficial)
            skip_backtest = p['fix_type'] in ['prompt_enhancement', 'data_requirement']
            
            if not skip_backtest and backtest_result.get('improvement') is not None:
                if backtest_result['improvement'] <= 0:
                    self._log('WARN', f"  Backtest shows no improvement ({backtest_result['improvement']:+.1f}%) - SKIPPING fix")
                    cursor.execute('''
                        UPDATE self_improvement_log
                        SET status = 'skipped_backtest', 
                            backtest_before = ?, backtest_after = ?, improvement_pct = ?
                        WHERE id = ?
                    ''', (backtest_result.get('before'), backtest_result.get('after'), 
                           backtest_result.get('improvement'), p['id']))
                    failed += 1
                    continue
                else:
                    self._log('INFO', f"  Backtest positive ({backtest_result['improvement']:+.1f}%) - applying fix")

            success = self.apply_fix({
                'fix_type': p['fix_type'],
                'fix_params': fix_params
            })

            if success:
                cursor.execute('''
                    UPDATE self_improvement_log
                    SET status = 'applied', applied_at = CURRENT_TIMESTAMP,
                        backtest_before = ?, backtest_after = ?, improvement_pct = ?
                    WHERE id = ?
                ''', (backtest_result.get('before'), backtest_result.get('after'), 
                       backtest_result.get('improvement'), p['id']))
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
    # ROLLBACK: Restore previous config version
    # =========================================================
    def rollback_to_version(self, target_version: int = None) -> dict:
        """
        Rollback config to a previous version.
        If target_version is None, rollback to version - 1.
        """
        import glob
        import shutil
        
        config_dir = os.path.dirname(CONFIG_PATH)
        
        # Get current version
        current_version = self.config.get('version', 0)
        
        if target_version is None:
            target_version = current_version - 1
        
        if target_version < 1:
            self._log('ERROR', "Cannot rollback: no previous version available")
            return {'success': False, 'error': 'No previous version'}
        
        # Find backup with matching version
        backups = glob.glob(os.path.join(config_dir, 'agent_config.json.backup.*'))
        target_backup = None
        
        for backup_path in sorted(backups, reverse=True):
            try:
                with open(backup_path, 'r') as f:
                    backup_config = json.load(f)
                    if backup_config.get('version') == target_version:
                        target_backup = backup_path
                        break
            except:
                continue
        
        if not target_backup:
            self._log('ERROR', f"Backup for version {target_version} not found")
            return {'success': False, 'error': f'Version {target_version} not found'}
        
        # Backup current config before rollback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy(CONFIG_PATH, f"{CONFIG_PATH}.backup.{timestamp}")
        self._log('INFO', f"Backed up current config (v{current_version})")
        
        # Restore from backup
        shutil.copy(target_backup, CONFIG_PATH)
        self._log('INFO', f"Restored config from {target_backup}")
        
        # Reload config
        self.config = self._load_config()
        
        # Log rollback in database
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO self_improvement_log 
            (diagnosis_type, diagnosis_detail, category_affected, proposed_fix, fix_type, status, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            'manual_rollback',
            f'Rolled back from v{current_version} to v{target_version}',
            'all',
            f'Restore config version {target_version}',
            'rollback',
            'applied'
        ))
        conn.commit()
        conn.close()
        
        self._log('INFO', f"✅ Rollback complete: v{current_version} → v{target_version}")
        
        return {
            'success': True,
            'from_version': current_version,
            'to_version': target_version,
            'config': self.config
        }

    def auto_rollback_if_needed(self) -> bool:
        """
        Check if recent predictions are performing poorly after a fix.
        If accuracy dropped significantly, trigger auto-rollback.
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get last fix applied_at
        cursor.execute("""
            SELECT applied_at FROM self_improvement_log 
            WHERE status = 'applied' AND fix_type != 'rollback'
            ORDER BY applied_at DESC LIMIT 1
        """)
        row = cursor.fetchone()
        
        if not row or not row[0]:
            conn.close()
            return False
        
        last_fix_time = row[0]
        
        # Get predictions after last fix
        cursor.execute("""
            SELECT direction_correct FROM prediction_tracking
            WHERE created_at > ? AND direction_correct IS NOT NULL
            ORDER BY created_at ASC
            LIMIT 5
        """, (last_fix_time,))
        
        recent_predictions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(recent_predictions) < 3:
            # Not enough data to decide
            return False
        
        # Check if first 3 predictions after fix are all wrong
        first_three = recent_predictions[:3]
        if sum(first_three) == 0:  # All wrong
            self._log('WARN', "⚠️ First 3 predictions after fix are ALL WRONG - triggering auto-rollback")
            result = self.rollback_to_version()
            return result.get('success', False)
        
        return False


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
        

        # Step 0: Check if we have new resolved predictions since last run
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(applied_at) FROM self_improvement_log")
        last_run = cursor.fetchone()[0]
        
        if last_run:
            cursor.execute("""
                SELECT COUNT(*) FROM prediction_tracking 
                WHERE direction_correct IS NOT NULL 
                AND resolved_at > ?
            """, (last_run,))
        else:
            cursor.execute("SELECT COUNT(*) FROM prediction_tracking WHERE direction_correct IS NOT NULL")
        
        new_resolved = cursor.fetchone()[0]
        conn.close()
        
        if new_resolved == 0:
            self._log('INFO', "No new resolved predictions since last run. SKIPPING.")
            self._log('INFO', "=" * 50)
            return {'applied': 0, 'failed': 0, 'skipped': True, 'reason': 'no_new_data'}

        self._log('INFO', f"Found {new_resolved} new resolved predictions - proceeding")

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
