#!/usr/bin/env python3
import json
import os
from pathlib import Path

report_path = Path(os.path.expanduser("~/.local/share/garak/garak_reports/garak_run.report.jsonl"))
hitlog_path = Path(os.path.expanduser("~/.local/share/garak/garak_reports/garak_run.hitlog.jsonl"))

print("=" * 60)
print("REPORT STATUS")
print("=" * 60)

if report_path.exists():
    lines = report_path.read_text().strip().split("\n")
    print(f"Report lines: {len(lines)}")
    
    # Parse all entries
    entries = []
    for line in lines:
        if line.strip():
            try:
                entries.append(json.loads(line))
            except:
                pass
    
    print(f"Valid JSON entries: {len(entries)}")
    
    if entries:
        print(f"\nFirst entry type: {entries[0].get('entry_type')}")
        print(f"Last entry type: {entries[-1].get('entry_type')}")
        print(f"Last entry probe: {entries[-1].get('probe')}")
        
        # Count by entry type
        types = {}
        for e in entries:
            t = e.get('entry_type')
            types[t] = types.get(t, 0) + 1
        print(f"\nEntry type counts: {types}")
else:
    print("Report file not found")

print("\n" + "=" * 60)
print("HITLOG STATUS")
print("=" * 60)

if hitlog_path.exists():
    content = hitlog_path.read_text()
    lines = [l for l in content.strip().split("\n") if l.strip()]
    print(f"Hitlog lines: {len(lines)}")
    
    if lines:
        # Check run_id consistency
        run_ids = set()
        for line in lines:
            try:
                entry = json.loads(line)
                run_ids.add(entry.get('run_id'))
            except:
                pass
        
        print(f"Unique run_id values: {len(run_ids)}")
        for rid in sorted(run_ids):
            print(f"  - {rid} (len={len(rid)})")
else:
    print("Hitlog file not found")

print("\n" + "=" * 60)
print("RESUME STATE")
print("=" * 60)

runs_dir = Path(os.path.expanduser("~/.garak/runs"))
if runs_dir.exists():
    subdirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    print(f"Resume runs directories: {len(subdirs)}")
    for d in sorted(subdirs)[-3:]:  # Last 3
        state_file = d / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            print(f"\n{d.name}:")
            print(f"  probes_completed: {len(state.get('probes_completed', []))}")
            print(f"  Total attempts completed: {sum(len(v) for v in state.get('attempts_completed', {}).values())}")
else:
    print("Resume state directory not found")
