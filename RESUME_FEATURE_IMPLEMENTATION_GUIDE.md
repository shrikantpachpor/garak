# Resume Feature Implementation Guide
## How to Apply Resume Feature to Any Fresh Garak Version

This guide explains how to implement the resume feature in any fresh garak installation, ensuring compatibility and avoiding breaking changes.

---

## 🎯 Overview

The resume feature consists of:
1. **One new module** (resumeservice.py) - Independent, no conflicts
2. **Five modified files** - Surgical changes to existing code
3. **Well-defined integration points** - Minimal coupling with core garak

---

## 📋 Pre-Implementation Checklist

Before starting, verify:
- [ ] Fresh garak downloaded and working: `python -m garak --version`
- [ ] Python 3.8+ installed
- [ ] Git initialized: `git init` (for tracking changes)
- [ ] Backup created: `cp -r garak garak.backup`

---

## 🔍 Understanding the Changes

### Change Categories

| Category | Files | Risk Level | Coupling |
|----------|-------|------------|----------|
| **New Module** | resumeservice.py | ⚠️ Low | None - standalone |
| **CLI Integration** | cli.py | ⚠️ Low | Argument parsing only |
| **Configuration** | _config.py | ⚠️ Low | 2 new parameters |
| **Lifecycle Hooks** | command.py | 🟡 Medium | end_run() modification |
| **Report Handling** | report_digest.py | 🟡 Medium | digest append logic |
| **Harness Integration** | probewise.py | 🔴 High | Core execution flow |

### Integration Points (Where Fresh Garak Touches Our Code)

1. **CLI Arguments** → Resume arguments added to argparse
2. **Config Loading** → Resume params loaded with other config
3. **Run Start** → Resume state loaded if --resume flag
4. **Probe Execution** → State checked before each probe/attempt
5. **Run End** → State saved, cleanup performed
6. **Report Generation** → Metadata preserved for continuity

---

## 📝 Step-by-Step Implementation

### STEP 1: Add the New Module (Zero Risk)

**File**: `garak/resumeservice.py`

**Action**: Copy entire file from backup
```powershell
Copy-Item backup_custom/garak/resumeservice.py garak/resumeservice.py
```

**Why Safe**: 
- Completely new file, no conflicts possible
- Self-contained module with no dependencies on modified core
- Other files import it, but it doesn't import modified code

**Validation**:
```powershell
python -c "import garak.resumeservice; print('✅ Module loads')"
```

---

### STEP 2: Add Configuration Parameters

**File**: `garak/_config.py`

**What to Add**: Two configuration parameters

**Location**: Find this section (around line 121):
```python
run.seed = None
run.soft_probe_prompt_cap = 64
run.target_lang = "en"
run.langproviders = []
```

**Add After It**:
```python
run.resumable = False  # Enable resumable scans
run.resume_granularity = "probe"  # Default: 'probe' or 'attempt'
```

**Also Add to run_params** (around line 38):
```python
# Find this line:
run_params = "seed deprefix eval_threshold generations probe_tags interactive system_prompt".split()

# Change to:
run_params = "seed deprefix eval_threshold generations probe_tags interactive system_prompt resumable resume_granularity".split()
```

**Why Safe**:
- Just adding new config parameters, not modifying existing ones
- Default values ensure no behavior change unless explicitly enabled

**Validation**:
```python
python -c "from garak import _config; _config.load_base_config(); print(f'resumable={_config.run.resumable}, granularity={_config.run.resume_granularity}')"
```

**Expected**: `resumable=False, granularity=probe`

---

### STEP 3: Add CLI Arguments

**File**: `garak/cli.py`

**What to Add**: Command-line argument definitions

#### 3A. Add Helper Function

**Location**: Before `def main()` function (around line 40)

