# Resume Feature - Report Continuity Implementation

## Overview
This document outlines the code changes needed to make resumed scans produce reports that are indistinguishable from continuous, uninterrupted scans.

## Current State (Already Implemented ✅)
1. ✅ Append mode for JSONL files (cli.py lines 797, 803)
2. ✅ Skip setup/init entries on resume (cli.py line 808)
3. ✅ UUID extraction from full run_id (resumeservice.py line 419-434)
4. ✅ State persistence with run metadata

## Required Changes

### 1. Preserve Original Run ID Across Resume
**Problem**: Currently, a new UUID is generated on resume
**Solution**: Load and reuse the original run_id from the existing report

### 2. Track Original Start Time
**Problem**: New timestamps created on resume
**Solution**: Parse original start_time from report and preserve it

### 3. Update Completion Entry on Resume
**Problem**: Old completion entry remains, or new one is appended
**Solution**: Remove old completion/digest, append new ones on completion

### 4. Regenerate Digest Without Duplication
**Problem**: Multiple digest entries if run interrupted multiple times
**Solution**: Always replace the last digest entry when building new one

## Implementation Details

See modified files below:
- garak/cli.py: Load original run_id and start_time from existing report
- garak/command.py: Update completion entry logic
- garak/analyze/report_digest.py: Handle digest replacement
- garak/resumeservice.py: Store original metadata in state

## Testing Checklist
- [ ] Resume preserves original run_id across all entries
- [ ] Resume preserves original start_time
- [ ] Completion entry shows updated end_time
- [ ] Only one digest entry in final report
- [ ] HTML report reflects complete run
- [ ] No duplicate attempt entries
