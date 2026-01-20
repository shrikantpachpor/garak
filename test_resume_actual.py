"""
Test resume with actual REST API to see what's happening
"""
import subprocess
import sys
import time
import json
from pathlib import Path

print("Starting scan - will interrupt after 3 attempts...")
print("="*80)

# Start scan
proc = subprocess.Popen(
    [sys.executable, "-m", "garak", "--config", "garak-config.yaml"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

run_id = None
attempt_count = 0

for line in iter(proc.stdout.readline, ''):
    print(line, end='')
    
    if "Run ID:" in line:
        run_id = line.split("Run ID: ")[1].split()[0]
        print(f"\n>>> CAPTURED RUN ID: {run_id}\n")
    
    if "Saved progress: attempt" in line:
        attempt_count += 1
        if attempt_count >= 3:
            print(f"\n>>> Stopping after {attempt_count} attempts\n")
            proc.terminate()
            time.sleep(2)
            proc.kill()
            break

print("\n" + "="*80)
print(f"Interrupted after {attempt_count} attempts")
print("="*80 + "\n")

if run_id:
    # Check state file
    state_file = Path.home() / ".garak" / "runs" / run_id / "state.json"
    print(f"State file: {state_file}\n")
    
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        
        print("Current state:")
        print(f"  Finished: {state.get('finished', False)}")
        print(f"  Granularity: {state.get('granularity')}")
        print(f"  Progress: {state.get('progress')}")
        print(f"  Completed probes: {state.get('completed_probes', [])}")
        print(f"  Probes state:")
        for probe, pdata in state.get('probes', {}).items():
            print(f"    {probe}: prompt_index={pdata.get('prompt_index')}, total={pdata.get('total_prompts')}")
        print()
        
        # Now resume
        print("="*80)
        print(f"RESUMING with: garak --resume {run_id}")
        print("="*80 + "\n")
        
        result = subprocess.run(
            [sys.executable, "-m", "garak", "--resume", run_id],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check state after resume
        print("\n" + "="*80)
        print("State after resume:")
        print("="*80 + "\n")
        
        if state_file.exists():
            with open(state_file) as f:
                state_after = json.load(f)
            
            print(f"  Finished: {state_after.get('finished', False)}")
            print(f"  Progress: {state_after.get('progress')}")
            print(f"  Completed probes: {state_after.get('completed_probes', [])}")
            print(f"  Probes state:")
            for probe, pdata in state_after.get('probes', {}).items():
                print(f"    {probe}: prompt_index={pdata.get('prompt_index')}, total={pdata.get('total_prompts')}")
        
        # Check the log file for RESUME DEBUG messages
        print("\n" + "="*80)
        print("RESUME DEBUG messages from log:")
        print("="*80 + "\n")
        
        log_file = Path.home() / ".local/share/garak/garak.log"
        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
            
            # Get last 100 lines and filter for RESUME DEBUG
            for line in lines[-100:]:
                if "[RESUME DEBUG]" in line:
                    print(line.rstrip())
    else:
        print(f"ERROR: State file not found at {state_file}")
else:
    print("ERROR: Could not capture run ID")
