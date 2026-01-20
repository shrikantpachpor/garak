# Quick Test Guide - Resume Continuity v2.0

## Prerequisites
- Garak installed with v2.0 changes
- Test model configured (use `test` model for speed)
- At least 2 probes available (e.g., `av_spam_scanning.EICAR`, `av_spam_scanning.GTUBE`)

## Quick Test (5 minutes)

### Step 1: Start Initial Scan
```powershell
python -m garak `
    --model_type test `
    --probes av_spam_scanning.EICAR,av_spam_scanning.GTUBE `
    --config run.resumable=true `
    --report_prefix test_v2
```

**What to expect**:
- Scan starts with EICAR probe (5 attempts)
- Report file created: `test_v2.report.jsonl`
- Hitlog file created: `test_v2.hitlog.jsonl`

### Step 2: Interrupt After First Probe
**Press `Ctrl+C`** after you see:
```
av_spam_scanning.EICAR ✓
```

**Check the report**:
```powershell
# Count entries
(Get-Content test_v2.report.jsonl).Count
# Should be ~7: setup, init, 5 attempts

# Extract init entry
Get-Content test_v2.report.jsonl | jq 'select(.entry_type == "init")'
# Note the "start_time" and "run" (run_id)
```

**Save for comparison**:
```powershell
# Note the run_id from the console output or init entry
# Example: "garak-run-abc123-2026-01-20T10-00-00"
$runId = "garak-run-YOUR-RUN-ID-HERE"
```

### Step 3: Resume the Scan
```powershell
python -m garak --resume $runId
```

**What to expect**:
- Loads state from `~/.garak/runs/<run-id>/state.json`
- Opens `test_v2.report.jsonl` in APPEND mode
- Writes `resume_info` entry
- Continues with GTUBE probe (5 more attempts)
- Writes completion and digest

### Step 4: Validate Results
```powershell
# Run validation script
python test_resume_v2.py test_v2.report.jsonl
```

**Expected output**:
```
✅ Single 'start_run setup' entry found
✅ Single 'init' entry found
✅ Found 1 resume_info entry(ies)
✅ start_time preserved: init and completion match
✅ All attempts use consistent run_id
✅ All tests passed!
```

### Step 5: Manual Inspection

#### Check Entry Counts
```powershell
# Count each entry type
Get-Content test_v2.report.jsonl | jq -r '.entry_type' | Group-Object | Format-Table Count, Name
```

**Expected**:
```
Count Name
----- ----
    1 start_run setup
    1 init
    1 resume_info
   10 attempt         (5 EICAR + 5 GTUBE)
    1 completion
    1 digest
```

#### Check start_time Consistency
```powershell
# Extract start_time from init and completion
Get-Content test_v2.report.jsonl | jq 'select(.entry_type == "init" or .entry_type == "completion") | {entry_type, start_time}'
```

**Expected** (both should have SAME start_time):
```json
{
  "entry_type": "init",
  "start_time": "2026-01-20T10:00:00.123456"
}
{
  "entry_type": "completion",
  "start_time": "2026-01-20T10:00:00.123456"
}
```

#### Check resume_info Entry
```powershell
Get-Content test_v2.report.jsonl | jq 'select(.entry_type == "resume_info")'
```

**Expected**:
```json
{
  "entry_type": "resume_info",
  "resumed_at": "2026-01-20T10:05:00.789012",
  "original_start_time": "2026-01-20T10:00:00.123456",
  "original_run_id": "abc123",
  "resume_from_file": "E:\\path\\to\\test_v2.report.jsonl",
  "completed_probes": ["av_spam_scanning.EICAR"],
  "resume_points": {
    "av_spam_scanning.GTUBE": {
      "resume_from_seq": 0,
      "total_prompts": 5
    }
  }
}
```

#### Verify No Duplicates
```powershell
# Check for duplicate setup entries
(Get-Content test_v2.report.jsonl | jq -r 'select(.entry_type == "start_run setup")').Count
# Should be 1

# Check for duplicate init entries
(Get-Content test_v2.report.jsonl | jq -r 'select(.entry_type == "init")').Count
# Should be 1

# Check for duplicate attempt UUIDs
Get-Content test_v2.report.jsonl | jq -r 'select(.entry_type == "attempt") | .uuid' | Sort-Object | Group-Object | Where-Object Count -gt 1
# Should be empty (no output)
```

---

## Advanced Tests

### Test Multiple Resume Cycles

**Scenario**: Interrupt twice, resume twice

