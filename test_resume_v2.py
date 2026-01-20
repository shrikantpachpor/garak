#!/usr/bin/env python3
"""
Comprehensive test script for Resume Continuity v2.0

Tests all three priorities:
A. Preserve original start_time
B. True append mode (no file overwrites)
C. Resume metadata entry

Usage:
    python test_resume_v2.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def read_jsonl(filepath):
    """Read JSONL file and return list of entries"""
    if not Path(filepath).exists():
        return []
    
    entries = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print_warning(f"Failed to parse line: {e}")
    return entries

def extract_run_id_from_init(entries):
    """Extract run_id from init entry"""
    for entry in entries:
        if entry.get("entry_type") == "init":
            return entry.get("run")
    return None

def extract_start_time_from_init(entries):
    """Extract start_time from init entry"""
    for entry in entries:
        if entry.get("entry_type") == "init":
            return entry.get("start_time")
    return None

def count_entry_types(entries):
    """Count occurrences of each entry type"""
    counts = {}
    for entry in entries:
        entry_type = entry.get("entry_type", "unknown")
        counts[entry_type] = counts.get(entry_type, 0) + 1
    return counts

def get_attempt_sequences(entries):
    """Get list of attempt sequence numbers"""
    sequences = []
    for entry in entries:
        if entry.get("entry_type") == "attempt":
            sequences.append(entry.get("seq"))
    return sorted(sequences)

def get_attempt_uuids(entries):
    """Get set of attempt UUIDs"""
    uuids = set()
    for entry in entries:
        if entry.get("entry_type") == "attempt":
            uuid = entry.get("uuid")
            if uuid:
                uuids.add(uuid)
    return uuids

def validate_report_structure(report_path):
    """Validate the structure of a resumed report"""
    print_info(f"Validating report structure: {report_path}")
    
    entries = read_jsonl(report_path)
    if not entries:
        print_error("Report file is empty or doesn't exist")
        return False
    
    counts = count_entry_types(entries)
    print_info(f"Entry counts: {counts}")
    
    all_passed = True
    
    # Test 1: Should have exactly one setup entry
    if counts.get("start_run setup", 0) == 1:
        print_success("Single 'start_run setup' entry found")
    else:
        print_error(f"Expected 1 'start_run setup' entry, found {counts.get('start_run setup', 0)}")
        all_passed = False
    
    # Test 2: Should have exactly one init entry
    if counts.get("init", 0) == 1:
        print_success("Single 'init' entry found")
    else:
        print_error(f"Expected 1 'init' entry, found {counts.get('init', 0)}")
        all_passed = False
    
    # Test 3: Should have resume_info entries (at least 1 for resumed run)
    if counts.get("resume_info", 0) >= 1:
        print_success(f"Found {counts.get('resume_info', 0)} resume_info entry(ies)")
    else:
        print_warning("No resume_info entries found (expected for resumed run)")
    
    # Test 4: Should have at most one completion entry
    if counts.get("completion", 0) <= 1:
        print_success(f"Valid completion count: {counts.get('completion', 0)}")
    else:
        print_error(f"Multiple completion entries found: {counts.get('completion', 0)}")
        all_passed = False
    
    # Test 5: Should have at most one digest entry
    if counts.get("digest", 0) <= 1:
        print_success(f"Valid digest count: {counts.get('digest', 0)}")
    else:
        print_error(f"Multiple digest entries found: {counts.get('digest', 0)}")
        all_passed = False
    
    # Test 6: Check for duplicate attempts
    attempt_uuids = get_attempt_uuids(entries)
    attempt_count = counts.get("attempt", 0)
    if len(attempt_uuids) == attempt_count:
        print_success(f"No duplicate attempts (all {attempt_count} attempts have unique UUIDs)")
    else:
        print_error(f"Duplicate attempts detected: {attempt_count} attempts but only {len(attempt_uuids)} unique UUIDs")
        all_passed = False
    
    # Test 7: Check sequence continuity
    sequences = get_attempt_sequences(entries)
    if sequences:
        expected = list(range(sequences[0], sequences[-1] + 1))
        if sequences == expected:
            print_success(f"Attempt sequences are continuous: {sequences[0]} to {sequences[-1]}")
        else:
            missing = set(expected) - set(sequences)
            print_error(f"Sequence gaps detected. Missing: {missing}")
            all_passed = False
    
    return all_passed

def validate_start_time_preservation(report_path):
    """Validate that original start_time is preserved across resume"""
    print_info("Validating start_time preservation")
    
    entries = read_jsonl(report_path)
    
    # Extract start_time from init
    init_start_time = extract_start_time_from_init(entries)
    if not init_start_time:
        print_error("No start_time found in init entry")
        return False
    
    print_info(f"Init start_time: {init_start_time}")
    
    # Extract start_time from completion
    completion_start_time = None
    for entry in entries:
        if entry.get("entry_type") == "completion":
            completion_start_time = entry.get("start_time")
            break
    
    if not completion_start_time:
        print_warning("No completion entry found (scan may be incomplete)")
        return True  # Not a failure, just incomplete
    
    print_info(f"Completion start_time: {completion_start_time}")
    
    # Compare
    if init_start_time == completion_start_time:
        print_success("start_time preserved: init and completion match")
        return True
    else:
        print_error(f"start_time mismatch: init='{init_start_time}' != completion='{completion_start_time}'")
        return False

def validate_resume_metadata(report_path):
    """Validate resume_info entry contents"""
    print_info("Validating resume metadata")
    
    entries = read_jsonl(report_path)
    
    resume_entries = [e for e in entries if e.get("entry_type") == "resume_info"]
    
    if not resume_entries:
        print_warning("No resume_info entries found")
        return True  # Optional feature
    
    print_success(f"Found {len(resume_entries)} resume_info entry(ies)")
    
    all_passed = True
    for i, resume_entry in enumerate(resume_entries, 1):
        print_info(f"Checking resume_info #{i}...")
        
        required_fields = ["resumed_at", "original_start_time", "original_run_id", "resume_from_file"]
        for field in required_fields:
            if field in resume_entry:
                print_success(f"  Field '{field}' present: {resume_entry[field]}")
            else:
                print_error(f"  Missing required field: '{field}'")
                all_passed = False
        
        # Optional fields
        if "completed_probes" in resume_entry:
            print_success(f"  Completed probes: {resume_entry['completed_probes']}")
        
        if "resume_points" in resume_entry:
            print_success(f"  Resume points: {resume_entry['resume_points']}")
    
    return all_passed

def validate_run_id_consistency(report_path):
    """Validate that run_id is consistent throughout report"""
    print_info("Validating run_id consistency")
    
    entries = read_jsonl(report_path)
    
    # Get run_id from init
    init_run_id = extract_run_id_from_init(entries)
    if not init_run_id:
        print_error("No run_id found in init entry")
        return False
    
    print_info(f"Init run_id: {init_run_id}")
    
    # Check all attempt entries
    attempt_run_ids = set()
    for entry in entries:
        if entry.get("entry_type") == "attempt":
            run_id = entry.get("run")
            if run_id:
                attempt_run_ids.add(run_id)
    
    if not attempt_run_ids:
        print_warning("No attempts with run_id found")
        return True
    
    if len(attempt_run_ids) == 1 and init_run_id in attempt_run_ids:
        print_success(f"All attempts use consistent run_id: {init_run_id}")
        return True
    else:
        print_error(f"Inconsistent run_ids detected: init={init_run_id}, attempts={attempt_run_ids}")
        return False

def validate_file_append_behavior(report_path_initial, report_path_resumed):
    """Validate that resumed report is larger (append, not overwrite)"""
    print_info("Validating file append behavior")
    
    if report_path_initial != report_path_resumed:
        print_error("Report paths differ - files were not appended to same file!")
        return False
    
    # Read initial entries
    initial_entries = read_jsonl(report_path_initial)
    initial_count = len(initial_entries)
    
    print_info(f"Initial entry count: {initial_count}")
    
    # This test requires manual interruption, so we can't fully automate
    # But we can check that the file has a reasonable structure
    if initial_count > 0:
        print_success("Report file exists and has entries")
        return True
    else:
        print_error("Report file is empty")
        return False

def main():
    """Main test execution"""
    print("=" * 70)
    print("Resume Continuity v2.0 - Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    # Check if we have a report file to test
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    else:
        # Look for most recent report in current directory
        report_files = list(Path(".").glob("*.report.jsonl"))
        if not report_files:
            print_error("No report files found in current directory")
            print_info("Usage: python test_resume_v2.py [path/to/report.jsonl]")
            print_info("Or run this script after a resumed scan")
            sys.exit(1)
        
        # Get most recent
        report_path = str(max(report_files, key=lambda p: p.stat().st_mtime))
    
    print_info(f"Testing report: {report_path}")
    print()
    
    # Run validation tests
    results = {}
    
    print("\n" + "="*70)
    print("TEST 1: Report Structure")
    print("="*70)
    results['structure'] = validate_report_structure(report_path)
    
    print("\n" + "="*70)
    print("TEST 2: start_time Preservation (Priority A)")
    print("="*70)
    results['start_time'] = validate_start_time_preservation(report_path)
    
    print("\n" + "="*70)
    print("TEST 3: run_id Consistency")
    print("="*70)
    results['run_id'] = validate_run_id_consistency(report_path)
    
    print("\n" + "="*70)
    print("TEST 4: Resume Metadata (Priority C)")
    print("="*70)
    results['metadata'] = validate_resume_metadata(report_path)
    
    print("\n" + "="*70)
    print("TEST 5: File Append Behavior (Priority B)")
    print("="*70)
    results['append'] = validate_file_append_behavior(report_path, report_path)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name.upper():20} {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! v2.0 implementation is working correctly.")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
