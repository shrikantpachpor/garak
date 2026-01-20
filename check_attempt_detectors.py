#!/usr/bin/env python3
import json

with open('report.jsonl') as f:
    for i, line in enumerate(f):
        entry = json.loads(line)
        if entry.get('entry_type') == 'attempt':
            detector_results = entry.get('detector_results', {})
            print(f"Attempt {i}: seq={entry.get('seq')}, status={entry.get('status')}, detector_results={len(detector_results)} detectors")
            if detector_results:
                for key in detector_results:
                    print(f"  - {key}: {detector_results[key]}")
            else:
                print("  (NO DETECTOR RESULTS)")
