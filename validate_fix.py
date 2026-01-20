#!/usr/bin/env python3
"""Validate that the critical fix is working correctly."""

import json
import sys
from pathlib import Path

def check_setup_entry():
    """Check if setup entry has all 48 fields with correct resume parameters."""
    
    # Paths
    report_path = Path.home() / ".local" / "share" / "garak" / "garak_reports" / "garak_run.report.jsonl"
    original_path = Path("garak_run_original.report.jsonl")
    
    if not report_path.exists():
        print("❌ No report file found. Run a scan first.")
        return False
    
    # Read reports
    try:
        with open(report_path) as f:
            modified_setup = json.loads(f.readline())
        
        if original_path.exists():
            with open(original_path) as f:
                original_setup = json.loads(f.readline())
        else:
            print("⚠️  No original report for comparison")
            original_setup = None
    except Exception as e:
        print(f"❌ Error reading reports: {e}")
        return False
    
    # Get setup entry field count
    modified_fields = set(modified_setup.keys())
    modified_count = len(modified_fields)
    
    print(f"\n{'='*60}")
    print(f"SETUP ENTRY VALIDATION")
    print(f"{'='*60}")
    
    # Check field count
    if modified_count == 48:
        print(f"✅ Field count: {modified_count} (expected 48)")
    else:
        print(f"❌ Field count: {modified_count} (expected 48)")
        return False
    
    # Check critical fields
    critical_fields = {
        "run.resumable": (True, bool),
        "run.resume_granularity": ("attempt", str),
        "transient.run_id": (None, str),  # UUID format expected
        "plugins.target_type": ("rest", str),
        "plugins.target_name": ("RestGenerator", str),
    }
    
    all_ok = True
    for field, (expected, field_type) in critical_fields.items():
        value = modified_setup.get(field)
        actual_type = type(value)
        
        if field == "transient.run_id":
            # Check UUID format (36 chars)
            if isinstance(value, str) and len(value) == 36 and value.count('-') == 4:
                print(f"✅ {field}: {value} (UUID format)")
            else:
                print(f"❌ {field}: {value} (not UUID format)")
                all_ok = False
        elif value == expected and actual_type == field_type:
            print(f"✅ {field}: {value}")
        else:
            print(f"❌ {field}: {value} (expected {expected})")
            all_ok = False
    
    # Check run_params list
    run_params = modified_setup.get("_config.run_params", [])
    if isinstance(run_params, list):
        has_resumable = "resumable" in run_params
        has_resume_gran = "resume_granularity" in run_params
        
        if not has_resumable and not has_resume_gran:
            print(f"✅ _config.run_params: {run_params} (no resume params)")
        else:
            print(f"❌ _config.run_params: Contains resume params!")
            all_ok = False
    else:
        print(f"❌ _config.run_params: Not a list!")
        all_ok = False
    
    # Compare with original if available
    if original_setup:
        print(f"\n{'='*60}")
        print(f"COMPARISON WITH ORIGINAL")
        print(f"{'='*60}")
        
        original_fields = set(original_setup.keys())
        original_count = len(original_fields)
        
        print(f"Original field count: {original_count}")
        print(f"Modified field count: {modified_count}")
        
        if original_count == modified_count:
            print(f"✅ Field counts match!")
        else:
            print(f"❌ Field counts don't match!")
            all_ok = False
        
        # Find differences
        missing_in_modified = original_fields - modified_fields
        extra_in_modified = modified_fields - original_fields
        
        if missing_in_modified:
            print(f"❌ Missing in modified: {missing_in_modified}")
            all_ok = False
        
        if extra_in_modified:
            print(f"❌ Extra in modified: {extra_in_modified}")
            all_ok = False
        
        if not missing_in_modified and not extra_in_modified:
            print(f"✅ Field names match perfectly!")
        
        # Check resume field values in original
        orig_resumable = original_setup.get("run.resumable")
        orig_granularity = original_setup.get("run.resume_granularity")
        
        print(f"\nOriginal resume settings:")
        print(f"  run.resumable: {orig_resumable}")
        print(f"  run.resume_granularity: {orig_granularity}")
        
        print(f"\nModified resume settings:")
        print(f"  run.resumable: {modified_setup.get('run.resumable')}")
        print(f"  run.resume_granularity: {modified_setup.get('run.resume_granularity')}")
        
        # Check original run_params
        orig_run_params = original_setup.get("_config.run_params", [])
        if "resumable" not in orig_run_params and "resume_granularity" not in orig_run_params:
            print(f"✅ Original also excludes resume params from list")
        else:
            print(f"⚠️  Original has resume params in list?")
    
    print(f"\n{'='*60}")
    if all_ok:
        print(f"✅ CRITICAL FIX VALIDATION: PASSED")
    else:
        print(f"❌ CRITICAL FIX VALIDATION: FAILED")
    print(f"{'='*60}\n")
    
    return all_ok

if __name__ == "__main__":
    success = check_setup_entry()
    sys.exit(0 if success else 1)
