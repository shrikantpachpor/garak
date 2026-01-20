# EXACT IMPLEMENTATION STEPS - Copy & Execute

## Setup (5 minutes)

### Step 0: Download and Prepare Fresh Garak
```powershell
# Create working directory
cd e:\SHRIKANT\projects
mkdir garak-with-resume
cd garak-with-resume

# Clone fresh garak
git clone https://github.com/NVIDIA/garak.git .

# Initialize git for tracking
git init
git add .
git commit -m "Fresh garak baseline"

# Verify it works
python -m garak --version
# Expected output: garak LLM vulnerability scanner v0.X.X
```

### Step 1: Copy Compatibility Checker (1 minute)
```powershell
# Copy checker from your current implementation
Copy-Item e:\SHRIKANT\projects\garak-resume-2\check_compatibility.py .

# Run compatibility check
python check_compatibility.py
# Expected: Score 80%+ (✅ COMPATIBLE or better)
# If score < 80%, STOP and review warnings
```

---

## Implementation (30-90 minutes)

### Step 2: Add resumeservice.py (Zero Risk - 2 minutes)
```powershell
# Copy the core resume module
Copy-Item e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\resumeservice.py garak\resumeservice.py

# Verify syntax
python -m py_compile garak\resumeservice.py
# No output = success

# Test import
python -c "import garak.resumeservice; print('✅ Module loads')"

# Commit
git add garak\resumeservice.py
git commit -m "Add resumeservice.py - core resume module"
```

---

### Step 3: Modify _config.py (Low Risk - 5 minutes)

#### 3A: Add to run_params
```powershell
# Open file
code garak\_config.py
```

**Find this line** (around line 38):
```python
run_params = "seed deprefix eval_threshold generations probe_tags interactive system_prompt".split()
```

**Replace with**:
```python
run_params = "seed deprefix eval_threshold generations probe_tags interactive system_prompt resumable resume_granularity".split()
```

#### 3B: Add defaults
**Find this section** (around line 121):
```python
run.seed = None
run.soft_probe_prompt_cap = 64
run.target_lang = "en"
run.langproviders = []
```

**Add after it**:
```python
run.resumable = False
run.resume_granularity = "probe"
```

#### 3C: Verify and Commit
```powershell
# Save file, then verify
python -m py_compile garak\_config.py
python -c "from garak import _config; _config.load_base_config(); print(f'✅ resumable={_config.run.resumable}, granularity={_config.run.resume_granularity}')"
# Expected: ✅ resumable=False, granularity=probe

# Commit
git add garak\_config.py
git commit -m "Add resume configuration parameters"
```

---

### Step 4: Modify cli.py (Low Risk - 15 minutes)

```powershell
# For simplicity, use the complete custom version
Copy-Item e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\cli.py garak\cli.py -Force

# Verify
python -m py_compile garak\cli.py
python -m garak --help | Select-String "resumable|resume|list_runs"
# Should show resume-related options

# Commit
git add garak\cli.py
git commit -m "Add resume CLI interface"
```

**Alternative Manual Method** (if you want to merge carefully):
```powershell
# Open both files side by side
code --diff e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\cli.py garak\cli.py

# Copy these sections from backup to fresh:
# 1. parse_existing_report_metadata() function (before main())
# 2. Resume argument definitions in parser.add_argument calls
# 3. --list_runs handler (after args = parser.parse_args())
# 4. --delete_run handler  
# 5. --resume handler
```

---

### Step 5: Modify command.py (Medium Risk - 10 minutes)

```powershell
# Use custom version for simplicity
Copy-Item e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\command.py garak\command.py -Force

# Verify
python -m py_compile garak\command.py
python -c "from garak import command; print('✅ Command module loads')"

# Commit
git add garak\command.py
git commit -m "Add resume cleanup and completion logic"
```

**Alternative Manual Method**:
```powershell
code --diff e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\command.py garak\command.py

# Add these to fresh command.py:
# 1. remove_trailing_metadata_entries() function (before end_run())
# 2. Cleanup call in end_run() (after logging.info("run complete"))
# 3. start_time preservation in completion entry
```

---

### Step 6: Modify report_digest.py (Medium Risk - 10 minutes)

