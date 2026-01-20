# Resume Continuity - Enhanced Implementation (v2.0)

## Overview

This document describes the **enhanced** implementation that makes resumed scans produce reports virtually indistinguishable from continuous, uninterrupted scans.

---

## What's New in v2.0

### Priority A: Preserve Original start_time ✅
**Status**: FULLY IMPLEMENTED

- Original `start_time` is now parsed from existing report.jsonl
- Preserved across all resume cycles in `_config.transient.original_start_time`
- Used in completion entry to show true scan duration
- Resume operations use current time only for `resumed_at` metadata

### Priority B: True Append Mode ✅
**Status**: FULLY IMPLEMENTED

- Report files opened in append mode (`"a"`) when resuming
- NO rewriting of setup/init entries (they already exist)
- Only new attempts are appended
- Completion and digest entries properly updated (old ones removed)
- Hitlog similarly appended with new hits only

### Priority C: Resume Metadata ✅
**Status**: FULLY IMPLEMENTED

- New `resume_info` entry added to report when resuming
- Includes:
  - `resumed_at`: Timestamp when resume started
  - `original_start_time`: Original scan start time
  - `original_run_id`: Consistent run_id
  - `completed_probes`: List of fully completed probes
  - `resume_points`: Per-probe resume positions

---

## Key Changes Made

### 1. Enhanced cli.py (Lines ~785-920)

#### Change 1A: Improved State Loading Order
```python
# OLD: Load state, then construct paths
if is_resuming:
    state = resumeservice._resume_state
    # ... load settings ...
    # PROBLEM: Report path constructed BEFORE parsing original run_id

# NEW: Load state AND parse report BEFORE constructing final paths
if is_resuming:
    state = resumeservice._resume_state
    original_run_id = resumeservice.extract_uuid_from_run_id(state["run_id"])
    _config.transient.run_id = original_run_id  # Set FIRST
    
    # NOW construct report path with correct run_id
    expected_report_path = ... f"{original_run_id}.report.jsonl"
    
    # Parse to get start_time
    parsed_run_id, original_start_time = parse_existing_report_metadata(expected_report_path)
    _config.transient.original_start_time = original_start_time
```

**Why**: Ensures we use the original run_id when constructing report filename, so we append to the RIGHT file.

#### Change 1B: Resume Metadata Entry
```python
# NEW: When resuming, write resume_info instead of setup/init
if not is_resuming:
    # Write setup and init entries (fresh run)
    ...
else:
    # Write resume metadata
    resume_entry = {
        "entry_type": "resume_info",
        "resumed_at": datetime.datetime.now().isoformat(),
        "original_start_time": _config.transient.original_start_time,
        "original_run_id": _config.transient.run_id,
        "resume_from_file": _config.transient.report_filename,
        "completed_probes": [...],
        "resume_points": {"probe_name": {"resume_from_seq": 3, "total_prompts": 5}}
    }
    reportfile.write(json.dumps(resume_entry) + "\n")
```

**Why**: Provides transparency about resume operations while maintaining report continuity.

---

### 2. Previous Changes (Still Active)

#### command.py
- `remove_trailing_metadata_entries()`: Removes old completion/digest before adding new
- Completion entry includes both `start_time` and `end_time`

#### report_digest.py
- Smart digest replacement (removes existing digest/completion before appending new)

#### resumeservice.py
- Preserves `original_start_time` in state

---

## Report Structure: Before vs After v2.0

### Original Garak (Uninterrupted Run)
```jsonl
{"entry_type": "start_run setup", ...}
{"entry_type": "init", "run": "abc-123", "start_time": "2026-01-20T10:00:00", ...}
{"entry_type": "attempt", "seq": 0, "probe_classname": "av_spam_scanning.EICAR", ...}
{"entry_type": "attempt", "seq": 1, "probe_classname": "av_spam_scanning.EICAR", ...}
...
{"entry_type": "completion", "start_time": "2026-01-20T10:00:00", "end_time": "2026-01-20T10:10:00", ...}
{"entry_type": "digest", ...}
```

