# Run ID Consistency and Probe Ordering Fixes - COMPLETE

## Issues Addressed

### 1. Hitlog run_id Mismatch - NEW RUN (FIXED) + RESUME (FIXED)

**Problem**: Hitlog entries showed different run_id than main report, INCLUDING on resume
- **New run**: Report used `2b0f2377...`, Hitlog used `87428f16...` (FIXED in v1)
- **Resume run**: EICAR used `0bac1a03...` (UUID), GTUBE used `garak-run-0bac1a03...-timestamp` (full) ❌

**Root Cause - New Runs (v1 fix)**:
1. `cli.py:756` generates UUID and sets `_config.transient.run_id`
2. `probewise.py:264` calls `resumeservice.initialize_new_run()` which generated a NEW UUID
3. `probewise.py:268` extracted this NEW UUID and overwrote `_config.transient.run_id`
4. Result: Hitlog used new UUID, report used old UUID

**Root Cause - Resumed Runs (v2 fix - THIS VERSION)**:
1. State file stores FULL run_id: `"run_id": "garak-run-<uuid>-<timestamp>"`
2. `cli.py:772` restored full run_id to `_config.transient.run_id` 
3. Hitlog wrote full run_id instead of just UUID
4. Result: Inconsistent format between new attempts (UUID) and resumed attempts (full run_id)

**Solution v1 (New Runs)**: Modified resumeservice to REUSE existing UUID
- Added `existing_uuid` parameter to `RunManager.generate_run_id()`
- Modified `probewise.py` to pass `_config.transient.run_id` to resumeservice
- Result: Same UUID flows through entire NEW run

**Solution v2 (Resumed Runs - THIS VERSION)**: Extract UUID on resume
- Modified `cli.py:772` to call `resumeservice.extract_uuid_from_run_id()` 
- Converts full run_id from state back to UUID before setting `transient.run_id`
- Result: Resumed attempts use same UUID format as new attempts

### 2. Probe Order Inconsistency (FIXED)

**Problem**: HTML/digest showed GTUBE first, then EICAR (reversed from probe_spec order)

**Root Cause**:
- `report.py:115` iterated via `for probe in self.scores.index:` (FIXED in v1)
- `report_digest.py:410` iterated from SQL query with no ordering (FIXED in v2)
- Pandas groupby and SQL queries don't preserve probe_spec order

**Solution v1 (report.py - AVID export)**: Respect probe_spec order in Report.export()
- Extract `plugins.probe_spec` from metadata
- Parse comma-separated spec into ordered list
- Iterate probes in spec order instead of DataFrame index order

**Solution v2 (report_digest.py - THIS VERSION)**: Respect probe_spec order in digest
- Extract `probespec` from `header_content` 
- Parse comma-separated spec into ordered list
- Sort `probe_result_summaries` by probe_spec index before iteration
- Result: Digest JSON and HTML both maintain EICAR, GTUBE order

## Changes Made - Version 2 (Resume Fix + Digest Ordering)

### File: `garak/cli.py` - Line 765

#### Extract UUID from full run_id on resume
```python
if state:
    if "report_dir" in state:
        _config.reporting.report_dir = state["report_dir"]
    if "report_prefix" in state:
        _config.reporting.report_prefix = state["report_prefix"]
    # Use the original run_id for report filename consistency
    if "run_id" in state:
        # Extract UUID from full run_id to maintain hitlog consistency
        # State stores full format "garak-run-<uuid>-<timestamp>"
        # but transient.run_id should be just the UUID for hitlog
        from garak import resumeservice
        full_run_id = state["run_id"]
        _config.transient.run_id = resumeservice.extract_uuid_from_run_id(full_run_id)
```

**Why**: State file contains full run_id format. On resume, we must extract just the UUID to maintain consistency with hitlog format.

### File: `garak/analyze/report_digest.py` - Line 408

#### Sort probes by probe_spec order in digest
```python
probe_result_summaries = _get_probe_result_summaries(cursor, probe_group)

# Sort probes by probe_spec order if available
probe_spec_order = []
if "probespec" in header_content and header_content["probespec"]:
    # Parse probe_spec: "av_spam_scanning.EICAR,av_spam_scanning.GTUBE"
    probe_spec_order = [p.strip() for p in header_content["probespec"].split(",")]

# Sort probe_result_summaries by probe_spec order
def probe_sort_key(item):
    probe_module, probe_class, _ = item
    probe_name = f"{probe_module}.{probe_class}"
    try:
        return probe_spec_order.index(probe_name)
    except (ValueError, AttributeError):
        return 999  # Put unspecified probes at end

if probe_spec_order:
    probe_result_summaries = sorted(probe_result_summaries, key=probe_sort_key)

for probe_module, probe_class, group_absolute_score in probe_result_summaries:
```

**Why**: SQL query doesn't preserve probe_spec order. Sort results before iteration to match vanilla garak output.

---

## Changes Made - Version 1 (New Run Fix)

#### 1. RunManager.generate_run_id() - Line 52
```python
def generate_run_id(self, existing_uuid: str = None) -> str:
    """Generate unique run ID with timestamp.
    
    Args:
        existing_uuid: Optional UUID to use instead of generating a new one.
                      Useful for maintaining consistency with transient.run_id.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_uuid = existing_uuid if existing_uuid else str(uuid.uuid4())
    return f"garak-run-{run_uuid}-{timestamp}"
```

#### 2. initialize_new_run() - Line 446
```python
def initialize_new_run(probenames: List[str], generator=None, existing_run_uuid: str = None) -> str:
    """Initialize a new resumable run.
    
    Args:
        existing_run_uuid: Optional existing UUID from _config.transient.run_id to maintain consistency
    """
    return initialize_new_run_with_attempts(probenames, generator, existing_run_uuid=existing_run_uuid)
```

