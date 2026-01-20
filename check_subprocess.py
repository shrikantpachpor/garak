#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import time

# Let subprocess handle it
result = subprocess.run([
    sys.executable, "-c", """
import json
import os
from pathlib import Path

report_path = Path(os.path.expanduser("~/.local/share/garak/garak_reports/garak_run.report.jsonl"))
hitlog_path = Path(os.path.expanduser("~/.local/share/garak/garak_reports/garak_run.hitlog.jsonl"))

print("=" * 60)
print("REPORT STATUS")
print("=" * 60)

if report_path.exists():
    lines = report_path.read_text().strip().split("\\n")
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
        print(f"\\nEntry types in report:")
        types = {}
        for e in entries:
            t = e.get('entry_type', 'unknown')
            types[t] = types.get(t, 0) + 1
        for t, c in sorted(types.items()):
            print(f"  {t}: {c}")
        
        print(f"\\nLast 3 entries:")
        for e in entries[-3:]:
            print(f"  {e.get('entry_type')}: probe={e.get('probe')}, attempt={e.get('attempt_id')}")
else:
    print("Report file not found")

print("\\n" + "=" * 60)
print("HITLOG STATUS")
print("=" * 60)

if hitlog_path.exists():
    content = hitlog_path.read_text()
    lines = [l for l in content.strip().split("\\n") if l.strip()]
    print(f"Hitlog lines: {len(lines)}")
    
    if lines:
        print(f"\\nFirst 3 hitlog entries:")
        for i, line in enumerate(lines[:3]):
            try:
                entry = json.loads(line)
                print(f"  Entry {i+1}: run_id={entry.get('run_id')}, attempt={entry.get('attempt_id')}")
            except:
                print(f"  Entry {i+1}: INVALID JSON")
    else:
        print("Hitlog is empty")
else:
    print("Hitlog file not found")
"""
], capture_output=True, text=True, timeout=30)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)