**Add This Function**:
```python
def parse_existing_report_metadata(report_path):
    """Parse existing report to extract original run_id and start_time.
    
    Args:
        report_path: Path to existing report.jsonl file
        
    Returns:
        Tuple of (run_id, start_time) or (None, None) if not found
    """
    import os
    import json
    import logging
    
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

**Why Safe**: New function, doesn't modify existing code

#### 3B. Add Argument Definitions

**Location**: In `main()`, find where other arguments are defined (after `parser.add_argument("--config"...)`)

**Add These Arguments**:
```python
parser.add_argument(
    "--resumable",
    action="store_true",
    default=_config.run.resumable,
    help="Enable resumable scans (default: disabled)",
)
parser.add_argument(
    "--resume_granularity",
    "--resume-granularity",
    type=str,
    choices=["probe", "attempt"],
    default=_config.run.resume_granularity,
    help="Granularity for resume: 'probe' (default) or 'attempt'",
)
parser.add_argument(
    "--resume",
    type=str,
    help="Resume a previous run by run ID",
)
parser.add_argument(
    "--list_runs",
    action="store_true",
    help="List all resumable runs",
)
parser.add_argument(
    "--delete_run",
    type=str,
    help="Delete a saved run state by run ID",
)
```

**Why Safe**: 
- Only adds new arguments, doesn't change existing ones
- Uses standard argparse patterns

#### 3C. Add Command Handlers

**Location**: In `main()`, after `args = parser.parse_args()` (around line 370)

**Add These Handlers**:
```python
# Handle --list_runs
if hasattr(args, 'list_runs') and args.list_runs:
    try:
        from garak import resumeservice
        print("\n📋 Resumable Runs:")
        print("=" * 80)
        runs = resumeservice.list_runs()
        if not runs:
            print("No resumable runs found.")
        else:
            for run in runs:
                print(f"  Run ID: {run.get('run_id', 'unknown')}")
                print(f"    Started: {run.get('start_time', 'unknown')}")
                print(f"    Granularity: {run.get('granularity', 'probe')}")
                print(f"    Progress: {run.get('progress', 'unknown')}")
                print()
        sys.exit(0)
    except Exception as e:
        print(f"Error listing runs: {e}")
        sys.exit(1)

# Handle --delete_run
if hasattr(args, 'delete_run') and args.delete_run:
    try:
        from garak import resumeservice
        if resumeservice.delete_run(args.delete_run):
            print(f"✅ Deleted run: {args.delete_run}")
        else:
            print(f"❌ Failed to delete run: {args.delete_run}")
        sys.exit(0)
    except Exception as e:
        print(f"Error deleting run: {e}")
        sys.exit(1)

# Handle --resume
if hasattr(args, 'resume') and args.resume:
    import garak.resumeservice as resumeservice
    _config.transient.resume_run_id = args.resume
    resumeservice.load()
    state = resumeservice.get_state()
    
    if state:
        # Parse existing report to get original run_id and start_time
        report_dir = _config.transient.data_dir / _config.reporting.report_dir
        report_prefix = _config.reporting.report_prefix or f"garak.{args.resume}"
        expected_report_path = str(report_dir / f"{report_prefix}.report.jsonl")
        
        original_run_id, original_start_time = parse_existing_report_metadata(expected_report_path)
        if original_run_id:
            _config.transient.run_id = original_run_id
            logging.info(f"Resuming with original run_id: {original_run_id}")
        if original_start_time:
            _config.transient.original_start_time = original_start_time
            logging.info(f"Preserving original start_time: {original_start_time}")
        
        print(resumeservice.get_startup_message())
```

**Why Safe**: 
- Uses early exits (sys.exit) for command-only operations
- Only executes when specific flags present
- Doesn't interfere with normal garak flow

**Validation**:
```powershell
python -m garak --help | Select-String "resume"
# Should show resume-related options
```

---

### STEP 4: Modify Report Digest Handling

**File**: `garak/analyze/report_digest.py`

**What to Modify**: The `append_report_object()` function

**Find This Function** (around line 365):
```python
def append_report_object(reportfile: IO, object: dict):
    """Append a report object to the JSONL file."""
    # ... existing code ...
```

**Replace With**:
```python
def append_report_object(reportfile: IO, object: dict):
    """Append a report object to the JSONL file.
    
    If the object is a digest entry and one already exists, it will be replaced
    rather than appended to avoid duplication.
    """
    import tempfile
    import os
    import json
    import logging
    
    # If this is a digest, replace existing one
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
            logging.warning(f"Could not filter existing digest: {e}")
    
    # Now append the new entry
    end_val = reportfile.seek(0, os.SEEK_END)
    if end_val > 0:
        reportfile.seek(end_val - 1)
        last_char = reportfile.read()
        if last_char not in "\n\r":
            reportfile.write("\n")
    reportfile.write(json.dumps(object, ensure_ascii=False) + "\n")
```

**Why This Change**:
- Prevents duplicate digest entries when resuming
- Replaces old completion/digest with new ones
- Preserves all other report entries

**Risk**: 🟡 Medium
- Modifies file I/O logic
- Could affect report generation if file is locked/corrupted
- Protected by try-except blocks

**Validation**:
```python
python -c "from garak.analyze import report_digest; print('✅ Module loads')"
```

---

### STEP 5: Modify Run Lifecycle

**File**: `garak/command.py`

**What to Modify**: The `end_run()` function

#### 5A. Add Cleanup Helper Function

**Location**: Before `end_run()` function

**Add This Function**:
```python
def remove_trailing_metadata_entries(report_path):
    """Remove trailing completion and digest entries from report file."""
    import os
    import json
    import tempfile
    import logging
    
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

