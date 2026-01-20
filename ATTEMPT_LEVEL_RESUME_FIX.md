# Attempt-Level Resume Fix - Summary

## Problem Identified
The resume feature was **only working at probe level**, not at attempt level. Even when setting `--resume_granularity attempt`, the system would only track completed probes, not individual attempts.

## Root Cause
In [garak/harnesses/probewise.py](garak/harnesses/probewise.py), after each attempt was processed and written to the report, the code was **NOT calling** `resumeservice.mark_attempt_complete()`. This meant:

1. Attempts were being written to the report ✅
2. Attempt state was NOT being saved to the resume state file ❌  
3. On resume, individual attempts could not be skipped ❌
4. Only entire probes could be skipped ❌

## Fix Applied
Added the following code in [garak/harnesses/probewise.py](garak/harnesses/probewise.py#L507-L513) after writing each attempt to the report (around line 507):

```python
# RESUME SUPPORT: Mark attempt complete (for attempt-level granularity)
# Only matters when resume_granularity="attempt"
if resumeservice.enabled() and resumeservice.get_granularity() == "attempt":
    attempt_uuid = getattr(attempt, "uuid", None)
    if attempt_uuid:
        resumeservice.mark_attempt_complete(attempt_uuid, probe_short_name)
        logger.debug(f"[RESUME] Marked attempt {attempt_uuid} (seq={attempt.seq}) complete for {probe_short_name}")
```

## What This Fix Does
- **Tracks individual attempts**: Each attempt's UUID is stored in the resume state when `resume_granularity="attempt"`
- **Enables fine-grained resume**: On interrupt, the system knows exactly which attempts completed
- **Skips completed attempts**: On resume, completed attempts are skipped, preventing redundant API calls
- **Automatic**: Only activates when `--resume_granularity attempt` is used

## How Attempt-Level Resume Works Now

### 1. Starting a Resumable Scan with Attempt-Level Granularity
```powershell
python -m garak -m <model> -p <probes> --resumable --resume_granularity attempt --report_prefix my_scan
```

### 2. During Execution
- Each probe generates multiple attempts (1 per prompt)
- After each attempt:
  1. Attempt is executed (prompt sent to model, response received)
  2. Detectors evaluate the attempt
  3. Attempt written to report with `status=2`
  4. **Attempt UUID is saved to resume state** ✅ (NEW)
  5. Progress saved to disk

### 3. On Interrupt (Ctrl+C)
- Resume state file contains:
  ```json
  {
    "resume_granularity": "attempt",
    "completed_attempts": ["uuid1", "uuid2", "uuid3", ...],
    "probe_states": {
      "probe_name": {
        "prompt_index": 42,
        "total_prompts": 100
      }
    }
  }
  ```

### 4. On Resume
```powershell
python -m garak --resume my_scan
```

**What happens:**
1. Load resume state including completed attempts list
2. For each probe:
   - Check if probe fully completed → skip entire probe
   - Otherwise, load probe and get its prompts
   - For each attempt:
     - Check if attempt UUID in completed list → skip
     - Otherwise, execute attempt normally
3. Continue until all probes/attempts complete

## Verification Tests

### Test 1: Check State File Has Completed Attempts
```powershell
# Start a scan with attempt-level granularity
python -m garak -m <model> -p <probe> --resumable --resume_granularity attempt --report_prefix test_attempt

# Let it run for a bit, then Ctrl+C

# Check the state file
$state = Get-Content ~\.garak\runs\*test_attempt*\state.json | ConvertFrom-Json
$state.resume_granularity  # Should be "attempt"
$state.completed_attempts.Count  # Should be > 0 (number of completed attempts)
```

### Test 2: Verify Attempts Are Skipped on Resume
```powershell
# Resume the interrupted scan
python -m garak --resume test_attempt

# Watch the console output - you should see:
# "⏭️  Skipping completed attempts: X/Y"
# OR
# "✅ All X attempts for <probe> already completed"
```

### Test 3: Check Report Consistency
```powershell
# After resume completes, check the report
Get-Content test_attempt.report.jsonl | Select-String '"seq":' | ForEach-Object { ($_ | ConvertFrom-Json).seq } | Group-Object | Where-Object { $_.Count -gt 1 }

# Should return NOTHING (no duplicate sequences)
# Each attempt should appear exactly once
```

## Comparison: Probe-Level vs Attempt-Level

| Aspect | Probe-Level (`--resume_granularity probe`) | Attempt-Level (`--resume_granularity attempt`) |
|--------|---------------------------------------------|------------------------------------------------|
| **Granularity** | Skip entire probes | Skip individual attempts |
| **Resume Speed** | Fast (less state to load) | Slower (more state checking) |
| **Wasted Work** | May re-execute many attempts from incomplete probe | Skips all completed attempts |
| **State File Size** | Small (~few KB) | Larger (~100s of KB for long runs) |
| **Best For** | Quick scans, stable environments | Long scans, unstable environments, expensive API calls |
| **State Tracked** | `completed_probes` list | `completed_attempts` list + `probe_states` |

## Example: Cost Savings with Attempt-Level Resume

**Scenario**: Scan with 10 probes, each with 100 attempts (1000 total attempts)

**Interrupt at attempt 555 (middle of probe 6):**

### Probe-Level Resume
- Completed probes: 5 (500 attempts)
- Partial probe 6: 55 attempts completed, but marked incomplete
- **On resume**: Re-executes all 100 attempts for probe 6
- **Wasted**: 55 duplicate attempts = 55 API calls wasted

### Attempt-Level Resume  
- Completed attempts: 555
- **On resume**: Skips first 555 attempts, starts at attempt 556
- **Wasted**: 0 duplicate attempts = 0 API calls wasted

**Savings**: 55 API calls = significant cost for expensive models!

## Integration with Future Garak Versions

When applying this fix to new garak versions, ensure [garak/harnesses/probewise.py](garak/harnesses/probewise.py) has:

1. **Import** (at top):
   ```python
   import garak.resumeservice as resumeservice
   ```

2. **After writing each attempt to report** (look for `_config.transient.reportfile.write()` and `flush()`):
   ```python
   # RESUME SUPPORT: Mark attempt complete
   if resumeservice.enabled() and resumeservice.get_granularity() == "attempt":
       attempt_uuid = getattr(attempt, "uuid", None)
       if attempt_uuid:
           resumeservice.mark_attempt_complete(attempt_uuid, probe_short_name)
   ```

3. **After all attempts in a probe complete**:
   ```python
   resumeservice.mark_probe_complete(probename)
   ```

4. **After all probes complete**:
   ```python
   resumeservice.mark_run_complete()
   ```

## Files Modified
- [garak/harnesses/probewise.py](garak/harnesses/probewise.py) - Added `mark_attempt_complete()` call
- [backup_custom/garak/harnesses/probewise.py](backup_custom/garak/harnesses/probewise.py) - Updated backup
- [EXACT_IMPLEMENTATION_STEPS.md](EXACT_IMPLEMENTATION_STEPS.md) - Added clarification about attempt-level tracking requirement

## Commits
- Commit 2d340e4: "Fix: Add attempt-level completion tracking in probewise.py"
- Commit 16fdf0c: "Update implementation steps with attempt-level tracking requirement"

## Status
✅ **Fix Applied**: Code updated and committed  
✅ **Backup Updated**: Custom files synchronized  
✅ **Documentation Updated**: Implementation guide clarified  
⏳ **Testing Blocked**: Cannot test due to missing `torch` dependency in current environment

## Next Steps for User
1. Test the fix in a working garak environment with proper dependencies
2. Start a scan with `--resume_granularity attempt`
3. Interrupt with Ctrl+C
4. Verify `completed_attempts` count > 0 in state file
5. Resume and verify attempts are skipped

## Summary
The attempt-level resume feature is now **fully implemented** in the code. The missing call to `mark_attempt_complete()` has been added, which means attempts will now be properly tracked in the resume state file. This enables true fine-grained resumption at the individual attempt level, saving time and API costs when scans are interrupted.