```powershell
# 1. Start scan
python -m garak -m test -p av_spam_scanning.EICAR,av_spam_scanning.GTUBE,packagehallucination --resumable --report_prefix multi_v2

# 2. Interrupt after EICAR (Ctrl+C)
# 3. Resume
python -m garak --resume <run-id>

# 4. Interrupt after GTUBE (Ctrl+C again)
# 5. Resume again
python -m garak --resume <run-id>

# 6. Let it complete packagehallucination
```

**Validation**:
```powershell
python test_resume_v2.py multi_v2.report.jsonl

# Check for 2 resume_info entries
Get-Content multi_v2.report.jsonl | jq 'select(.entry_type == "resume_info")' | Measure-Object
# Count should be 2
```

### Test with Real Models

Replace `test` with actual model:

```powershell
python -m garak `
    --model_type openai `
    --model_name gpt-3.5-turbo `
    --probes encoding.InjectAscii85,encoding.InjectBase64 `
    --config run.resumable=true `
    --report_prefix real_v2

# Interrupt after first probe completes
# Resume
python -m garak --resume <run-id>

# Validate
python test_resume_v2.py real_v2.report.jsonl
```

---

## Troubleshooting

### Issue: "No run_id found in init entry"
**Cause**: Report file may be from old Garak version

**Fix**:
```powershell
# Check init entry structure
Get-Content test_v2.report.jsonl | jq 'select(.entry_type == "init")' | ConvertTo-Json -Depth 10
```

If no `"run"` field, your Garak version predates the changes.

### Issue: "Multiple setup/init entries"
**Cause**: Files being overwritten instead of appended

**Debug**:
```powershell
# Check file mode in cli.py
Select-String -Path garak/cli.py -Pattern 'file_mode = "a"' -Context 2,2
```

Should show:
```python
if is_resuming:
    file_mode = "a"
```

### Issue: "start_time mismatch"
**Cause**: Original start_time not being preserved

**Debug**:
```powershell
# Check if parse_existing_report_metadata is called
Select-String -Path garak/cli.py -Pattern 'parse_existing_report_metadata' -Context 5,5

# Check if original_start_time set in _config.transient
Select-String -Path garak/cli.py -Pattern 'original_start_time' -Context 2,2
```

### Issue: "No resume_info entry"
**Cause**: Conditional logic not writing resume_info

**Debug**:
```powershell
# Find resume_info writing code
Select-String -Path garak/cli.py -Pattern 'resume_info' -Context 10,10
```

Should be inside:
```python
if not is_resuming:
    # Write setup/init
else:
    # Write resume_info  ← Should be here
```

---

## Success Criteria

✅ **Priority A - Preserve start_time**: Init and completion entries have matching start_time  
✅ **Priority B - True append mode**: Report has single setup/init, no duplicate attempts  
✅ **Priority C - Resume metadata**: resume_info entry documents the resume event

---

## Expected vs Actual

### Expected Behavior (v2.0)
```
Initial run:
- Creates test_v2.report.jsonl
- Writes: setup, init, attempts[0-4]

[Interrupt]

Resume:
- Opens test_v2.report.jsonl in APPEND mode
- Writes: resume_info, attempts[5-9], completion, digest
- Final file has ~15 entries
```

### Common Mistakes (Pre-v2.0)
```
Initial run:
- Creates test_v2.report.jsonl
- Writes: setup, init, attempts[0-4]

[Interrupt]

Resume:
- Creates NEW file (different run_id)
- Overwrites test_v2.report.jsonl
- Writes: setup, init, attempts[5-9], completion, digest
- Final file has ~13 entries (missing original attempts!)
```

---

## Quick Commands Cheat Sheet

```powershell
# Count entries
(Get-Content report.jsonl).Count

# Group by entry_type
Get-Content report.jsonl | jq -r '.entry_type' | Group-Object | Format-Table

# Extract specific entry type
Get-Content report.jsonl | jq 'select(.entry_type == "resume_info")'

# Check for duplicates
Get-Content report.jsonl | jq -r 'select(.entry_type == "attempt") | .uuid' | Group-Object | Where-Object Count -gt 1

# Compare start_time
Get-Content report.jsonl | jq 'select(.entry_type == "init" or .entry_type == "completion") | {entry_type, start_time}'

# Pretty print entire file
Get-Content report.jsonl | jq '.'

# Extract just attempt sequences
Get-Content report.jsonl | jq -r 'select(.entry_type == "attempt") | .seq' | Sort-Object
```

---

*Quick Test Guide v2.0*  
*For Garak Resume Continuity Enhancement*
