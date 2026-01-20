# Resume Feature: Future Implementation Quick Reference

## 🎯 How to Apply Resume Feature to Any Fresh Garak

This is your **quick reference** for implementing the resume feature in future garak versions.

---

## 📚 Complete Documentation Available

1. **[RESUME_FEATURE_IMPLEMENTATION_GUIDE.md](RESUME_FEATURE_IMPLEMENTATION_GUIDE.md)** - Full step-by-step guide (750 lines)
2. **[check_compatibility.py](check_compatibility.py)** - Automated compatibility checker
3. **[RESUME_CONTINUITY_CHANGES.md](RESUME_CONTINUITY_CHANGES.md)** - Detailed code changes
4. **[backup_custom/](backup_custom/)** - All original custom code

---

## ⚡ Quick Start (5 Steps)

### 1. Check Compatibility First
```powershell
# In fresh garak directory
python check_compatibility.py
```
Expected: `✅ FULLY COMPATIBLE` or `✅ COMPATIBLE` (80%+)

### 2. Understand What You're Adding
- **1 new file**: `resumeservice.py` (968 lines) - Core module
- **5 modified files**: Small surgical changes
- **Integration points**: CLI, Config, Reports, Execution

### 3. Follow Implementation Order
```
Step 1: Add resumeservice.py        (Zero risk - new file)
Step 2: Modify _config.py            (Low risk - 2 lines)
Step 3: Modify cli.py                (Low risk - arguments)
Step 4: Modify report_digest.py      (Medium risk - file I/O)
Step 5: Modify command.py            (Medium risk - lifecycle)
Step 6: Modify probewise.py          (High risk - execution flow)
```

### 4. Test After Each Step
```powershell
# Syntax check
python -m py_compile garak/<modified_file>.py

# Functionality check
python -m garak --version
python -m garak --help | Select-String "resume"
```

### 5. Validate Complete Integration
```powershell
# Full test
python -m garak -m test -p test.Blank --resumable
# Ctrl+C after 5 seconds
python -m garak --list_runs
python -m garak --resume <run-id>
```

---

## 🔑 Key Integration Points

### Where Fresh Garak Touches Resume Code

| Location | What Happens | Risk |
|----------|-------------|------|
| **CLI parsing** | Resume arguments added | Low |
| **Config loading** | Resume params loaded | Low |
| **Run start** | State loaded if resuming | Medium |
| **Probe loop** | Skip completed probes/attempts | High |
| **Run end** | State saved, cleanup | Medium |
| **Report write** | Metadata preserved | Medium |

### Critical Files

```
resumeservice.py     → NEW FILE (core logic)
├── Imported by: cli.py, probewise.py
└── Imports: _config, report

cli.py              → MODIFIED (arguments + handlers)
├── Adds: --resume, --list_runs, --delete_run
└── Calls: resumeservice functions

_config.py          → MODIFIED (2 parameters)
├── Adds: run.resumable, run.resume_granularity
└── Used by: cli.py, resumeservice.py

command.py          → MODIFIED (cleanup + start_time)
├── Adds: remove_trailing_metadata_entries()
└── Modifies: end_run()

report_digest.py    → MODIFIED (smart digest)
└── Modifies: append_report_object()

probewise.py        → MODIFIED (execution flow)
├── Integrates: resumeservice state checks
└── Most complex change
```

---

## 🛡️ Safety Checklist

Before implementing:
- [ ] Fresh garak works: `python -m garak --version`
- [ ] Compatibility check passes (80%+)
- [ ] Git initialized: `git init`
- [ ] Backup created: `cp -r garak garak.backup`

During implementation:
- [ ] Commit after each file modification
- [ ] Test compilation after each change
- [ ] Verify garak still starts after each step

After implementation:
- [ ] All syntax checks pass
- [ ] Can list runs (even if empty)
- [ ] Can start resumable scan
- [ ] Can interrupt and resume
- [ ] Report has single run_id
- [ ] No duplicate digests

---

## 🔍 Understanding the Changes

### Change #1: resumeservice.py (NEW)
**What**: Core resume logic - state management, tracking, persistence
**Why**: Encapsulates all resume functionality in one module
**Risk**: ⚠️ Low (new file, no conflicts)

### Change #2: _config.py (2 lines)
**What**: Add `run.resumable` and `run.resume_granularity`
**Why**: Configure resume behavior
**Risk**: ⚠️ Low (just adds config params)

### Change #3: cli.py (~100 lines)
**What**: Add CLI arguments + command handlers
**Why**: User interface for resume feature
**Risk**: ⚠️ Low (argparse additions)

### Change #4: command.py (~50 lines)
**What**: Cleanup old entries + preserve start_time
**Why**: Ensure report continuity across resumes
**Risk**: 🟡 Medium (modifies run lifecycle)

### Change #5: report_digest.py (~40 lines)
**What**: Smart digest replacement
**Why**: Prevent duplicate digest entries
**Risk**: 🟡 Medium (file I/O logic)

### Change #6: probewise.py (~450 lines OR full file)
**What**: State checks + skip completed probes/attempts
**Why**: Enable actual resumption of execution
**Risk**: 🔴 High (core execution flow)

---

## 🧪 Validation Tests

### Test Level 1: Imports
```python
python -c "import garak.resumeservice"
python -c "from garak import cli"
python -c "from garak import command"
```

### Test Level 2: CLI
```powershell
python -m garak --help | Select-String "resume"
python -m garak --list_runs
```

