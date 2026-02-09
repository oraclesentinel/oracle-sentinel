#!/usr/bin/env python3
"""
Self-Improvement Cron Runner
Run this daily/weekly to make Oracle Sentinel improve itself.

Usage:
  python3 run_self_improvement.py           # Full cycle
  python3 run_self_improvement.py --report  # Just show report
  python3 run_self_improvement.py --apply   # Apply pending fixes
"""

import sys
import os
from datetime import datetime

# Ensure we can import from scripts directory
sys.path.insert(0, os.path.dirname(__file__))

from self_awareness import SelfAwareness, print_report
from error_analyzer import ErrorAnalyzer
from self_diagnosis import SelfDiagnosis
from self_improvement import SelfImprovement


def log(message):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {message}")


def run_full_cycle():
    """Run complete self-improvement cycle."""
    log("=" * 60)
    log("🧠 ORACLE SENTINEL - SELF-IMPROVEMENT CYCLE")
    log("=" * 60)
    
    # Step 1: Self-Awareness Report
    log("\n📊 STEP 1: Generating self-awareness report...")
    awareness = SelfAwareness()
    report = awareness.generate_report()
    print_report(report)
    awareness.save_daily_metrics()
    
    # Step 2: Error Analysis
    log("\n🔍 STEP 2: Analyzing errors...")
    error_analyzer = ErrorAnalyzer()
    error_results = error_analyzer.analyze_all_errors()
    if error_results:
        log(f"   Analyzed {len(error_results)} new errors")
    else:
        log("   No new errors to analyze")
    error_analyzer.print_report()
    
    # Step 3: Self-Diagnosis
    log("\n🩺 STEP 3: Running self-diagnosis...")
    diagnosis = SelfDiagnosis()
    proposals = diagnosis.diagnose()
    if proposals:
        log(f"   Generated {len(proposals)} improvement proposals")
        diagnosis.save_proposals(proposals)
        diagnosis.print_diagnosis(proposals)
    else:
        log("   No issues diagnosed")
    
    # Step 4: Apply Improvements
    log("\n🔧 STEP 4: Applying improvements...")
    improvement = SelfImprovement()
    results = improvement.apply_all_pending()
    log(f"   Applied: {results['applied']} | Failed: {results['failed']}")
    
    # Step 5: Show final config
    log("\n⚙️ STEP 5: Current configuration...")
    improvement.print_config()
    
    # Summary
    log("\n" + "=" * 60)
    log("✅ SELF-IMPROVEMENT CYCLE COMPLETE")
    log("=" * 60)
    
    return {
        'report': report,
        'errors_analyzed': len(error_results) if error_results else 0,
        'proposals': len(proposals) if proposals else 0,
        'applied': results['applied'],
        'failed': results['failed']
    }


def show_report_only():
    """Just show self-awareness report without applying fixes."""
    log("📊 ORACLE SENTINEL - SELF-AWARENESS REPORT")
    
    awareness = SelfAwareness()
    report = awareness.generate_report()
    print_report(report)
    
    error_analyzer = ErrorAnalyzer()
    error_analyzer.print_report()
    
    improvement = SelfImprovement()
    improvement.print_config()


def apply_only():
    """Apply pending fixes without running full diagnosis."""
    log("🔧 ORACLE SENTINEL - APPLYING PENDING FIXES")
    
    improvement = SelfImprovement()
    
    pending = improvement.diagnosis.get_pending_proposals()
    if not pending:
        log("No pending proposals to apply")
        return
    
    log(f"Found {len(pending)} pending proposals")
    results = improvement.apply_all_pending()
    log(f"Applied: {results['applied']} | Failed: {results['failed']}")
    
    improvement.print_config()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--report':
            show_report_only()
        elif sys.argv[1] == '--apply':
            apply_only()
        elif sys.argv[1] == '--help':
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print(__doc__)
    else:
        run_full_cycle()
