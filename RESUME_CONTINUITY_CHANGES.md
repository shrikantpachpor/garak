# Resume Continuity - Code Changes Summary

## Quick Reference for Code Review

This document provides a concise summary of all code changes made to implement resume continuity.

---

## File 1: `garak/cli.py`

### Change 1A: Add metadata parsing helper (Lines ~750-780)

```python
# ADD: Helper function to parse existing report
def parse_existing_report_metadata(report_path):
    """Parse existing report to extract original run_id and start_time."""
    if not os.path.exists(report_path):
        return None, None
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line.strip())
                if entry.get('entry_type') == 'init':
                    return entry.get('run'), entry.get('start_time')
    except Exception as e:
        logging.warning(f"Could not parse existing report metadata: {e}")
    return None, None
```

### Change 1B: Load original metadata on resume (Lines ~760-800)

```python
# MODIFY: Existing resume logic
is_resuming = hasattr(_config.transient, "resume_run_id") and _config.transient.resume_run_id
original_start_time = None  # ADD: Track original start time

if is_resuming:
    # ... existing state loading code ...
    
    # ADD: Parse existing report to preserve original metadata
    report_dir = _config.transient.data_dir / _config.reporting.report_dir
    report_prefix = _config.reporting.report_prefix or f"garak.{_config.transient.run_id}"
    expected_report_path = str(report_dir / f"{report_prefix}.report.jsonl")
    
    original_run_id, original_start_time = parse_existing_report_metadata(expected_report_path)
    if original_run_id:
        logging.info(f"Resuming with original run_id: {original_run_id}")
        _config.transient.run_id = original_run_id
    if original_start_time:
        logging.info(f"Preserving original start_time: {original_start_time}")
        _config.transient.original_start_time = original_start_time
```

**Impact**: Preserves original `run_id` and `start_time` across resume cycles.

---

## File 2: `garak/command.py`

### Change 2A: Add cleanup helper in `end_run()` (Lines ~155-205)

```python
def end_run():
    import datetime
    import logging
    import tempfile  # ADD
    import os        # ADD

    from garak import _config

    logging.info("run complete, ending")
    
    # ADD: Helper function to remove old completion/digest entries
    def remove_trailing_metadata_entries(report_path):
        """Remove trailing completion and digest entries from report file."""
        if not os.path.exists(report_path):
            return
        try:
            # Read all lines
            with open(report_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find last non-completion/digest entry
            last_valid_idx = len(lines) - 1
            for i in range(len(lines) - 1, -1, -1):
                if not lines[i].strip():
                    continue
                try:
                    entry = json.loads(lines[i].strip())
                    if entry.get('entry_type') not in ('completion', 'digest'):
                        last_valid_idx = i
                        break
                except:
                    pass
            
            # Write back only valid entries
            if last_valid_idx < len(lines) - 1:
                with tempfile.NamedTemporaryFile('w', delete=False, 
                                                 dir=os.path.dirname(report_path),
                                                 encoding='utf-8') as tmp:
                    tmp.writelines(lines[:last_valid_idx + 1])
                    tmp_path = tmp.name
                os.replace(tmp_path, report_path)
                logging.info(f"Removed {len(lines) - last_valid_idx - 1} trailing metadata entries")
        except Exception as e:
            logging.warning(f"Could not remove trailing entries: {e}")
```

### Change 2B: Update completion entry logic (Lines ~205-215)

```python
    # ADD: Remove old entries if resuming
    is_resuming = hasattr(_config.transient, "resume_run_id") and _config.transient.resume_run_id
    if is_resuming:
        remove_trailing_metadata_entries(_config.transient.report_filename)
    
    # MODIFY: Use original start_time if available
    start_time = (_config.transient.original_start_time 
                  if hasattr(_config.transient, "original_start_time") and _config.transient.original_start_time
                  else _config.transient.starttime_iso)
    
    # MODIFY: Include start_time in completion entry
    end_object = {
        "entry_type": "completion",
        "start_time": start_time,  # ADD: Include original start time
        "end_time": datetime.datetime.now().isoformat(),
        "run": _config.transient.run_id,
    }
```

### Change 2C: Update digest writing (Lines ~320-330)