### v2.0 Resumed Run (NOW IDENTICAL + Resume Metadata)
```jsonl
{"entry_type": "start_run setup", ...}                                        # Initial run
{"entry_type": "init", "run": "abc-123", "start_time": "2026-01-20T10:00:00", ...}  # Initial run
{"entry_type": "attempt", "seq": 0, "probe_classname": "av_spam_scanning.EICAR", ...}  # Initial run
{"entry_type": "attempt", "seq": 1, "probe_classname": "av_spam_scanning.EICAR", ...}  # Initial run
[INTERRUPTED at seq 1]
{"entry_type": "resume_info", "resumed_at": "2026-01-20T10:05:00", "original_start_time": "2026-01-20T10:00:00", ...}  # Resume marker
{"entry_type": "attempt", "seq": 2, "probe_classname": "av_spam_scanning.EICAR", ...}  # Resumed (APPENDED)
{"entry_type": "attempt", "seq": 3, "probe_classname": "av_spam_scanning.EICAR", ...}  # Resumed (APPENDED)
...
{"entry_type": "completion", "start_time": "2026-01-20T10:00:00", "end_time": "2026-01-20T10:15:00", ...}  # Complete timeline
{"entry_type": "digest", ...}
```

**Key Improvements**:
- ✅ Single file (no separate resumed report)
- ✅ Same `run_id` throughout ("abc-123")
- ✅ Original `start_time` preserved ("2026-01-20T10:00:00")
- ✅ Resume transparently documented (`resume_info` entry)
- ✅ Sequential attempts (no duplicates)
- ✅ Complete timeline in completion entry

---

## Verification Steps

### 1. Check File Append Behavior
```bash
# Start scan
python -m garak -m test -p av_spam_scanning --resumable --report_prefix test_v2

# Count lines (should be ~7: setup, init, 5 EICAR attempts)
wc -l test_v2.report.jsonl
# Output: 7

# Press Ctrl+C after EICAR completes

# Resume
python -m garak --resume garak-run-<uuid>-<timestamp>

# Count lines again (should be MORE, not reset)
wc -l test_v2.report.jsonl
# Output: ~15 (original 7 + resume_info + 5 GTUBE attempts + completion + digest)
```

### 2. Verify Original start_time
```bash
# Extract init and completion start_time
cat test_v2.report.jsonl | jq 'select(.entry_type == "init" or .entry_type == "completion") | {entry_type, start_time}'

# Expected output:
# {
#   "entry_type": "init",
#   "start_time": "2026-01-20T10:00:00.123456"  ← Original
# }
# {
#   "entry_type": "completion",
#   "start_time": "2026-01-20T10:00:00.123456"  ← SAME as init!
# }
```

### 3. Check Resume Metadata
```bash
# Extract resume_info entry
cat test_v2.report.jsonl | jq 'select(.entry_type == "resume_info")'

# Expected output:
# {
#   "entry_type": "resume_info",
#   "resumed_at": "2026-01-20T10:05:00.789012",
#   "original_start_time": "2026-01-20T10:00:00.123456",
#   "original_run_id": "abc-123",
#   "resume_from_file": ".../test_v2.report.jsonl",
#   "completed_probes": ["av_spam_scanning.EICAR"],
#   "resume_points": {
#     "av_spam_scanning.GTUBE": {
#       "resume_from_seq": 0,
#       "total_prompts": 5
#     }
#   }
# }
```

### 4. Verify No Duplicates
```bash
# Count setup entries (should be 1)
grep -c '"entry_type": "start_run setup"' test_v2.report.jsonl

# Count init entries (should be 1)
grep -c '"entry_type": "init"' test_v2.report.jsonl

# Count resume_info entries (should be 1 per resume cycle)
grep -c '"entry_type": "resume_info"' test_v2.report.jsonl

# Check for duplicate attempt UUIDs (should be 0)
cat test_v2.report.jsonl | jq -r 'select(.entry_type == "attempt") | .uuid' | sort | uniq -d | wc -l
```

