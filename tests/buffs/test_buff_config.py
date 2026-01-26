# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# two tests:
# set buffs_include_original_prompt true
#  run test/lmrc.anthro
#  check that attempts w status 1 are original prompts + their lowercase versions
# set buffs_include_original_prompt false
#  run test/lmrc.anthro
#  check that attempts w status 1 are unique and have no uppercase characters

import json
import os
import tempfile
import uuid

import pytest

from garak import cli, _config

PREFIX = "test_buff_single" + str(uuid.uuid4())

_config.load_config()
REPORT_PATH = _config.transient.data_dir / _config.reporting.report_dir


@pytest.fixture(scope="function", autouse=True)
def clean_before_buff_tests():
    """Clean up test-related resume state before EACH buff config test."""
    import shutil
    from pathlib import Path
    import json
    
    # CRITICAL: Clear module-level resume state cache
    from garak import resumeservice
    resumeservice._resume_state = None
    resumeservice._run_manager = None
    
    # Clear transient resume_run_id to prevent auto-resume
    if hasattr(_config.transient, 'resume_run_id'):
        _config.transient.resume_run_id = None
    
    # Clean up resume state directory
    runs_dir = Path.home() / ".garak" / "runs"
    if runs_dir.exists():
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir():
                state_file = run_dir / "state.json"
                if state_file.exists():
                    try:
                        with open(state_file, 'r') as f:
                            state = json.load(f)
                        # Remove test-related runs
                        # probe_spec can be a string or list
                        probe_spec = state.get('probe_spec', [])
                        if isinstance(probe_spec, str):
                            probe_spec = [probe_spec]
                        if any('test.' in str(p) for p in probe_spec):
                            shutil.rmtree(run_dir)
                    except Exception:
                        pass
    
    # Clean up test report files that trigger auto-resume
    if REPORT_PATH.exists():
        for pattern in ['_garak_internal_test*.report.jsonl', 
                       '_garak_internal_test*.report.html',
                       '*test*.report.jsonl', 
                       '*Test*.report.jsonl']:
            for file in REPORT_PATH.glob(pattern):
                try:
                    if file.is_file():
                        file.unlink()
                except Exception:
                    pass


def test_include_original_prompt():
    # https://github.com/python/cpython/pull/97015 to ensure Windows compatibility
    with tempfile.NamedTemporaryFile(buffering=0, delete=False, suffix=".yaml") as tmp:
        tmp.write(
            """---
run:
    resumable: false
plugins:
    buffs_include_original_prompt: true
""".encode(
                "utf-8"
            )
        )
        tmp.close()
        cli.main(
            f"-m test -p test.Test -b lowercase.Lowercase --config {tmp.name} --report_prefix {PREFIX}".split()
        )
        os.remove(tmp.name)

    prompts = []
    with open(
        REPORT_PATH / f"{PREFIX}.report.jsonl", "r", encoding="utf-8"
    ) as reportfile:
        for line in reportfile:
            r = json.loads(line)
            if r["entry_type"] == "attempt" and r["status"] == 1:
                prompts.append(r["prompt"])
    nonupper_prompts = set([])
    other_prompts = set([])
    for prompt in prompts:
        text = prompt["turns"][-1]["content"]["text"]
        if text == text.lower() and text not in nonupper_prompts:
            nonupper_prompts.add(text)
        else:
            other_prompts.add(text)
    assert len(nonupper_prompts) >= len(other_prompts)
    assert len(nonupper_prompts) + len(other_prompts) == len(prompts)
    assert (
        set(map(str.lower, [p["turns"][-1]["content"]["text"] for p in prompts]))
        == nonupper_prompts
    )


def test_exclude_original_prompt():
    with tempfile.NamedTemporaryFile(buffering=0, delete=False, suffix=".yaml") as tmp:
        tmp.write(
            """---
run:
    resumable: false
plugins:
    buffs_include_original_prompt: false
""".encode(
                "utf-8"
            )
        )
        tmp.close()
        cli.main(
            f"-m test -p test.Test -b lowercase.Lowercase --config {tmp.name} --report_prefix {PREFIX}".split()
        )
        os.remove(tmp.name)

    prompts = []
    with open(
        REPORT_PATH / f"{PREFIX}.report.jsonl", "r", encoding="utf-8"
    ) as reportfile:
        for line in reportfile:
            r = json.loads(line)
            if r["entry_type"] == "attempt" and r["status"] == 1:
                prompts.append(r["prompt"])
    for prompt in prompts:
        text = prompt["turns"][-1]["content"]["text"]
        assert text == text.lower()


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""

    def remove_buff_reports():
        # Clean up report files
        files = [
            REPORT_PATH / f"{PREFIX}.report.jsonl",
            REPORT_PATH / f"{PREFIX}.report.html",
            REPORT_PATH / f"{PREFIX}.hitlog.jsonl",
        ]
        for file in files:
            if os.path.exists(file):
                os.remove(file)
        
        # Clean up resume state for test runs
        import shutil
        from pathlib import Path
        runs_dir = Path.home() / ".garak" / "runs"
        if runs_dir.exists():
            for run_dir in runs_dir.iterdir():
                if run_dir.is_dir():
                    # Remove directories that contain test-related runs
                    state_file = run_dir / "state.json"
                    if state_file.exists():
                        try:
                            import json
                            with open(state_file, 'r') as f:
                                state = json.load(f)
                            # Check if this is a test run (has test probes)
                            if any('test.' in str(p) for p in state.get('probe_spec', [])):
                                shutil.rmtree(run_dir)
                        except:
                            pass  # Ignore errors reading state files

    request.addfinalizer(remove_buff_reports)
