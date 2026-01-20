#!/usr/bin/env python3
"""
Quick validation script to verify resume continuity implementation.

This script checks that all necessary code changes are in place.
Run this BEFORE testing to ensure implementation is complete.

Usage:
    python validate_implementation.py
"""

import os
import sys
from pathlib import Path


def check_file_contains(filepath, patterns, description):
    """Check if a file contains all specified patterns."""
    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for pattern in patterns:
        if pattern in content:
            print(f"  ✓ Found: {description} - {pattern[:50]}...")
        else:
            print(f"  ✗ Missing: {description} - {pattern[:50]}...")
            all_found = False
    
    return all_found


def validate_implementation():
    """Validate that all code changes are present."""
    print("=" * 70)
    print("RESUME CONTINUITY IMPLEMENTATION VALIDATION")
    print("=" * 70)
    print()
    
    all_valid = True
    
    # Check 1: cli.py changes
    print("📋 Checking cli.py changes...")
    cli_patterns = [
        "def parse_existing_report_metadata(report_path):",
        "original_run_id, original_start_time = parse_existing_report_metadata",
        "_config.transient.original_start_time = original_start_time",
    ]
    valid = check_file_contains(
        "garak/cli.py", 
        cli_patterns, 
        "cli.py metadata parsing"
    )
    all_valid = all_valid and valid
    print()
    
    # Check 2: command.py changes
    print("📋 Checking command.py changes...")
    command_patterns = [
        "def remove_trailing_metadata_entries(report_path):",
        "if is_resuming:",
        '"start_time": start_time,',
        'with open(report_filename, "r+", encoding="utf-8") as reportfile:',
    ]
    valid = check_file_contains(
        "garak/command.py", 
        command_patterns, 
        "command.py cleanup logic"
    )
    all_valid = all_valid and valid
    print()
    
    # Check 3: report_digest.py changes
    print("📋 Checking report_digest.py changes...")
    digest_patterns = [
        "if object.get('entry_type') == 'digest':",
        "reportfile.truncate()",
        'if entry.get(\'entry_type\') not in (\'digest\', \'completion\'):',
    ]
    valid = check_file_contains(
        "garak/analyze/report_digest.py", 
        digest_patterns, 
        "report_digest.py replacement logic"
    )
    all_valid = all_valid and valid
    print()
    
    # Check 4: resumeservice.py changes
    print("📋 Checking resumeservice.py changes...")
    resume_patterns = [
        "_config.transient.original_start_time",
        "original_start_time = (",
    ]
    valid = check_file_contains(
        "garak/resumeservice.py", 
        resume_patterns, 
        "resumeservice.py start_time preservation"
    )
    all_valid = all_valid and valid
    print()
    
    # Check 5: Documentation files
    print("📋 Checking documentation files...")
    docs = [
        "RESUME_CONTINUITY_IMPLEMENTATION.md",
        "RESUME_CONTINUITY_GUIDE.md",
        "RESUME_CONTINUITY_CHANGES.md",
        "RESUME_CONTINUITY_SUMMARY.md",
        "test_resume_continuity.py",
    ]
    
    for doc in docs:
        if os.path.exists(doc):
            print(f"  ✓ Found: {doc}")
        else:
            print(f"  ✗ Missing: {doc}")
            all_valid = False
    print()
    
    # Summary
    print("=" * 70)
    if all_valid:
        print("✅ VALIDATION PASSED")
        print()
        print("All code changes and documentation are in place.")
        print("You can now proceed to testing:")
        print()
        print("  1. Run automated test:")
        print("     python test_resume_continuity.py")
        print()
        print("  2. Or run manual test:")
        print("     python -m garak -m test -p av_spam_scanning --resumable")
    else:
        print("❌ VALIDATION FAILED")
        print()
        print("Some required changes are missing. Please review:")
        print("  - RESUME_CONTINUITY_CHANGES.md for code diffs")
        print("  - RESUME_CONTINUITY_GUIDE.md for implementation details")
    print("=" * 70)
    
    return all_valid


if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)
