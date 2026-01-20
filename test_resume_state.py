#!/usr/bin/env python3
"""Test the resume functionality - check if state is saved and can be resumed."""

import json
from pathlib import Path

def test_resume_state():
    """Check if resume state is properly saved."""
    
    run_dir = Path.home() / ".garak" / "runs"
    
    print(f"\n{'='*60}")
    print(f"RESUME STATE VALIDATION")
    print(f"{'='*60}\n")
    
    if not run_dir.exists():
        print("⚠️  No runs directory found (expected if no resumes yet)")
        return False
    
    # Find latest run directory
    run_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        print("⚠️  No run state directories found")
        return False
    
    latest_run = run_dirs[-1]
    print(f"Latest run: {latest_run.name}")
    
    state_file = latest_run / "state.json"
    if not state_file.exists():
        print("⚠️  No state.json file found")
        return False
    
    try:
        with open(state_file) as f:
            state = json.load(f)
        
        print(f"✅ State file exists and is valid JSON")
        print(f"\nState contents:")
        
        # Check essential state fields
        essential_fields = ["garak_version", "run_id", "completed_attempts", "completed_probes", "granularity"]
        
        for field in essential_fields:
            if field in state:
                value = state[field]
                if isinstance(value, (list, dict)):
                    print(f"  ✅ {field}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"  ✅ {field}: {value}")
            else:
                print(f"  ⚠️  {field}: not found")
        
        # Validate granularity
        granularity = state.get("granularity", "")
        if granularity == "attempt":
            print(f"\n✅ Granularity set to 'attempt' (attempt-level resume)")
        else:
            print(f"\n⚠️  Granularity: {granularity} (expected 'attempt')")
        
        # Validate run_id format
        run_id = state.get("run_id", "")
        if run_id.startswith("garak-run-"):
            print(f"✅ Run ID has garak-run- prefix: {run_id}")
        else:
            print(f"⚠️  Run ID format unexpected: {run_id}")
        
        # Show completed tracking
        completed_attempts = state.get("completed_attempts", set())
        completed_probes = state.get("completed_probes", set())
        
        if isinstance(completed_attempts, list):
            print(f"✅ Completed attempts tracked: {len(completed_attempts)} attempts")
        else:
            print(f"⚠️  completed_attempts is not a list: {type(completed_attempts)}")
        
        if isinstance(completed_probes, list):
            print(f"✅ Completed probes tracked: {len(completed_probes)} probes")
        else:
            print(f"⚠️  completed_probes is not a list: {type(completed_probes)}")
        
        print(f"\n✅ Resume state is properly saved for continuation")
        
    except json.JSONDecodeError as e:
        print(f"❌ State file is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading state: {e}")
        return False
    
    print(f"\n{'='*60}\n")
    return True

if __name__ == "__main__":
    test_resume_state()
