#!/usr/bin/env python3
"""Validate attempt entries and hitlog structure."""

import json
from pathlib import Path

def validate_attempts():
    """Validate attempt entry structure."""
    
    report_path = Path.home() / ".local" / "share" / "garak" / "garak_reports" / "garak_run.report.jsonl"
    original_path = Path("garak_run_original.report.jsonl")
    
    if not report_path.exists():
        print("❌ No report file found")
        return False
    
    print(f"\n{'='*60}")
    print(f"ATTEMPT ENTRIES VALIDATION")
    print(f"{'='*60}\n")
    
    # Read and analyze modified report
    attempts_modified = []
    with open(report_path) as f:
        f.readline()  # skip setup
        f.readline()  # skip init
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("entry_type") == "attempt":
                    attempts_modified.append(entry)
            except:
                break
    
    print(f"Modified report: {len(attempts_modified)} attempts")
    
    if attempts_modified:
        # Validate first attempt structure
        first = attempts_modified[0]
        required_fields = [
            "uuid", "seq", "status", "probe_classname", "prompt",
            "outputs", "detector_results"
        ]
        
        missing = [f for f in required_fields if f not in first]
        if missing:
            print(f"❌ Missing fields in attempt: {missing}")
            return False
        else:
            print(f"✅ Attempt structure complete")
        
        # Check UUID format
        if len(first.get("uuid", "")) == 36 and first["uuid"].count("-") == 4:
            print(f"✅ Attempt UUID format correct: {first['uuid']}")
        else:
            print(f"❌ Attempt UUID format incorrect: {first['uuid']}")
            return False
    
    # Read and analyze original report
    if original_path.exists():
        attempts_original = []
        with open(original_path) as f:
            f.readline()  # skip setup
            f.readline()  # skip init
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("entry_type") == "attempt":
                        attempts_original.append(entry)
                except:
                    break
        
        print(f"Original report: {len(attempts_original)} attempts")
        
        if attempts_modified and attempts_original:
            # Compare first attempt structure
            orig_keys = set(attempts_original[0].keys())
            mod_keys = set(attempts_modified[0].keys())
            
            if orig_keys == mod_keys:
                print(f"✅ Attempt field structure matches original")
            else:
                missing = orig_keys - mod_keys
                extra = mod_keys - orig_keys
                if missing:
                    print(f"❌ Missing in modified: {missing}")
                if extra:
                    print(f"❌ Extra in modified: {extra}")
                return False
    
    print(f"\n{'='*60}")
    print(f"✅ ATTEMPT ENTRIES VALIDATION: PASSED")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    validate_attempts()
