#!/usr/bin/env python3
"""Validate setup entry format."""

import json
from pathlib import Path

report_file = Path("report.jsonl")
with open(report_file) as f:
    setup = json.loads(f.readline())

print("=" * 70)
print("SETUP ENTRY VALIDATION")
print("=" * 70)

# Check entry_type
print(f"\n✓ entry_type: {setup.get('entry_type')}")
assert setup.get('entry_type') == 'start_run setup', "Wrong entry type"

# Check transient.run_id format
run_id = setup.get('transient.run_id')
print(f"✓ transient.run_id: {run_id}")
print(f"  - Length: {len(run_id)} chars")
print(f"  - Is UUID: {len(run_id) == 36}")
assert len(run_id) == 36, "run_id should be 36 chars (UUID only)"
assert not run_id.startswith("garak-run"), "run_id should not have 'garak-run' prefix"

# Check plugins.target_type
target_type = setup.get('plugins.target_type')
print(f"✓ plugins.target_type: {target_type}")
assert target_type == "rest", f"Expected 'rest', got '{target_type}'"

# Check plugins.target_name
target_name = setup.get('plugins.target_name')
print(f"✓ plugins.target_name: {target_name}")
assert target_name == "RestGenerator", f"Expected 'RestGenerator', got '{target_name}'"

# Check _config.plugins_params
plugins_params = setup.get('_config.plugins_params')
print(f"✓ _config.plugins_params: {plugins_params}")
expected_params = ["target_type", "target_name", "extended_detectors"]
assert plugins_params == expected_params, f"Expected {expected_params}, got {plugins_params}"

# Check that resumable-related params are NOT in run_params
run_params = setup.get('_config.run_params')
print(f"✓ _config.run_params: {run_params}")
assert "resumable" not in run_params, "resumable should not be in run_params"
assert "resume_granularity" not in run_params, "resume_granularity should not be in run_params"

print("\n" + "=" * 70)
print("✅ ALL SETUP ENTRY CHECKS PASSED")
print("=" * 70)
print("\nSetup entry format matches original garak structure:")
print("  ✓ Correct entry_type")
print("  ✓ transient.run_id is UUID-only (36 chars)")
print("  ✓ plugins.target_type and plugins.target_name correct")
print("  ✓ _config.plugins_params excludes model_type/model_name")
print("  ✓ Resume params not exposed in run_params")