```powershell
# Use custom version
Copy-Item e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\analyze\report_digest.py garak\analyze\report_digest.py -Force

# Verify
python -m py_compile garak\analyze\report_digest.py
python -c "from garak.analyze import report_digest; print('✅ Report digest module loads')"

# Commit
git add garak\analyze\report_digest.py
git commit -m "Add smart digest replacement logic"
```

**Alternative Manual Method**:
```powershell
code --diff e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\analyze\report_digest.py garak\analyze\report_digest.py

# Replace append_report_object() function with version from backup
```

---

### Step 7: Modify probewise.py (High Risk - 15 minutes)

```powershell
# Check if structures are similar
(Get-Content garak\harnesses\probewise.py).Count
(Get-Content e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\harnesses\probewise.py).Count

# If custom version is much larger (500+ vs 100-150 lines):
Copy-Item e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\harnesses\probewise.py garak\harnesses\probewise.py -Force

# Verify
python -m py_compile garak\harnesses\probewise.py
python -c "from garak.harnesses import probewise; print('✅ Probewise harness loads')"

# Commit
git add garak\harnesses\probewise.py
git commit -m "Add resume integration to probewise harness"
```

**CRITICAL for Attempt-Level Resumption:**

The probewise.py file MUST call `resumeservice.mark_attempt_complete()` after writing each attempt to the report. This is what enables attempt-level granularity to work correctly.

**Key integration points in probewise.py:**
1. Import: `import garak.resumeservice as resumeservice` (at top)
2. In run() method: Check resume state before probe execution
3. Skip completed probes/attempts based on state
4. **CRITICAL**: After writing each attempt (status=2), call:
   ```python
   if resumeservice.enabled() and resumeservice.get_granularity() == "attempt":
       attempt_uuid = getattr(attempt, "uuid", None)
       if attempt_uuid:
           resumeservice.mark_attempt_complete(attempt_uuid, probe_short_name)
   ```
5. Mark probes complete after all attempts finish

**If structures differ significantly** (manual integration needed):
```powershell
code --diff e:\SHRIKANT\projects\garak-resume-2\backup_custom\garak\harnesses\probewise.py garak\harnesses\probewise.py

# Key changes to add (in order of location in file):
# 1. Import resumeservice at top
# 2. In run() - Initialize/load resume state
# 3. In run() - Skip completed probes  
# 4. In run() - Check for incomplete attempts on resume
# 5. In run() - For each attempt after detector evaluation:
#    - Write attempt with status=2 to report
#    - Call mark_attempt_complete() if granularity=="attempt"
# 6. In run() - Mark probe complete after all attempts
# 7. In run() - Mark run complete after all probes
```

---

## Validation (10 minutes)

### Test 1: Basic Functionality
```powershell
# Test garak starts
python -m garak --version
# Expected: garak LLM vulnerability scanner v0.X.X

# Test resume options visible
python -m garak --help | Select-String "resumable|resume|list_runs"
# Expected: Shows --resumable, --resume, --list_runs, --delete_run

# Test list runs (even if empty)
python -m garak --list_runs
# Expected: Shows "No resumable runs found" or lists existing runs
```

### Test 2: Create Resumable Scan
```powershell
# Start a small resumable scan
python -m garak -m test -p test.Blank --resumable --report_prefix validation_test --generations 5

# Let it run for 10-15 seconds, then press Ctrl+C

# Check it was saved
python -m garak --list_runs
# Expected: Shows validation_test in list
```

### Test 3: Resume Scan
```powershell
# Resume the interrupted scan
python -m garak --resume validation_test

# Let it complete (should be quick)
```

### Test 4: Verify Report Quality
```powershell
# Check report has single run_id
Get-Content validation_test.report.jsonl | Select-String '"run":' | Select-Object -First 5
# All lines should show same run ID

# Count digest entries (should be 1)
(Get-Content validation_test.report.jsonl | Select-String 'entry_type.*digest').Count
# Expected: 1

# View completion entry
Get-Content validation_test.report.jsonl | Select-String 'entry_type.*completion' | ConvertFrom-Json | Format-List
# Should show start_time and end_time
```

---

## Final Verification Checklist

Run all these commands - all should succeed:

