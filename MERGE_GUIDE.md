# Manual Merge Guide

## Overview
This guide helps you merge custom resume feature changes into the latest garak.

## Files to Merge


### 1. garak/cli.py

**Custom file**: `backup_custom/garak/cli.py`
**Fresh file**: `garak-fresh/garak/cli.py`
**Target**: `garak/cli.py`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile garak/cli.py`
5. Commit: `git add garak/cli.py && git commit -m "Merge: garak/cli.py"`

**Key changes to look for:**

- Resume command handling (--resume, --list-runs, --delete-run)
- parse_existing_report_metadata() function
- Original run_id and start_time preservation

### 2. garak/command.py

**Custom file**: `backup_custom/garak/command.py`
**Fresh file**: `garak-fresh/garak/command.py`
**Target**: `garak/command.py`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile garak/command.py`
5. Commit: `git add garak/command.py && git commit -m "Merge: garak/command.py"`

**Key changes to look for:**

- remove_trailing_metadata_entries() function
- Cleanup of old completion/digest entries
- start_time in completion entry

### 3. garak/_config.py

**Custom file**: `backup_custom/garak/_config.py`
**Fresh file**: `garak-fresh/garak/_config.py`
**Target**: `garak/_config.py`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile garak/_config.py`
5. Commit: `git add garak/_config.py && git commit -m "Merge: garak/_config.py"`

**Key changes to look for:**

- resumable and resume_granularity parameters
- transient.resume_run_id handling

### 4. garak/analyze/report_digest.py

**Custom file**: `backup_custom/garak/analyze/report_digest.py`
**Fresh file**: `garak-fresh/garak/analyze/report_digest.py`
**Target**: `garak/analyze/report_digest.py`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile garak/analyze/report_digest.py`
5. Commit: `git add garak/analyze/report_digest.py && git commit -m "Merge: garak/analyze/report_digest.py"`

**Key changes to look for:**

- Smart digest replacement in append_report_object()
- Filtering of old digest/completion entries

### 5. garak/harnesses/probewise.py

**Custom file**: `backup_custom/garak/harnesses/probewise.py`
**Fresh file**: `garak-fresh/garak/harnesses/probewise.py`
**Target**: `garak/harnesses/probewise.py`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile garak/harnesses/probewise.py`
5. Commit: `git add garak/harnesses/probewise.py && git commit -m "Merge: garak/harnesses/probewise.py"`

**Key changes to look for:**

- Integration with resumeservice
- Attempt tracking and completion marking


## New Files to Copy


### garak/resumeservice.py

Simply copy from backup:
```bash
cp backup_custom/garak/resumeservice.py garak/resumeservice.py
git add garak/resumeservice.py
git commit -m "Add: garak/resumeservice.py"
```


## Testing Checklist

After each file merge:
- [ ] File compiles: `python -m py_compile <file>`
- [ ] No syntax errors: `python -m garak --help`

After all merges:
- [ ] Resume feature works: `python -m garak --list-runs`
- [ ] Can start resumable scan: `python -m garak -m test -p test --resumable`
- [ ] Can resume interrupted scan: `python -m garak --resume <run-id>`
- [ ] Reports maintain run_id continuity
- [ ] No duplicate digest entries

## Rollback

If anything goes wrong:
```bash
git checkout pre-migration
```

## Tips

1. Use VS Code's diff view: `code --diff backup_custom/<file> <file>`
2. Commit after each successful file merge
3. Test frequently, not just at the end
4. Keep backup_custom/ until fully confident