#### 5B. Modify end_run() Function

**Find**: The `end_run()` function (around line 155)

**At the Start of the Function, After** `logging.info("run complete, ending")`:

**Add**:
```python
    # Remove old completion/digest entries if resuming
    is_resuming = hasattr(_config.transient, "resume_run_id") and _config.transient.resume_run_id
    if is_resuming and hasattr(_config.transient, 'report_filename'):
        remove_trailing_metadata_entries(_config.transient.report_filename)
```

**Find the Completion Entry Creation** (looks like):
```python
    end_object = {
        "entry_type": "completion",
        "end_time": datetime.datetime.now().isoformat(),
        "run": _config.transient.run_id,
    }
```

**Replace With**:
```python
    # Use original start_time if available
    start_time = (_config.transient.original_start_time 
                  if hasattr(_config.transient, "original_start_time") and _config.transient.original_start_time
                  else _config.transient.starttime_iso)
    
    end_object = {
        "entry_type": "completion",
        "start_time": start_time,  # Add original start time
        "end_time": datetime.datetime.now().isoformat(),
        "run": _config.transient.run_id,
    }
```

**Why These Changes**:
- Cleanup prevents duplicate completion/digest entries
- start_time preservation ensures report continuity
- Only affects resumed runs, normal runs unchanged

**Risk**: 🟡 Medium
- Modifies critical run lifecycle
- Protected by hasattr checks and try-except

---

### STEP 6: Integrate with Probe Execution

**File**: `garak/harnesses/probewise.py`

**This is the Most Complex Integration**

**Risk**: 🔴 High - Modifies core execution flow

#### Option A: Use Your Custom Version (Recommended)

If fresh garak's probewise.py structure is similar:

```powershell
# Compare line counts
wc -l garak/harnesses/probewise.py
wc -l backup_custom/garak/harnesses/probewise.py

# If custom is much larger (500+ lines vs 100-150), use custom:
Copy-Item backup_custom/garak/harnesses/probewise.py garak/harnesses/probewise.py
```

**Why**: probewise.py has extensive resume integration throughout

#### Option B: Manual Integration (If Structure Changed)

If fresh garak significantly changed probewise.py:

1. **Add imports** at top:
```python
import garak.resumeservice as resumeservice
```

2. **In run() method**, wrap probe execution:
```python
# Before each probe execution, check if should skip
if resumeservice.enabled():
    state = resumeservice.get_state()
    if probe_name in state.get('completed_probes', set()):
        logging.info(f"Skipping completed probe: {probe_name}")
        continue
```

3. **After probe completes**:
```python
# Mark probe as complete
if resumeservice.enabled():
    resumeservice.mark_probe_complete(probe_name)
```

4. **For attempt-level granularity**, add similar checks per attempt

**Validation Strategy**:
```powershell
# Test probe execution still works
python -m garak -m test -p test.Blank --generations 1
# Should complete without errors
```

---

## 🧪 Testing Strategy

### Level 1: Syntax & Import Tests
```powershell
# Test each modified file compiles
python -m py_compile garak/resumeservice.py
python -m py_compile garak/cli.py
python -m py_compile garak/command.py
python -m py_compile garak/_config.py
python -m py_compile garak/analyze/report_digest.py
python -m py_compile garak/harnesses/probewise.py

# Test imports
python -c "import garak.resumeservice"
python -c "from garak import cli"
python -c "from garak import command"
python -c "from garak import _config"
```

### Level 2: Basic Functionality
```powershell
# Test garak starts
python -m garak --version

# Test help shows resume options
python -m garak --help | Select-String "resume"

# Test list runs (even if empty)
python -m garak --list_runs
```

### Level 3: Resume Feature
```powershell
# Start a resumable scan
python -m garak -m test -p test.Blank --resumable --report_prefix test_resume

# Wait 5-10 seconds, then Ctrl+C

# List runs
python -m garak --list_runs
# Should show test_resume

# Resume it
python -m garak --resume test_resume
# Should continue from where it stopped
```

### Level 4: Report Continuity
```powershell
# Check report has single run_id
Get-Content test_resume.report.jsonl | Select-String "entry_type.*init|entry_type.*completion" | ConvertFrom-Json | Select run

# Check no duplicate digests
(Get-Content test_resume.report.jsonl | Select-String "entry_type.*digest").Count
# Should be 1
```

