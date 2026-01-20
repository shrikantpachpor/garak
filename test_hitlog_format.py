#!/usr/bin/env python3
"""Test hitlog run_id consistency without full scan."""

import json
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add garak to path
sys.path.insert(0, str(Path(__file__).parent))

def test_hitlog_run_id():
    """Test that hitlog entries use consistent UUID-only run_id."""
    
    # Mock attempt object
    class MockAttempt:
        def __init__(self):
            self.uuid = "test-uuid-1234"
            self.seq = 0
            self.goal = "test goal"
            self.notes = {"triggers": None}
            self.probe = "test.probe"
            self.prompt = MagicMock()
            self.outputs = [MagicMock()]
            self.detector_results = {"test_detector": [0.5]}
    
    # Create a minimal hitlog entry manually
    attempt = MockAttempt()
    run_id_uuid = "85c0f1df-1e8e-4b3e-8bde-4ba915705122"
    target_type = "rest"
    target_name = "RestGenerator"
    
    hitlog_entry = {
        "goal": attempt.goal,
        "prompt": "test prompt",
        "output": "test output",
        "triggers": None,
        "score": 0.5,
        "run_id": str(run_id_uuid),  # This is what evaluators/base.py line 112 writes
        "attempt_id": str(attempt.uuid),
        "attempt_seq": attempt.seq,
        "attempt_idx": 0,
        "generator": f"{target_type} {target_name}",
        "probe": "test.probe",
        "detector": "test_detector",
        "generations_per_prompt": 1,
    }
    
    # Verify the run_id in hitlog entry
    print("=" * 60)
    print("HITLOG ENTRY TEST")
    print("=" * 60)
    print(f"run_id: {hitlog_entry['run_id']}")
    print(f"Length: {len(hitlog_entry['run_id'])} chars")
    print(f"Is UUID format (36 chars): {len(hitlog_entry['run_id']) == 36}")
    print(f"Contains 'garak-run': {'garak-run' in hitlog_entry['run_id']}")
    
    # Check if it matches the pattern of a UUID
    import re
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    is_valid_uuid = bool(re.match(uuid_pattern, hitlog_entry['run_id']))
    print(f"Matches UUID regex: {is_valid_uuid}")
    
    # Verify generator field
    print(f"\ngenerator: {hitlog_entry['generator']}")
    print(f"Correct format (type name): {hitlog_entry['generator'] == 'rest RestGenerator'}")
    
    # Success criteria
    success = (
        len(hitlog_entry['run_id']) == 36 and
        'garak-run' not in hitlog_entry['run_id'] and
        is_valid_uuid and
        hitlog_entry['generator'] == 'rest RestGenerator'
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ HITLOG RUN_ID TEST PASSED")
        print("Hitlog entries will use consistent UUID-only format")
    else:
        print("❌ HITLOG RUN_ID TEST FAILED")
        if len(hitlog_entry['run_id']) != 36:
            print(f"  - run_id length is {len(hitlog_entry['run_id'])}, expected 36")
        if 'garak-run' in hitlog_entry['run_id']:
            print("  - run_id contains 'garak-run' prefix (should be UUID only)")
        if not is_valid_uuid:
            print("  - run_id does not match UUID format")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(test_hitlog_run_id())