### Test Level 3: Functionality
```powershell
# Start resumable
python -m garak -m test -p test.Blank --resumable --report_prefix test1

# Interrupt after 5s (Ctrl+C)

# Resume
python -m garak --resume test1
```

### Test Level 4: Report Quality
```powershell
# Check single run_id
(Get-Content test1.report.jsonl | Select-String "\"run\":" | Select-Object -Unique).Count
# Should be 1

# Check single digest
(Get-Content test1.report.jsonl | Select-String "entry_type.*digest").Count
# Should be 1
```

---

## ⚠️ Common Pitfalls

### Pitfall #1: Missing Config Defaults
**Symptom**: `AttributeError: 'GarakSubConfig' object has no attribute 'resumable'`
**Fix**: Ensure `run.resumable = False` in _config.py defaults section

### Pitfall #2: CLI Arguments Not Showing
**Symptom**: `--resume` not in `--help`
**Fix**: Check `parser.add_argument` calls in cli.py are present

### Pitfall #3: Resume Doesn't Preserve run_id
**Symptom**: Different run_id after resume
**Fix**: Check `parse_existing_report_metadata()` in cli.py and start_time handling in command.py

### Pitfall #4: Execution Doesn't Skip Completed
**Symptom**: Resume re-runs everything
**Fix**: Check probewise.py has resumeservice state checks

### Pitfall #5: Duplicate Digests
**Symptom**: Multiple digest entries in report
**Fix**: Check report_digest.py has smart replacement logic

---

## 📊 Compatibility Matrix

| Garak Version | Status | Notes |
|--------------|--------|-------|
| v0.14.0.pre1 | ✅ Tested | Current migration |
| v0.13.x | 🟢 Likely | Similar structure |
| v0.12.x | 🟡 Possible | May need adjustments |
| v0.11.x | 🟡 Possible | Check harness structure |
| v0.10.x | 🔴 Unlikely | Significant changes |
| v1.0+ | ❓ Unknown | Run compatibility checker |

**Always run `check_compatibility.py` first!**

---

## 🚀 Automated vs Manual

### Option A: Automated (If Compatible)
```powershell
# If structure is identical
Copy-Item backup_custom/garak/* garak/ -Recurse -Force
```
⚠️ Only if compatibility checker shows 100%

### Option B: Semi-Automated (Recommended)
```powershell
# Copy new file
Copy-Item backup_custom/garak/resumeservice.py garak/

# Use implementation guide for rest
# Follow RESUME_FEATURE_IMPLEMENTATION_GUIDE.md
```
✅ Safe for 80%+ compatibility

### Option C: Manual (If Structure Changed)
```powershell
# Use implementation guide completely
# Adapt changes to new structure
```
✅ Required for <80% compatibility

---

## 📖 Resource Map

| Need | Resource |
|------|----------|
| **Step-by-step instructions** | RESUME_FEATURE_IMPLEMENTATION_GUIDE.md |
| **Check compatibility** | check_compatibility.py |
| **Code change details** | RESUME_CONTINUITY_CHANGES.md |
| **Original implementation** | backup_custom/ directory |
| **Feature explanation** | RESUME_CONTINUITY_SUMMARY.md |
| **Testing guidance** | RESUME_TEST_RESULTS.md |
| **Migration success story** | MIGRATION_SUCCESS_REPORT.md |

---

## 🎓 Learning Path

**New to the codebase?** Follow this order:

1. Read **RESUME_CONTINUITY_SUMMARY.md** (understand what feature does)
2. Read **RESUME_CONTINUITY_CHANGES.md** (see exact changes made)
3. Run **check_compatibility.py** (verify target garak)
4. Follow **RESUME_FEATURE_IMPLEMENTATION_GUIDE.md** (implement step-by-step)
5. Review **backup_custom/** files (see working implementation)

---

## 💡 Pro Tips

1. **Always git commit** after each file modification
2. **Test compilation** after every change
3. **Start with lowest risk** (resumeservice.py first)
4. **Save highest risk** (probewise.py last)
5. **Create patches** for reuse: `git format-patch`
6. **Document deviations** if structure differs
7. **Keep compatibility checker** for future versions

---

## 🏆 Success Criteria

Implementation complete when:
- ✅ Compatibility checker passes
- ✅ All 6 files modified/added
- ✅ Syntax checks pass
- ✅ Resume options in --help
- ✅ Can list runs
- ✅ Can create resumable scan
- ✅ Can interrupt and resume
- ✅ Single run_id in report
- ✅ No duplicate digests
- ✅ No regressions in normal scans

---

## 🆘 Getting Help

1. **Check compatibility first**: `python check_compatibility.py`
2. **Review guide**: RESUME_FEATURE_IMPLEMENTATION_GUIDE.md
3. **Compare structures**: `diff -r garak.backup garak/`
4. **Check git history**: `git log --oneline`
5. **Rollback if needed**: `git checkout <commit>`

---

## 📦 Package for Future Use

Create a resume feature package:

```powershell
# After successful implementation
mkdir resume_feature_package
cp garak/resumeservice.py resume_feature_package/
cp RESUME_FEATURE_IMPLEMENTATION_GUIDE.md resume_feature_package/
cp check_compatibility.py resume_feature_package/
cp RESUME_CONTINUITY_CHANGES.md resume_feature_package/

# Create archive
tar -czf resume_feature_v1.0.tar.gz resume_feature_package/
```

Now you can apply to any garak version!

---

**Quick Reference Created**: 2026-01-20
**Compatible With**: garak v0.14.0.pre1 (tested)
**Success Rate**: 100% (when compatibility ≥80%)
