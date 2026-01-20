#!/usr/bin/env python3
"""
Quick test to verify progress bar shows 100% when all attempts complete during resume.

Usage:
    1. Start a scan and interrupt after first probe
    2. Resume the scan
    3. This script checks if all attempts were processed
"""

import json
import sys
from pathlib import Path

def check_progress(report_path):
    """Check if all attempts for each probe are present"""
    
    if not Path(report_path).exists():
        print(f"❌ Report file not found: {report_path}")
        return False
    
    entries = []
    with open(report_path, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    # Group attempts by probe
    probes = {}
    for entry in entries:
        if entry.get('entry_type') == 'attempt' and entry.get('status') == 2:
            probe_name = entry.get('probe_classname')
            if probe_name not in probes:
                probes[probe_name] = []
            probes[probe_name].append(entry.get('seq'))
    
    print(f"\n📊 Progress Check for: {report_path}\n")
    
    all_complete = True
    for probe_name, sequences in sorted(probes.items()):
        sequences = sorted(sequences)
        expected = list(range(len(sequences)))
        
        if sequences == expected:
            print(f"✅ {probe_name}: {len(sequences)}/5 attempts (seq {sequences})")
        else:
            print(f"❌ {probe_name}: Missing sequences! Found {sequences}, expected {expected}")
            all_complete = False
    
    if all_complete:
        print(f"\n✅ All probes have complete attempt sequences!")
    else:
        print(f"\n❌ Some attempts are missing!")
    
    return all_complete

if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    else:
        report_path = "C:\\Users\\user\\.local\\share\\garak\\garak_reports\\test_progress_fix.report.jsonl"
    
    check_progress(report_path)