```python
# MODIFY: Change file mode from 'a' to 'r+' for digest replacement
def write_report_digest(report_filename, html_report_filename):
    from garak.analyze import report_digest

    digest = report_digest.build_digest(report_filename)
    
    # CHANGE: Open in r+ mode instead of append mode
    with open(report_filename, "r+", encoding="utf-8") as reportfile:
        report_digest.append_report_object(reportfile, digest)
    
    html_report = report_digest.build_html(digest)
    with open(html_report_filename, "w", encoding="utf-8") as htmlfile:
        htmlfile.write(html_report)
```

**Impact**: Removes duplicate completion/digest entries and includes full timeline in completion.

---

## File 3: `garak/analyze/report_digest.py`

### Change 3: Smart digest replacement (Lines ~365-395)

```python
# MODIFY: Replace entire function
def append_report_object(reportfile: IO, object: dict):
    """Append a report object to the JSONL file.
    
    If the object is a digest entry and one already exists, it will be replaced
    rather than appended to avoid duplication.
    """
    import tempfile
    
    # ADD: If this is a digest, replace existing one
    if object.get('entry_type') == 'digest':
        try:
            # Read all existing lines
            reportfile.seek(0)
            lines = reportfile.readlines()
            
            # Find and remove existing digest/completion entries
            filtered_lines = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    # Skip existing digest and completion entries
                    if entry.get('entry_type') not in ('digest', 'completion'):
                        filtered_lines.append(line)
                except:
                    filtered_lines.append(line)
            
            # Rewrite file with filtered content
            reportfile.seek(0)
            reportfile.truncate()
            reportfile.writelines(filtered_lines)
            reportfile.flush()
        except Exception as e:
            import logging
            logging.warning(f"Could not filter existing digest: {e}")
    
    # Now append the new entry
    end_val = reportfile.seek(0, os.SEEK_END)
    if end_val > 0:
        reportfile.seek(end_val - 1)
        last_char = reportfile.read()
        if last_char not in "\n\r":
            reportfile.write("\n")
    reportfile.write(json.dumps(object, ensure_ascii=False) + "\n")  # ADD: ensure_ascii=False + newline
```

**Impact**: Ensures only one digest entry exists in final report.

---

## File 4: `garak/resumeservice.py`

### Change 4: Preserve original start time (Lines ~770-785)

```python
# MODIFY: Use original start_time if available
def initialize_new_run_with_attempts(probenames: List[str], generator=None, existing_run_uuid: str = None) -> str:
    # ... existing code ...
    
    # ADD: Preserve original start_time if available (for resumed runs)
    original_start_time = (_config.transient.original_start_time 
                           if hasattr(_config.transient, "original_start_time") and _config.transient.original_start_time
                           else datetime.now().isoformat())
    
    _resume_state = {
        "run_id": run_id,
        "probenames": probenames,
        # ... other fields ...
        "start_time": original_start_time,  # CHANGE: Use original instead of current time
        "finished": False,
    }
    
    # ... rest of function ...
```

**Impact**: State file preserves original start_time for consistency.

---

## Summary of Changes

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `garak/cli.py` | ~30 lines added | Parse and preserve original run_id/start_time |
| `garak/command.py` | ~50 lines added/modified | Clean up old metadata, update completion entry |
| `garak/analyze/report_digest.py` | ~40 lines modified | Smart digest replacement |
| `garak/resumeservice.py` | ~5 lines modified | Preserve original start_time in state |
| **Total** | **~125 lines** | **Complete resume continuity** |

---

## Testing Commands

```bash
# Run automated test
python test_resume_continuity.py

# Manual test
python -m garak -m test -p av_spam_scanning --resumable --report_prefix test
# Press Ctrl+C after 5 seconds
python -m garak --resume <run-id>

# Verify continuity
cat test.report.jsonl | jq 'select(.entry_type == "init" or .entry_type == "completion")'
# Should show matching run_id and start_time

grep -c '"entry_type": "digest"' test.report.jsonl
# Should output: 1
```

---

## Before/After Comparison

### Before Changes
```
Initial run creates:  run_id=A, start_time=T1
Resume creates:       run_id=B, start_time=T2  ❌
Result: Inconsistent reports
```

### After Changes
```
Initial run creates:  run_id=A, start_time=T1
Resume preserves:     run_id=A, start_time=T1  ✅
Result: Continuous, consistent report
```

---

## Integration Points

These changes integrate with existing resume logic:
- ✅ `resumeservice.load()` - State loading unchanged
- ✅ `mark_attempt_complete_by_seq()` - Attempt tracking unchanged
- ✅ Append mode for JSONL - Already implemented
- ✅ UUID extraction - Already implemented

**No breaking changes to existing functionality.**
