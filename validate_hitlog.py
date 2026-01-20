#!/usr/bin/env python3
"""Validate hitlog structure and run_id format."""

import json
from pathlib import Path

def validate_hitlog():
    """Validate hitlog entries if they exist."""
    
    hitlog_path = Path.home() / ".local" / "share" / "garak" / "garak_reports" / "garak_run.hitlog.jsonl"
    original_hitlog_path = Path("garak_run_original.hitlog.jsonl")
    
    print(f"\n{'='*60}")
    print(f"HITLOG VALIDATION")
    print(f"{'='*60}\n")
    
    # Check modified hitlog
    if hitlog_path.exists():
        hitlog_entries = []
        with open(hitlog_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    hitlog_entries.append(entry)
                except:
                    break
        
        print(f"Modified hitlog: {len(hitlog_entries)} entries")
        
        if hitlog_entries:
            # Validate first entry structure
            first = hitlog_entries[0]
            required_fields = ["run", "attempt_id", "seq", "prompt", "detector", "detector_name"]
            
            missing = [f for f in required_fields if f not in first]
            if missing:
                print(f"⚠️  Missing fields in hitlog entry: {missing}")
            else:
                print(f"✅ Hitlog entry structure complete")
            
            # Check run_id format
            run_id = first.get("run", "")
            if len(run_id) == 36 and run_id.count("-") == 4:
                print(f"✅ Hitlog run_id is UUID format: {run_id}")
            else:
                print(f"❌ Hitlog run_id is not UUID format: {run_id}")
            
            # Check generator format if present
            if "generator" in first:
                gen = first["generator"]
                if gen == "rest RestGenerator":
                    print(f"✅ Generator format correct: {gen}")
                else:
                    print(f"❌ Generator format incorrect: {gen}")
    else:
        print("⚠️  No hitlog file yet (detectors haven't run)")
    
    # Check original hitlog
    if original_hitlog_path.exists():
        hitlog_entries_orig = []
        with open(original_hitlog_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    hitlog_entries_orig.append(entry)
                except:
                    break
        
        print(f"Original hitlog: {len(hitlog_entries_orig)} entries")
        
        if hitlog_entries_orig:
            first_orig = hitlog_entries_orig[0]
            orig_keys = set(first_orig.keys())
            
            print(f"\nOriginal hitlog entry fields: {sorted(orig_keys)}")
            
            if hitlog_entries:
                first_mod = hitlog_entries[0]
                mod_keys = set(first_mod.keys())
                
                print(f"Modified hitlog entry fields: {sorted(mod_keys)}")
                
                if orig_keys == mod_keys:
                    print(f"✅ Hitlog field structure matches original")
                else:
                    missing = orig_keys - mod_keys
                    extra = mod_keys - orig_keys
                    if missing:
                        print(f"❌ Missing in modified: {missing}")
                    if extra:
                        print(f"❌ Extra in modified: {extra}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    validate_hitlog()