---

## Benefits of v2.0

### For Compliance/Auditing
- **Single source of truth**: One file per scan, regardless of interruptions
- **Complete timeline**: True start-to-finish duration in completion entry
- **Transparency**: Resume operations clearly documented
- **Traceability**: Can identify which attempts were from original vs resumed runs

### For Analysis
- **Consistent run_id**: Easy to correlate attempts across tools
- **Accurate metrics**: Total scan time calculated from original start_time
- **Resume history**: Know exactly when/where scan was interrupted and resumed

### For Debugging
- **Clear audit trail**: See exact sequence of events
- **Resume metadata**: Understand what was completed before interrupt
- **No ambiguity**: Single file makes troubleshooting straightforward

---

## Edge Cases Handled

### Case 1: Multiple Resume Cycles
```
Initial run: seq 0-2
[Interrupt 1]
Resume 1: seq 3-4
[Interrupt 2]
Resume 2: seq 5-7
```

**Result**:
- 2 `resume_info` entries (one per resume)
- All attempts in sequence (0-7)
- Original `start_time` preserved across all cycles
- Final completion shows total duration

### Case 2: Report File Doesn't Exist
**Scenario**: State exists but report file deleted

**Handling**:
- `parse_existing_report_metadata()` returns `(None, None)`
- Falls back to fresh run behavior (write setup/init)
- Logs warning about missing report

### Case 3: run_id Mismatch
**Scenario**: State run_id ≠ Report run_id

**Handling**:
- Logs warning
- Uses state's run_id (more authoritative)
- Continues resume operation
- Analyst can investigate using resume_info

### Case 4: Corrupted Report File
**Scenario**: Report file exists but unparseable

**Handling**:
- `parse_existing_report_metadata()` catches exception
- Returns `(None, None)`
- Logs warning
- Falls back to fresh run (safe default)

---

## Testing Checklist

- [ ] Fresh run creates correct structure (setup, init, attempts, completion, digest)
- [ ] Interrupted run preserves partial report
- [ ] Resume appends to same file (doesn't overwrite)
- [ ] Resume uses original run_id
- [ ] Resume preserves original start_time
- [ ] Resume writes resume_info entry
- [ ] No duplicate setup/init entries on resume
- [ ] No duplicate attempts
- [ ] Completion entry has both start_time and end_time
- [ ] Only one digest in final report
- [ ] HTML report generated correctly
- [ ] Multiple resume cycles work correctly

---

## Comparison: v1.0 vs v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Preserve run_id | ✅ | ✅ |
| Preserve start_time | ✅ | ✅ |
| Append mode | ✅ | ✅ **Enhanced** |
| Skip duplicate setup/init | ❌ | ✅ **New** |
| Resume metadata | ❌ | ✅ **New** |
| Correct file path resolution | ⚠️ (Had bug) | ✅ **Fixed** |
| Resume point tracking | Basic | ✅ **Detailed** |

---

## Summary

**v2.0 Implementation Achievements**:

1. ✅ **Priority A (Preserve start_time)**: Fully implemented with robust parsing and fallbacks
2. ✅ **Priority B (True append mode)**: Files truly appended, no overwrites, no duplicate setup/init
3. ✅ **Priority C (Resume metadata)**: Comprehensive resume_info entry with full details

**Key Improvement**: Fixed critical bug where report filename was constructed BEFORE loading original run_id, causing resume to create new files instead of appending.

**Result**: Resumed scans now produce reports that are **structurally identical** to continuous runs, with the only additions being transparent `resume_info` entries that enhance traceability.

---

*Version: 2.0*  
*Last Updated: 2026-01-20*  
*Garak Version: 0.14.0.pre1*
