"""Test script to verify resume functionality by interrupting a scan."""
import subprocess
import time
import sys
import signal
import os

# Start garak with a probe that has multiple attempts
cmd = [
    sys.executable, "-m", "garak",
    "--target_type", "test",
    "--target_name", "Test",
    "--probes", "av_spam_scanning.EICAR,av_spam_scanning.GTUBE,goodside.WhoIsRiley",
    "--resumable",
    "--resume_granularity", "attempt"
]

print("🚀 Starting garak scan...")
print(f"Command: {' '.join(cmd)}\n")

# Start the process
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

# Collect output and run_id
run_id = None
attempt_count = 0
for line in iter(proc.stdout.readline, ''):
    if not line:
        break
    print(line, end='')
    
    # Extract run ID
    if "Run ID:" in line:
        run_id = line.split("Run ID: ")[1].split()[0]
        print(f"\n📝 Captured Run ID: {run_id}\n")
    
    # Count saved attempts
    if "Saved progress: attempt" in line:
        attempt_count += 1
        print(f"[Test] Counted {attempt_count} saved attempts so far")
        
        # Kill after 3 attempts from first probe
        if attempt_count == 3:
            print(f"\n❌ Interrupting after {attempt_count} attempts...\n")
            proc.send_signal(signal.CTRL_C_EVENT if os.name == 'nt' else signal.SIGINT)
            time.sleep(2)
            proc.terminate()
            time.sleep(1)
            proc.kill()
            break

print("\n" + "="*80)
print("First scan interrupted. Now checking state file...")
print("="*80 + "\n")

if run_id:
    # Check the state file
    state_file = os.path.expanduser(f"~/.garak/runs/{run_id}/state.json")
    print(f"State file path: {state_file}")
    
    if os.path.exists(state_file):
        import json
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        print(f"\n📊 State file contents:")
        print(f"  - Granularity: {state.get('granularity')}")
        print(f"  - Finished: {state.get('finished')}")
        print(f"  - Completed probes: {state.get('completed_probes', [])}")
        print(f"  - Probes state: {json.dumps(state.get('probes', {}), indent=4)}")
        
        # Now try to resume
        print("\n" + "="*80)
        print(f"Now resuming with: --resume {run_id}")
        print("="*80 + "\n")
        
        resume_cmd = [
            sys.executable, "-m", "garak",
            "--resume", run_id
        ]
        
        print(f"Resume command: {' '.join(resume_cmd)}\n")
        result = subprocess.run(resume_cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check state file again
        print("\n" + "="*80)
        print("After resume - checking state file again...")
        print("="*80 + "\n")
        
        with open(state_file, 'r') as f:
            state_after = json.load(f)
        
        print(f"  - Finished: {state_after.get('finished')}")
        print(f"  - Completed probes: {state_after.get('completed_probes', [])}")
        print(f"  - Probes state: {json.dumps(state_after.get('probes', {}), indent=4)}")
    else:
        print(f"❌ State file not found: {state_file}")
else:
    print("❌ Could not extract run ID from output")