```powershell
# Syntax checks
python -m py_compile garak\resumeservice.py
python -m py_compile garak\cli.py
python -m py_compile garak\command.py
python -m py_compile garak\_config.py
python -m py_compile garak\analyze\report_digest.py
python -m py_compile garak\harnesses\probewise.py

# Import checks
python -c "import garak.resumeservice"
python -c "from garak import cli"
python -c "from garak import command"
python -c "from garak import _config"
python -c "from garak.analyze import report_digest"
python -c "from garak.harnesses import probewise"

# Functionality checks
python -m garak --version
python -m garak --help | Select-String "resume"
python -m garak --list_runs

# Success indicators:
# ✅ All py_compile commands complete with no output
# ✅ All imports succeed
# ✅ --version shows garak version
# ✅ --help shows resume options
# ✅ --list_runs executes (shows list or "no runs found")
```

---

## Troubleshooting

### Issue: AttributeError: 'GarakSubConfig' has no attribute 'resumable'
**Fix**:
```powershell
# Check _config.py has defaults
python -c "from garak import _config; print(hasattr(_config.run, 'resumable'))"
# Should print: True

# If False, add to _config.py:
# run.resumable = False
# run.resume_granularity = "probe"
```

### Issue: resume options not in --help
**Fix**:
```powershell
# Verify cli.py has resume arguments
Select-String -Path garak\cli.py -Pattern "parser.add_argument.*resume"
# Should show multiple matches

# If none, cli.py wasn't properly modified - redo Step 4
```

### Issue: ImportError: No module named 'resumeservice'
**Fix**:
```powershell
# Check file exists
Test-Path garak\resumeservice.py
# Should be True

# If False, redo Step 2
```

### Issue: Resume doesn't preserve run_id
**Fix**:
```powershell
# Check command.py has start_time handling
Select-String -Path garak\command.py -Pattern "original_start_time"
# Should show matches

# Check cli.py has parse_existing_report_metadata
Select-String -Path garak\cli.py -Pattern "parse_existing_report_metadata"
# Should show matches

# If missing, redo Steps 4 and 5
```

---

## Quick Reference Commands

### Daily Usage
```powershell
# List all resumable runs
python -m garak --list_runs

# Start resumable scan
python -m garak -m <model> -p <probes> --resumable --report_prefix <name>

# Resume interrupted scan
python -m garak --resume <run-id or prefix>

# Delete saved run
python -m garak --delete_run <run-id>
```

### Verification
```powershell
# Check resume is working
python check_compatibility.py

# View report run_id consistency
Get-Content <report>.report.jsonl | Select-String '"run":' | Select-Object -Unique

# Count digests (should be 1)
(Get-Content <report>.report.jsonl | Select-String 'entry_type.*digest').Count
```

---

## Time Estimates

| Step | Time | Risk |
|------|------|------|
| Setup & Check | 5 min | None |
| resumeservice.py | 2 min | Low |
| _config.py | 5 min | Low |
| cli.py | 15 min | Low |
| command.py | 10 min | Medium |
| report_digest.py | 10 min | Medium |
| probewise.py | 15 min | High |
| Validation | 10 min | None |
| **TOTAL** | **60-90 min** | - |

---

## Success Criteria

✅ **Implementation Complete When:**
- [ ] All 6 files modified/added
- [ ] All syntax checks pass
- [ ] All import checks pass
- [ ] `python -m garak --version` works
- [ ] `python -m garak --help` shows resume options
- [ ] `python -m garak --list_runs` executes
- [ ] Can start scan with `--resumable`
- [ ] Can interrupt with Ctrl+C
- [ ] `--list_runs` shows the interrupted run
- [ ] Can resume with `--resume <id>`
- [ ] Report shows single run_id
- [ ] Report has only 1 digest entry
- [ ] Normal garak scans still work

---

## Git History (For Reference)

After complete implementation, your git log should look like:
```
* Add resume integration to probewise harness
* Add smart digest replacement logic
* Add resume cleanup and completion logic
* Add resume CLI interface
* Add resume configuration parameters
* Add resumeservice.py - core resume module
* Fresh garak baseline
```

---

**READY TO START?**

1. Copy these steps to a text file
2. Execute commands in order
3. Validate after each step
4. Commit after each file
5. Test at the end

Total time: 60-90 minutes for full implementation
