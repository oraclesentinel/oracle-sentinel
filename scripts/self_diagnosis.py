#!/usr/bin/env python3
"""
Self Diagnosis Engine - Agent diagnoses its own problems and proposes fixes
Combines self-awareness + error analysis to generate improvement proposals
"""

import sqlite3
import os
import json
from datetime import datetime
from self_awareness import SelfAwareness
from error_analyzer import ErrorAnalyzer

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class SelfDiagnosis:
    
    def __init__(self):
        self.db_path = DB_PATH
        self.awareness = SelfAwareness()
        self.error_analyzer = ErrorAnalyzer()
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
    
    # =========================================================
    # Diagnose issues and propose fixes
    # =========================================================
    def diagnose(self) -> list:
        """
        Run full diagnosis and generate improvement proposals.
        Returns list of proposed improvements.
        """
        self._log('INFO', "Starting self-diagnosis...")
        
        proposals = []
        
        # Get current state
        report = self.awareness.generate_report()
        error_patterns = self.error_analyzer.get_error_patterns()
        
        overall = report['overall']
        by_category = report['by_category']
        weaknesses = report['weaknesses']
        
        # =========================================================
        # DIAGNOSIS 1: Overall accuracy too low
        # =========================================================
        if overall['resolved'] >= 5 and overall['accuracy_pct'] < 40:
            proposals.append({
                'diagnosis_type': 'low_overall_accuracy',
                'diagnosis_detail': f"Overall accuracy is {overall['accuracy_pct']}% (target: >50%)",
                'category_affected': 'all',
                'severity': 'critical',
                'proposed_fix': 'Increase confidence threshold from 3% edge to 5% edge before signaling',
                'fix_type': 'threshold_adjustment',
                'fix_params': {
                    'parameter': 'min_edge_threshold',
                    'current_value': 3,
                    'proposed_value': 5
                },
                'expected_impact': 'Fewer signals but higher quality'
            })
        
        # =========================================================
        # DIAGNOSIS 2: Specific category performing badly
        # =========================================================
        for category, metrics in by_category.items():
            if metrics['resolved'] >= 3 and metrics['accuracy_pct'] < 30:
                proposals.append({
                    'diagnosis_type': 'category_underperformance',
                    'diagnosis_detail': f"{category} accuracy is {metrics['accuracy_pct']}% with {metrics['resolved']} resolved",
                    'category_affected': category,
                    'severity': 'high',
                    'proposed_fix': f'Reduce confidence in {category} predictions by applying 0.8x multiplier',
                    'fix_type': 'category_confidence_adjustment',
                    'fix_params': {
                        'category': category,
                        'confidence_multiplier': 0.8
                    },
                    'expected_impact': f'More conservative {category} predictions'
                })
        
        # =========================================================
        # DIAGNOSIS 3: Overconfidence pattern
        # =========================================================
        if error_patterns.get('by_error_type', {}).get('overconfidence', 0) >= 2:
            proposals.append({
                'diagnosis_type': 'systematic_overconfidence',
                'diagnosis_detail': f"Found {error_patterns['by_error_type']['overconfidence']} overconfidence errors",
                'category_affected': 'all',
                'severity': 'high',
                'proposed_fix': 'Apply probability dampening: move all probabilities 10% closer to 50%',
                'fix_type': 'probability_dampening',
                'fix_params': {
                    'dampening_factor': 0.1
                },
                'expected_impact': 'Less extreme probability estimates'
            })
        
        # =========================================================
        # DIAGNOSIS 4: Negative average edge
        # =========================================================
        if overall['avg_edge'] < 0:
            proposals.append({
                'diagnosis_type': 'negative_edge',
                'diagnosis_detail': f"Average edge is {overall['avg_edge']}% (should be positive)",
                'category_affected': 'all',
                'severity': 'high',
                'proposed_fix': 'Only signal when edge > 10% instead of current threshold',
                'fix_type': 'threshold_adjustment',
                'fix_params': {
                    'parameter': 'min_edge_threshold',
                    'current_value': 3,
                    'proposed_value': 10
                },
                'expected_impact': 'Much fewer signals but positive expected value'
            })
        
        # =========================================================
        # DIAGNOSIS 5: Insufficient data patterns
        # =========================================================
        insufficient_errors = error_patterns.get('by_error_type', {}).get('insufficient_data', 0)
        if insufficient_errors >= 2:
            proposals.append({
                'diagnosis_type': 'insufficient_data_errors',
                'diagnosis_detail': f"Found {insufficient_errors} errors due to insufficient data",
                'category_affected': 'all',
                'severity': 'medium',
                'proposed_fix': 'Require minimum 5 news sources before making prediction',
                'fix_type': 'data_requirement',
                'fix_params': {
                    'min_news_sources': 5
                },
                'expected_impact': 'Better informed predictions'
            })
        
        # =========================================================
        # DIAGNOSIS 6: Apply lessons from error analysis
        # =========================================================
        lessons = error_patterns.get('lessons_learned', [])
        if lessons:
            proposals.append({
                'diagnosis_type': 'lessons_from_errors',
                'diagnosis_detail': f"Extracted {len(lessons)} lessons from error analysis",
                'category_affected': 'all',
                'severity': 'medium',
                'proposed_fix': 'Incorporate lessons into system prompt',
                'fix_type': 'prompt_enhancement',
                'fix_params': {
                    'lessons': lessons[:5]  # Top 5 lessons
                },
                'expected_impact': 'AI learns from past mistakes'
            })
        
        self._log('INFO', f"Generated {len(proposals)} improvement proposals")
        return proposals
    
    # =========================================================
    # Save proposals to database
    # =========================================================
    def save_proposals(self, proposals: list):
        """Save improvement proposals to database."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        for p in proposals:
            cursor.execute('''
                INSERT INTO self_improvement_log (
                    diagnosis_type, diagnosis_detail, category_affected,
                    proposed_fix, fix_type, status
                ) VALUES (?, ?, ?, ?, ?, 'proposed')
            ''', (
                p['diagnosis_type'],
                p['diagnosis_detail'],
                p['category_affected'],
                p['proposed_fix'],
                p['fix_type']
            ))
        
        conn.commit()
        conn.close()
        self._log('INFO', f"Saved {len(proposals)} proposals to database")
    
    # =========================================================
    # Get pending proposals
    # =========================================================
    def get_pending_proposals(self) -> list:
        """Get proposals that haven't been applied yet."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM self_improvement_log
            WHERE status = 'proposed'
            ORDER BY created_at DESC
        ''')
        
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    
    # =========================================================
    # Print diagnosis report
    # =========================================================
    def print_diagnosis(self, proposals: list):
        """Print diagnosis report."""
        print("\n" + "=" * 60)
        print("ORACLE SENTINEL - SELF DIAGNOSIS REPORT")
        print("=" * 60)
        
        if not proposals:
            print("\n✅ No issues diagnosed. System performing within acceptable parameters.")
            print("=" * 60)
            return
        
        print(f"\n🔍 FOUND {len(proposals)} ISSUES\n")
        
        for i, p in enumerate(proposals, 1):
            severity_icon = "🔴" if p['severity'] == 'critical' else "🟠" if p['severity'] == 'high' else "🟡"
            
            print(f"{severity_icon} ISSUE {i}: {p['diagnosis_type'].upper()}")
            print(f"   Detail: {p['diagnosis_detail']}")
            print(f"   Affects: {p['category_affected']}")
            print(f"   Severity: {p['severity']}")
            print(f"   ")
            print(f"   💡 Proposed Fix: {p['proposed_fix']}")
            print(f"   📈 Expected Impact: {p['expected_impact']}")
            print()
        
        print("=" * 60)
        print("To apply fixes, run: python3 self_improvement.py --apply")
        print("=" * 60)


def main():
    diagnosis = SelfDiagnosis()
    
    # Run error analysis first
    print("Step 1: Analyzing errors...")
    diagnosis.error_analyzer.analyze_all_errors()
    
    # Run diagnosis
    print("\nStep 2: Running self-diagnosis...")
    proposals = diagnosis.diagnose()
    
    # Save proposals
    if proposals:
        diagnosis.save_proposals(proposals)
    
    # Print report
    diagnosis.print_diagnosis(proposals)
    
    # Also print error patterns
    print("\n")
    diagnosis.error_analyzer.print_report()


if __name__ == "__main__":
    main()