---

## 🚨 Compatibility Verification

### Check Garak Version Compatibility

Different garak versions may have changes. Check these key areas:

#### 1. CLI Argument Parsing
```python
# Does fresh garak still use argparse in cli.py?
grep -n "argparse" garak/cli.py

# Does it still have a main() function?
grep -n "def main" garak/cli.py
```

#### 2. Configuration Structure
```python
# Does _config still use same structure?
python -c "from garak import _config; print(dir(_config.run))"

# Check if run_params still exists
grep -n "run_params" garak/_config.py
```

#### 3. Report Format
```python
# Does report_digest.py still exist?
test -f garak/analyze/report_digest.py && echo "✅ Exists"

# Does it have append_report_object?
grep -n "def append_report_object" garak/analyze/report_digest.py
```

#### 4. Harness Structure
```python
# Does probewise.py still exist?
test -f garak/harnesses/probewise.py && echo "✅ Exists"

# Does it have a run() method?
grep -n "def run" garak/harnesses/probewise.py
```

### Breaking Change Indicators

**If you see these, extra caution needed:**

- ❌ `cli.py` no longer uses argparse → Need new argument handling
- ❌ `_config` restructured → Need to adjust config integration
- ❌ `probewise.py` removed → Find new execution harness
- ❌ Report format changed → Adjust metadata preservation
- ❌ Major version bump (v0.x → v1.x) → Review all integrations

---

## 📦 Creating a Reusable Patch

For easier future applications, create a patch:

```powershell
# After implementing in fresh garak:
cd fresh-garak-with-resume
git init
git add .
git commit -m "Fresh garak baseline"

# Apply resume feature
# ... follow steps above ...

git add .
git commit -m "Add resume feature"

# Create patch
git format-patch HEAD~1
# Creates: 0001-Add-resume-feature.patch

# To apply to another fresh garak:
cd another-fresh-garak
git apply 0001-Add-resume-feature.patch
```

---

## 🔧 Automated Implementation Script

Create `apply_resume_feature.py`:

```python
"""
Automated Resume Feature Applicator
Applies resume feature to fresh garak installation
"""

import os
import shutil
from pathlib import Path

SOURCE_DIR = Path("backup_custom/garak")
TARGET_DIR = Path("garak")

def apply_resume_feature():
    print("🚀 Applying Resume Feature to Fresh Garak")
    print("=" * 80)
    
    # Step 1: Copy resumeservice.py
    print("\n📦 Step 1: Adding resumeservice.py...")
    shutil.copy2(SOURCE_DIR / "resumeservice.py", TARGET_DIR / "resumeservice.py")
    print("  ✅ Copied")
    
    # Step 2-6: Apply changes
    # (Implementation of surgical edits)
    
    print("\n✅ Resume feature applied!")
    print("Run tests: python -m garak --list_runs")

if __name__ == "__main__":
    apply_resume_feature()
```

---

## 📋 Final Checklist

Before considering implementation complete:

- [ ] All 6 files modified/added
- [ ] Syntax check passes on all files
- [ ] `python -m garak --version` works
- [ ] `python -m garak --help` shows resume options
- [ ] `python -m garak --list_runs` executes (even if empty)
- [ ] Can start resumable scan
- [ ] Can interrupt and resume scan
- [ ] Report shows single run_id after resume
- [ ] No duplicate digest entries
- [ ] All original garak features still work

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: ImportError for resumeservice
**Fix**: Check resumeservice.py in garak/ directory

**Issue**: AttributeError: 'GarakSubConfig' has no attribute 'resumable'
**Fix**: Check _config.py has resume parameters and defaults set

**Issue**: resume arguments not in --help
**Fix**: Check cli.py has parser.add_argument calls for resume options

**Issue**: Can't list runs
**Fix**: Check resumeservice.py copied and cli.py has list_runs handler

**Issue**: Resume doesn't preserve run_id
**Fix**: Check command.py has start_time preservation in completion entry

---

## 🎯 Success Metrics

Implementation is successful when:

1. ✅ Fresh garak starts normally: `python -m garak --version`
2. ✅ Resume options visible: `python -m garak --help | grep resume`
3. ✅ Can create resumable scan: `--resumable` flag works
4. ✅ Can list runs: `--list_runs` shows saved states
5. ✅ Can resume: `--resume <id>` continues from checkpoint
6. ✅ Reports maintain continuity: Single run_id across resume cycles
7. ✅ No duplicates: Only one digest entry per report
8. ✅ No regressions: All standard garak features work

---

**This guide ensures safe, repeatable application of resume feature to any garak version!**
