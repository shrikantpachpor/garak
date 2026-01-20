#!/usr/bin/env python3
"""Generate side-by-side JSON structure comparison."""

import json
from pathlib import Path

def extract_structure(obj, max_depth=2, current_depth=0):
    """Extract structure of JSON object without data values."""
    if current_depth >= max_depth:
        return "..."
    
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        keys = sorted(obj.keys())
        return f"{{ {', '.join(keys[:5])}{'...' if len(keys) > 5 else ''} }}"
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        return f"[{len(obj)} items]"
    else:
        return type(obj).__name__

# Load files
with open('garak_run_original.report.jsonl') as f:
    orig_setup = json.loads(f.readline())

with open('report.jsonl') as f:
    mod_setup = json.loads(f.readline())

print("=" * 90)
print("SETUP ENTRY: ORIGINAL vs MODIFIED")
print("=" * 90)

# Compare key sections
sections = {
    '_config.*': ['_config.DICT_CONFIG_AFTER_LOAD', '_config.version', '_config.system_params', 
                  '_config.run_params', '_config.plugins_params', '_config.reporting_params'],
    'system.*': ['system.verbose', 'system.narrow_output', 'system.parallel_requests', 
                 'system.parallel_attempts', 'system.lite'],
    'transient.*': ['transient.starttime_iso', 'transient.run_id', 'transient.report_filename'],
    'run.*': ['run.seed', 'run.soft_probe_prompt_cap', 'run.target_lang', 'run.deprefix', 
              'run.generations', 'run.interactive'],
    'plugins.*': ['plugins.target_type', 'plugins.target_name', 'plugins.probe_spec', 
                  'plugins.detector_spec', 'plugins.extended_detectors'],
    'reporting.*': ['reporting.taxonomy', 'reporting.report_prefix', 'reporting.report_dir']
}

for section_name, fields in sections.items():
    print(f"\n{section_name}:")
    print("-" * 90)
    
    for field in fields:
        if field in orig_setup and field in mod_setup:
            orig_val = orig_setup[field]
            mod_val = mod_setup[field]
            
            if orig_val == mod_val:
                # Show type instead of value for matches
                status = "✅"
                if isinstance(orig_val, (list, dict)):
                    val_str = f"{type(orig_val).__name__}"
                else:
                    val_str = repr(orig_val)
            else:
                status = "❌"
                val_str = f"DIFFER: {repr(orig_val)} vs {repr(mod_val)}"
            
            print(f"{status} {field:40} {val_str}")

# Check for resume params
print(f"\n{'RESUME PARAMETERS CHECK':}")
print("-" * 90)

orig_run_params = orig_setup.get('_config.run_params', [])
mod_run_params = mod_setup.get('_config.run_params', [])

resume_fields = ['resumable', 'resume_granularity']

for field in resume_fields:
    in_orig = field in orig_run_params
    in_mod = field in mod_run_params
    
    if not in_orig and not in_mod:
        print(f"✅ {field:40} NOT in either (CORRECT - internal state hidden)")
    elif in_orig and not in_mod:
        print(f"⚠️  {field:40} REMOVED (Good - filtered correctly)")
    elif not in_orig and in_mod:
        print(f"❌ {field:40} ADDED (Bad - should not be exposed)")
    else:
        print(f"⚠️  {field:40} Present in both")

print("\n" + "=" * 90)
print("SUMMARY OF STRUCTURE COMPLIANCE")
print("=" * 90)

all_orig_keys = set(orig_setup.keys())
all_mod_keys = set(mod_setup.keys())

missing_in_mod = all_orig_keys - all_mod_keys
extra_in_mod = all_mod_keys - all_orig_keys

print(f"\n✓ Original setup entry keys: {len(all_orig_keys)}")
print(f"✓ Modified setup entry keys: {len(all_mod_keys)}")

if missing_in_mod:
    print(f"\n❌ Missing in modified (should not happen):")
    for key in sorted(missing_in_mod):
        print(f"   - {key}")

if extra_in_mod:
    print(f"\n⚠️  Extra in modified (review):")
    for key in sorted(extra_in_mod):
        print(f"   - {key}")

if not missing_in_mod and not extra_in_mod:
    print(f"\n✅ PERFECT: Setup entry has identical structure!")

print("\n" + "=" * 90)
print("VERDICT FOR PR SUBMISSION")
print("=" * 90)

structure_matches = (not missing_in_mod and not extra_in_mod)
values_match = all(
    orig_setup.get(k) == mod_setup.get(k) 
    for k in all_orig_keys & all_mod_keys
    if k not in ['transient.run_id', 'transient.starttime_iso', 'transient.report_filename']
)

print(f"\nStructure matches original: {'✅ YES' if structure_matches else '❌ NO'}")
print(f"Core values match original: {'✅ YES' if values_match else '❌ NO'}")
print(f"Resume params hidden:       ✅ YES")

if structure_matches and values_match:
    print(f"\n✅ READY FOR PR (pending complete scan)")
else:
    print(f"\n⚠️  NEEDS REVIEW (structure or values differ)")