#### 3. initialize_new_run_with_attempts() - Line 744
```python
def initialize_new_run_with_attempts(probenames: List[str], generator=None, existing_run_uuid: str = None) -> str:
    """Initialize a new resumable run with attempt tracking support.
    
    Args:
        existing_run_uuid: Optional existing UUID from _config.transient.run_id to maintain consistency
    """
    run_id = _run_manager.generate_run_id(existing_uuid=existing_run_uuid)
```

### File: `garak/harnesses/probewise.py`

#### Line 264 - Pass existing UUID to resumeservice
```python
if _config.run.resumable:
    # Pass existing transient.run_id to maintain consistency across reports/hitlog
    existing_uuid = str(_config.transient.run_id) if _config.transient.run_id else None
    run_id = resumeservice.initialize_new_run(probenames, model, existing_run_uuid=existing_uuid)
    # Extract UUID from full run_id - it should match the existing UUID we passed in
    uuid_part = resumeservice.extract_uuid_from_run_id(run_id)
    _config.transient.run_id = uuid_part
```

### File: `garak/report.py`

#### Line 115 - Order probes by probe_spec
```python
# Determine probe order: use original probe_spec order if available, else DataFrame index order
probe_order = list(self.scores.index)
if self.metadata is not None and "plugins.probe_spec" in self.metadata:
    probe_spec = self.metadata.get("plugins.probe_spec", "")
    if probe_spec:
        # probe_spec format: "malwaregen.Eicar,malwaregen.GTUBE"
        spec_probes = [p.strip() for p in probe_spec.split(",")]
        # Filter to only probes that actually ran
        probe_order = [p for p in spec_probes if p in self.scores.index]
        # Add any probes that ran but weren't in spec
        for p in self.scores.index:
            if p not in probe_order:
                probe_order.append(p)

for probe in probe_order:
    # ... rest of digest generation
```

## Resume Safety Analysis - Version 2

**CRITICAL CONSTRAINT**: "EVERYTIME YOU MAKE CHANGES IN CODE, OUR TOOL LOSES ITS ABILITY TO RESUME"

### Changes Are Safe Because:

1. **State persistence logic UNCHANGED**:
   - No modifications to state.json structure
   - No changes to save_state() or load_state()
   - No changes to mark_attempt_complete_by_seq()
   - State tracking granularity preserved

2. **Only UUID extraction added, not state tracking**:
   - v1: Pass existing UUID to initialize_new_run() (new runs)
   - v2: Extract UUID from full run_id on resume (resumed runs)
   - State save/load still works identically
   - Resume still restores run_id from state

3. **Digest ordering is purely presentational**:
   - v1: Report.export() sorts probes before iteration
   - v2: build_digest() sorts probes before iteration
   - Doesn't affect eval calculations or state persistence
   - Only changes output formatting order

4. **Backward compatible**:
   - All parameters are optional (defaults to None)
   - If probe_spec missing, uses original order
   - Existing state files still load correctly
   - extract_uuid_from_run_id() handles both UUID and full format

5. **Resume flow preserved**:
   - cli.py loads state → extracts UUID → sets transient.run_id
   - probewise.py checks resumeservice.enabled() → skips initialization
   - Attempts resume from correct position
   - No re-execution of completed attempts

### Verification Steps:

1. **Test new run**:
   ```bash
   python -m garak -m test -p malwaregen --report_prefix new_run
   ```
   - Verify hitlog run_id matches report run_id
   - Verify probe order is EICAR, GTUBE in digest

2. **Test resume** (interrupt and resume):
   ```bash
   # Start run (Ctrl+C after first probe)
   python -m garak -m test -p malwaregen --resumable
   
   # Resume
   python -m garak --resume garak-run-<uuid>-<timestamp>
   ```
   - Verify state loads correctly
   - Verify run_id preserved across resume
   - Verify attempts don't re-execute

3. **Test probe ordering persistence**:
   ```bash
   python -m garak -m test -p malwaregen.GTUBE,malwaregen.Eicar
   ```
   - Verify digest shows GTUBE first (as specified), not EICAR

## Expected Outcomes - Version 2

✅ **Hitlog consistency (NEW RUNS)**: All report files use same UUID  
✅ **Hitlog consistency (RESUMED RUNS)**: Resumed attempts use same UUID format  
✅ **Probe ordering (AVID export)**: Report.export() respects probe_spec order  
✅ **Probe ordering (Digest/HTML)**: build_digest() respects probe_spec order  
✅ **Resume functionality**: State tracking unaffected  
✅ **Backward compatibility**: Existing state files load correctly  
✅ **No breaking changes**: Optional parameters with safe defaults

## Testing Checklist - Version 2

**New Run Tests**:
- [ ] New run shows consistent UUID across report.jsonl and hitlog.jsonl
- [ ] Probe order in digest matches probe_spec order (EICAR, GTUBE)
- [ ] Probe order in HTML matches probe_spec order
- [ ] seq numbering still resets to 0 per probe

**Resume Tests**:
- [ ] Interrupt run after first probe completes
- [ ] Resume shows consistent UUID in hitlog (no "garak-run-..." format)
- [ ] Resume loads state correctly (no re-execution)
- [ ] Resumed attempts have same run_id format as original attempts
- [ ] Probe order preserved after resume
- [ ] Attempt-level granularity still works

**Edge Cases**:
- [ ] Resume with missing probe_spec (should use default order)
- [ ] Resume with malformed state file (should fail gracefully)
- [ ] Multiple resume cycles preserve UUID consistency
