#!/usr/bin/env python3
"""
Self Awareness Engine - Agent knows its own performance
Calculates metrics, detects trends, identifies weaknesses
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from market_categorizer import MarketCategorizer

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')


class SelfAwareness:
    
    def __init__(self):
        self.db_path = DB_PATH
        self.categorizer = MarketCategorizer()
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
    
    # =========================================================
    # STEP 1: Backfill categories for existing predictions
    # =========================================================
    def backfill_categories(self):
        """Assign categories to predictions that don't have one."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get predictions without category
        cursor.execute('''
            SELECT pt.id, pt.question, m.description
            FROM prediction_tracking pt
            LEFT JOIN markets m ON pt.market_id = m.id
            WHERE pt.category IS NULL OR pt.category = ''
        ''')
        
        rows = cursor.fetchall()
        self._log('INFO', f"Found {len(rows)} predictions without category")
        
        updated = 0
        for row in rows:
            category = self.categorizer.categorize(
                row['question'] or '',
                row['description'] or ''
            )
            cursor.execute(
                'UPDATE prediction_tracking SET category = ? WHERE id = ?',
                (category, row['id'])
            )
            updated += 1
        
        conn.commit()
        conn.close()
        self._log('INFO', f"Updated {updated} predictions with categories")
        return updated
    
    # =========================================================
    # STEP 2: Calculate overall metrics
    # =========================================================
    def calculate_overall_metrics(self) -> dict:
        """Calculate overall performance metrics."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Total predictions
        cursor.execute('SELECT COUNT(*) as total FROM prediction_tracking')
        total = cursor.fetchone()['total']
        
        # Resolved predictions
        cursor.execute('''
            SELECT COUNT(*) as resolved 
            FROM prediction_tracking 
            WHERE final_resolution IS NOT NULL
        ''')
        resolved = cursor.fetchone()['resolved']
        
        # Correct predictions
        cursor.execute('''
            SELECT COUNT(*) as correct 
            FROM prediction_tracking 
            WHERE direction_correct = 1
        ''')
        correct = cursor.fetchone()['correct']
        
        # Wrong predictions
        cursor.execute('''
            SELECT COUNT(*) as wrong 
            FROM prediction_tracking 
            WHERE direction_correct = 0
        ''')
        wrong = cursor.fetchone()['wrong']
        
        # Calculate accuracy
        accuracy = (correct / resolved * 100) if resolved > 0 else 0
        
        # Average edge
        cursor.execute('''
            SELECT AVG(edge_at_signal) as avg_edge 
            FROM prediction_tracking
        ''')
        avg_edge = cursor.fetchone()['avg_edge'] or 0
        
        # Brier score (if we have probability data)
        cursor.execute('''
            SELECT 
                ai_probability,
                CASE WHEN direction_correct = 1 THEN 1.0 ELSE 0.0 END as outcome
            FROM prediction_tracking
            WHERE final_resolution IS NOT NULL
            AND ai_probability IS NOT NULL
        ''')
        brier_data = cursor.fetchall()
        
        brier_score = None
        if brier_data:
            brier_sum = sum((row['ai_probability'] - row['outcome']) ** 2 for row in brier_data)
            brier_score = brier_sum / len(brier_data)
        
        conn.close()
        
        return {
            'total_predictions': total,
            'resolved': resolved,
            'pending': total - resolved,
            'correct': correct,
            'wrong': wrong,
            'accuracy_pct': round(accuracy, 2),
            'avg_edge': round(avg_edge, 2),
            'brier_score': round(brier_score, 4) if brier_score else None
        }
    
    # =========================================================
    # STEP 3: Calculate metrics by category
    # =========================================================
    def calculate_metrics_by_category(self) -> dict:
        """Calculate performance metrics broken down by category."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as total,
                SUM(CASE WHEN final_resolution IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN direction_correct = 0 THEN 1 ELSE 0 END) as wrong,
                AVG(edge_at_signal) as avg_edge,
                AVG(CASE WHEN direction_correct = 1 THEN ai_probability END) as avg_prob_correct,
                AVG(CASE WHEN direction_correct = 0 THEN ai_probability END) as avg_prob_wrong
            FROM prediction_tracking
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY total DESC
        ''')
        
        results = {}
        for row in cursor.fetchall():
            category = row['category']
            resolved = row['resolved'] or 0
            correct = row['correct'] or 0
            
            results[category] = {
                'total': row['total'],
                'resolved': resolved,
                'correct': correct,
                'wrong': row['wrong'] or 0,
                'accuracy_pct': round((correct / resolved * 100) if resolved > 0 else 0, 2),
                'avg_edge': round(row['avg_edge'] or 0, 2),
                'avg_prob_when_correct': round(row['avg_prob_correct'] or 0, 3),
                'avg_prob_when_wrong': round(row['avg_prob_wrong'] or 0, 3)
            }
        
        conn.close()
        return results
    
    # =========================================================
    # STEP 4: Detect trends (improving/declining)
    # =========================================================
    def calculate_trend(self, days: int = 7) -> dict:
        """Calculate accuracy trend over recent days."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Get daily accuracy for last N days
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN direction_correct = 1 THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN direction_correct = 0 THEN 1 ELSE 0 END) as wrong
            FROM prediction_tracking
            WHERE final_resolution IS NOT NULL
            AND created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''', (f'-{days} days',))
        
        daily_data = []
        for row in cursor.fetchall():
            resolved = (row['correct'] or 0) + (row['wrong'] or 0)
            accuracy = (row['correct'] / resolved * 100) if resolved > 0 else 0
            daily_data.append({
                'date': row['date'],
                'total': row['total'],
                'correct': row['correct'] or 0,
                'accuracy': round(accuracy, 2)
            })
        
        conn.close()
        
        # Determine trend
        if len(daily_data) < 2:
            trend = 'insufficient_data'
        else:
            first_half = daily_data[:len(daily_data)//2]
            second_half = daily_data[len(daily_data)//2:]
            
            avg_first = sum(d['accuracy'] for d in first_half) / len(first_half) if first_half else 0
            avg_second = sum(d['accuracy'] for d in second_half) / len(second_half) if second_half else 0
            
            diff = avg_second - avg_first
            if diff > 5:
                trend = 'improving'
            elif diff < -5:
                trend = 'declining'
            else:
                trend = 'stable'
        
        return {
            'daily_data': daily_data,
            'trend': trend,
            'days_analyzed': days
        }
    
    # =========================================================
    # STEP 5: Identify weaknesses
    # =========================================================
    def identify_weaknesses(self) -> list:
        """Identify areas where agent is performing poorly."""
        weaknesses = []
        
        # Get metrics by category
        category_metrics = self.calculate_metrics_by_category()
        overall_metrics = self.calculate_overall_metrics()
        
        overall_accuracy = overall_metrics['accuracy_pct']
        
        for category, metrics in category_metrics.items():
            # Only analyze categories with enough data
            if metrics['resolved'] < 3:
                continue
            
            # Check if category accuracy is significantly below overall
            if metrics['accuracy_pct'] < overall_accuracy - 10:
                weaknesses.append({
                    'type': 'low_accuracy_category',
                    'category': category,
                    'accuracy': metrics['accuracy_pct'],
                    'vs_overall': round(metrics['accuracy_pct'] - overall_accuracy, 2),
                    'sample_size': metrics['resolved'],
                    'severity': 'high' if metrics['accuracy_pct'] < 30 else 'medium'
                })
            
            # Check for overconfidence (high probability predictions that are wrong)
            if metrics['avg_prob_when_wrong'] and metrics['avg_prob_when_wrong'] > 0.6:
                weaknesses.append({
                    'type': 'overconfidence',
                    'category': category,
                    'avg_prob_when_wrong': metrics['avg_prob_when_wrong'],
                    'severity': 'high' if metrics['avg_prob_when_wrong'] > 0.7 else 'medium'
                })
        
        # Check overall accuracy
        if overall_accuracy < 40 and overall_metrics['resolved'] >= 5:
            weaknesses.append({
                'type': 'overall_low_accuracy',
                'accuracy': overall_accuracy,
                'resolved': overall_metrics['resolved'],
                'severity': 'critical' if overall_accuracy < 30 else 'high'
            })
        
        return weaknesses
    
    # =========================================================
    # STEP 6: Generate self-awareness report
    # =========================================================
    def generate_report(self) -> dict:
        """Generate complete self-awareness report."""
        self._log('INFO', "Generating self-awareness report...")
        
        # Backfill categories first
        self.backfill_categories()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'overall': self.calculate_overall_metrics(),
            'by_category': self.calculate_metrics_by_category(),
            'trend': self.calculate_trend(days=7),
            'weaknesses': self.identify_weaknesses()
        }
        
        # Determine best and worst categories
        categories = report['by_category']
        if categories:
            valid_cats = {k: v for k, v in categories.items() if v['resolved'] >= 2}
            if valid_cats:
                report['best_category'] = max(valid_cats, key=lambda x: valid_cats[x]['accuracy_pct'])
                report['worst_category'] = min(valid_cats, key=lambda x: valid_cats[x]['accuracy_pct'])
        
        return report
    
    # =========================================================
    # STEP 7: Save metrics to database
    # =========================================================
    def save_daily_metrics(self):
        """Save today's metrics to agent_metrics table."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        report = self.generate_report()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO agent_metrics (
                date, total_predictions, total_resolved, total_correct,
                overall_accuracy, accuracy_trend, best_category, worst_category,
                brier_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            today,
            report['overall']['total_predictions'],
            report['overall']['resolved'],
            report['overall']['correct'],
            report['overall']['accuracy_pct'],
            report['trend']['trend'],
            report.get('best_category'),
            report.get('worst_category'),
            report['overall'].get('brier_score')
        ))
        
        # Save category metrics
        for category, metrics in report['by_category'].items():
            cursor.execute('''
                INSERT OR REPLACE INTO metrics_by_category (
                    date, category, total_predictions, resolved_count,
                    correct_count, wrong_count, accuracy_pct, avg_edge, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                today, category,
                metrics['total'], metrics['resolved'],
                metrics['correct'], metrics['wrong'],
                metrics['accuracy_pct'], metrics['avg_edge']
            ))
        
        conn.commit()
        conn.close()
        self._log('INFO', f"Saved metrics for {today}")


def print_report(report: dict):
    """Pretty print the self-awareness report."""
    print("\n" + "=" * 60)
    print("ORACLE SENTINEL - SELF AWARENESS REPORT")
    print("=" * 60)
    print(f"Generated: {report['generated_at']}")
    
    print("\n📊 OVERALL PERFORMANCE")
    print("-" * 40)
    o = report['overall']
    print(f"  Total Predictions: {o['total_predictions']}")
    print(f"  Resolved: {o['resolved']} | Pending: {o['pending']}")
    print(f"  Correct: {o['correct']} | Wrong: {o['wrong']}")
    print(f"  Accuracy: {o['accuracy_pct']}%")
    print(f"  Avg Edge: {o['avg_edge']}%")
    if o.get('brier_score'):
        print(f"  Brier Score: {o['brier_score']} (lower is better)")
    
    print("\n📈 TREND (Last 7 Days)")
    print("-" * 40)
    print(f"  Direction: {report['trend']['trend'].upper()}")
    
    print("\n📁 PERFORMANCE BY CATEGORY")
    print("-" * 40)
    for cat, m in report['by_category'].items():
        status = "✓" if m['accuracy_pct'] >= 50 else "✗"
        print(f"  [{status}] {cat:12} | Acc: {m['accuracy_pct']:5.1f}% | Resolved: {m['resolved']:3} | Edge: {m['avg_edge']:5.1f}%")
    
    if report.get('best_category'):
        print(f"\n  Best:  {report['best_category']}")
        print(f"  Worst: {report['worst_category']}")
    
    if report['weaknesses']:
        print("\n⚠️  IDENTIFIED WEAKNESSES")
        print("-" * 40)
        for w in report['weaknesses']:
            sev = "🔴" if w['severity'] == 'critical' else "🟠" if w['severity'] == 'high' else "🟡"
            if w['type'] == 'low_accuracy_category':
                print(f"  {sev} {w['category']}: {w['accuracy']}% accuracy ({w['vs_overall']:+.1f}% vs overall)")
            elif w['type'] == 'overconfidence':
                print(f"  {sev} {w['category']}: Overconfident (avg {w['avg_prob_when_wrong']:.0%} prob when wrong)")
            elif w['type'] == 'overall_low_accuracy':
                print(f"  {sev} Overall accuracy too low: {w['accuracy']}%")
    else:
        print("\n✅ No major weaknesses identified")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    awareness = SelfAwareness()
    report = awareness.generate_report()
    print_report(report)
    
    # Save to database
    awareness.save_daily_metrics()
