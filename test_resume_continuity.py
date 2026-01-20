#!/usr/bin/env python3
"""
Test script to verify resume continuity functionality.

This script tests that resumed scans produce reports identical to
continuous scans in terms of run_id, timestamps, and structure.

Usage:
    python test_resume_continuity.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def parse_report_jsonl(report_path):
    """Parse a report JSONL file and extract key metadata."""
    if not os.path.exists(report_path):
        return None
    
    report_data = {
        'setup': None,
        'init': None,
        'attempts': [],
        'completion': None,
        'digest': None
    }
    
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line.strip())
                entry_type = entry.get('entry_type')
                
                if entry_type == 'start_run setup':
                    report_data['setup'] = entry
                elif entry_type == 'init':
                    report_data['init'] = entry
                elif entry_type == 'attempt':
                    report_data['attempts'].append(entry)
                elif entry_type == 'completion':
                    report_data['completion'] = entry
                elif entry_type == 'digest':
                    report_data['digest'] = entry
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line: {e}")
    
    return report_data


def parse_hitlog_jsonl(hitlog_path):
    """Parse a hitlog JSONL file."""
    if not os.path.exists(hitlog_path):
        return []
    
    hits = []
    with open(hitlog_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                hit = json.loads(line.strip())
                hits.append(hit)
            except json.JSONDecodeError:
                pass
    
    return hits


def test_resume_continuity():
    """Main test function."""
    print("=" * 70)
    print("RESUME CONTINUITY TEST")
    print("=" * 70)
    print()
    
    # Configuration
    test_dir = Path("test_resume_output")
    test_dir.mkdir(exist_ok=True)
    
    report_prefix = "test_resume"
    report_path = test_dir / f"{report_prefix}.report.jsonl"
    hitlog_path = test_dir / f"{report_prefix}.hitlog.jsonl"
    html_path = test_dir / f"{report_prefix}.report.html"
    
    # Clean up previous test files
    for path in [report_path, hitlog_path, html_path]:
        if path.exists():
            path.unlink()
            print(f"Cleaned up: {path}")
    
    print()
    print("Step 1: Run partial scan (will be interrupted)")
    print("-" * 70)
    
    # Start a scan that we'll interrupt
    cmd = [
        sys.executable, "-m", "garak",
        "-m", "test",
        "-p", "av_spam_scanning.EICAR,av_spam_scanning.GTUBE",
        "--report_prefix", report_prefix,
        "--report_dir", str(test_dir),
        "--resumable"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        # Run for a few seconds then interrupt
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(5)  # Let EICAR probe complete
        proc.terminate()
        proc.wait(timeout=5)
        print("✓ Interrupted scan after ~5 seconds")
    except subprocess.TimeoutExpired:
        proc.kill()
        print("✓ Force-killed scan")
    except Exception as e:
        print(f"✗ Error during initial scan: {e}")
        return False
    
    print()
    
    # Parse initial report
    initial_data = parse_report_jsonl(report_path)
    if not initial_data or not initial_data['init']:
        print("✗ Could not parse initial report")
        return False
    
    initial_run_id = initial_data['init']['run']
    initial_start_time = initial_data['init']['start_time']
    initial_attempt_count = len(initial_data['attempts'])
    
    print(f"Initial report metadata:")
    print(f"  Run ID: {initial_run_id}")
    print(f"  Start time: {initial_start_time}")
    print(f"  Attempts: {initial_attempt_count}")
    print()
    
    # Extract run_id for resume (it might be in state format)
    # Look for the resume run_id in ~/.garak/runs/
    garak_runs_dir = Path.home() / ".garak" / "runs"
    if garak_runs_dir.exists():
        # Find the most recent run directory
        run_dirs = sorted([d for d in garak_runs_dir.iterdir() if d.is_dir()], 
                         key=lambda x: x.stat().st_mtime, reverse=True)
        if run_dirs:
            resume_run_id = run_dirs[0].name
            print(f"Resume run ID: {resume_run_id}")
        else:
            print("✗ No resume state found")
            return False
    else:
        print("✗ No .garak/runs directory found")
        return False
    
    print()
    print("Step 2: Resume the scan")
    print("-" * 70)
    
    # Resume the scan
    cmd_resume = [
        sys.executable, "-m", "garak",
        "--resume", resume_run_id
    ]
    
    print(f"Command: {' '.join(cmd_resume)}")
    print()
    
    try:
        result = subprocess.run(cmd_resume, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Resume completed successfully")
        else:
            print(f"✗ Resume failed with code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Resume timed out")
        return False
    except Exception as e:
        print(f"✗ Error during resume: {e}")
        return False
    
    print()
    print("Step 3: Verify report continuity")
    print("-" * 70)
    
    # Parse final report
    final_data = parse_report_jsonl(report_path)
    final_hits = parse_hitlog_jsonl(hitlog_path)
    
    if not final_data or not final_data['init']:
        print("✗ Could not parse final report")
        return False
    
    final_run_id = final_data['init']['run']
    final_start_time = final_data['init']['start_time']
    final_attempt_count = len(final_data['attempts'])
    
    print(f"Final report metadata:")
    print(f"  Run ID: {final_run_id}")
    print(f"  Start time: {final_start_time}")
    print(f"  Attempts: {final_attempt_count}")
    print(f"  Hitlog entries: {len(final_hits)}")
    print()
    
    # Validation checks
    all_passed = True
    
    # Check 1: Run ID consistency
    if final_run_id == initial_run_id:
        print("✓ Run ID preserved across resume")
    else:
        print(f"✗ Run ID changed: {initial_run_id} → {final_run_id}")
        all_passed = False
    
    # Check 2: Start time preserved
    if final_start_time == initial_start_time:
        print("✓ Start time preserved across resume")
    else:
        print(f"✗ Start time changed: {initial_start_time} → {final_start_time}")
        all_passed = False
    
    # Check 3: No duplicate attempts
    attempt_uuids = [a['uuid'] for a in final_data['attempts']]
    if len(attempt_uuids) == len(set(attempt_uuids)):
        print("✓ No duplicate attempts")
    else:
        print(f"✗ Found duplicate attempts")
        all_passed = False
    
    # Check 4: Attempts increased (resume added new ones)
    if final_attempt_count > initial_attempt_count:
        print(f"✓ New attempts added: {initial_attempt_count} → {final_attempt_count}")
    else:
        print(f"✗ No new attempts added")
        all_passed = False
    
    # Check 5: Hitlog run_id consistency
    hitlog_run_ids = set(hit['run_id'] for hit in final_hits)
    if len(hitlog_run_ids) == 1 and hitlog_run_ids.pop() == final_run_id:
        print("✓ Hitlog run_id consistent")
    else:
        print(f"✗ Hitlog has inconsistent run_ids: {hitlog_run_ids}")
        all_passed = False
    
    # Check 6: Completion entry exists with correct timestamps
    if final_data['completion']:
        completion = final_data['completion']
        if 'start_time' in completion and completion['start_time'] == initial_start_time:
            print("✓ Completion entry has correct start_time")
        else:
            print(f"✗ Completion entry has wrong start_time")
            all_passed = False
        
        if 'end_time' in completion:
            print(f"✓ Completion entry has end_time: {completion['end_time']}")
        else:
            print("✗ Completion entry missing end_time")
            all_passed = False
    else:
        print("✗ No completion entry found")
        all_passed = False
    
    # Check 7: Only one digest entry
    # Count digest entries by parsing file directly
    digest_count = 0
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '"entry_type": "digest"' in line or '"entry_type":"digest"' in line:
                digest_count += 1
    
    if digest_count == 1:
        print("✓ Exactly one digest entry")
    else:
        print(f"✗ Found {digest_count} digest entries (expected 1)")
        all_passed = False
    
    # Check 8: HTML report generated
    if html_path.exists():
        print("✓ HTML report generated")
    else:
        print("✗ HTML report not generated")
        all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Resume continuity working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = test_resume_continuity()
    sys.exit(0 if success else 1)
