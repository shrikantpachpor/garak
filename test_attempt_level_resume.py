#!/usr/bin/env python3
"""Test script to verify attempt-level resume functionality.

This script:
1. Starts a resumable scan with attempt-level granularity
2. Lets it run for a few attempts
3. Checks that attempts are being marked as complete in the state
4. Verifies resume state is saved correctly
"""

import subprocess
import time
import json
import sys
from pathlib import Path

def test_attempt_level_resume():
    """Test that attempt-level resume tracking works correctly."""
    
    print("=" * 60)
    print("Testing Attempt-Level Resume Functionality")
    print("=" * 60)
    
    # Clean up any existing test run
    test_prefix = "attempt_level_test"
    run_state_dir = Path.home() / ".garak" / "runs"
    
    print(f"\n1. Cleaning up any existing test runs...")
    if run_state_dir.exists():
        for run_dir in run_state_dir.glob("*attempt_level_test*"):
            print(f"   Deleting old run: {run_dir.name}")
            import shutil
            shutil.rmtree(run_dir, ignore_errors=True)
    
    # Start a small resumable scan with attempt-level granularity
    print(f"\n2. Starting resumable scan with attempt-level granularity...")
    print(f"   Command: python -m garak -m test -p test.Blank --resumable --resume_granularity attempt --report_prefix {test_prefix} --generations 5")
    
    process = subprocess.Popen(
        [
            sys.executable, "-m", "garak",
            "-m", "test",
            "-p", "test.Blank",
            "--resumable",
            "--resume_granularity", "attempt",
            "--report_prefix", test_prefix,
            "--generations", "5"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Let it run for a few seconds to generate some attempts
    print(f"\n3. Letting scan run for 8 seconds to generate attempts...")
    time.sleep(8)
    
    # Interrupt the scan
    print(f"\n4. Interrupting scan with Ctrl+C...")
    process.terminate()
    try:
        stdout, stderr = process.communicate(timeout=5)
        print(f"   Scan interrupted")
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        print(f"   Scan killed (timeout)")
    
    # Check that state was saved
    print(f"\n5. Checking saved state...")
    
    # Find the run directory
    run_dirs = list(run_state_dir.glob(f"*{test_prefix}*"))
    if not run_dirs:
        print("   ❌ ERROR: No run state directory found!")
        print(f"   Expected directory matching: *{test_prefix}*")
        print(f"   Searched in: {run_state_dir}")
        return False
    
    run_dir = run_dirs[0]
    state_file = run_dir / "state.json"
    
    if not state_file.exists():
        print(f"   ❌ ERROR: State file not found: {state_file}")
        return False
    
    print(f"   ✅ State file found: {state_file}")
    
    # Load and check state
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    print(f"\n6. Analyzing state contents...")
    print(f"   Granularity: {state.get('resume_granularity', 'NOT SET')}")
    print(f"   Total probes: {len(state.get('probes', []))}")
    
    completed_attempts = state.get('completed_attempts', [])
    if isinstance(completed_attempts, set):
        completed_attempts = list(completed_attempts)
    
    print(f"   Completed attempts: {len(completed_attempts)}")
    
    # Check key requirements
    success = True
    
    # Check granularity is set to "attempt"
    if state.get('resume_granularity') != 'attempt':
        print(f"\n   ❌ FAIL: resume_granularity is '{state.get('resume_granularity')}', expected 'attempt'")
        success = False
    else:
        print(f"\n   ✅ PASS: resume_granularity is 'attempt'")
    
    # Check that attempts were tracked
    if len(completed_attempts) == 0:
        print(f"   ❌ FAIL: No attempts were marked as complete")
        print(f"   This means mark_attempt_complete() is not being called!")
        success = False
    else:
        print(f"   ✅ PASS: {len(completed_attempts)} attempts were marked as complete")
        print(f"   First few attempt UUIDs: {completed_attempts[:3]}")
    
    # Check probe state
    probe_states = state.get('probe_states', {})
    print(f"\n   Probe states tracked: {len(probe_states)}")
    for probe_name, probe_state in probe_states.items():
        total = probe_state.get('total_prompts', 0)
        completed = probe_state.get('prompt_index', -1) + 1
        print(f"   - {probe_name}: {completed}/{total} attempts completed")
    
    # Check report was generated
    print(f"\n7. Checking report file...")
    report_file = Path(f"{test_prefix}.report.jsonl")
    if not report_file.exists():
        print(f"   ❌ WARNING: Report file not found: {report_file}")
    else:
        print(f"   ✅ Report file exists: {report_file}")
        
        # Count attempts in report
        attempt_count = 0
        with open(report_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('entry_type') == 'attempt':
                        attempt_count += 1
                except:
                    pass
        print(f"   Attempts in report: {attempt_count}")
    
    # Final verdict
    print(f"\n{'=' * 60}")
    if success:
        print("✅ TEST PASSED: Attempt-level resume tracking is working!")
        print(f"\nYou can now resume this scan with:")
        print(f"  python -m garak --resume {run_dir.name}")
    else:
        print("❌ TEST FAILED: Attempt-level tracking is NOT working correctly")
        print("\nThe issue is likely that probewise.py is not calling")
        print("resumeservice.mark_attempt_complete() after each attempt.")
    print(f"{'=' * 60}")
    
    return success


if __name__ == "__main__":
    success = test_attempt_level_resume()
    sys.exit(0 if success else 1)
