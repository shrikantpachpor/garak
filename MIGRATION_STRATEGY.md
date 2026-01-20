# Garak Migration Strategy: From Mixed Versions to Latest

## Current Status ✅

**Git initialized** and baseline commit created (516c1fc)
**Fresh garak cloned** at e:\SHRIKANT\projects\garak-fresh (commit: 666ca84)

## Customization Summary

### 🆕 New Files (1)
- **garak/resumeservice.py** (968 lines) - Core resume service logic

### 🔧 Modified Files (5)
1. **garak/cli.py** (+340 lines)
   - Resume command handling
   - Metadata parsing for run continuity
   - Run management (list, delete, resume)

2. **garak/harnesses/probewise.py** (+523 lines)
   - Probe-wise execution with resume support
   - Attempt tracking integration

3. **garak/command.py** (+133 lines)
   - Cleanup of duplicate metadata entries
   - Original start_time preservation

4. **garak/analyze/report_digest.py** (+66 lines)
   - Smart digest replacement (no duplicates)

5. **garak/_config.py** (+4 lines)
   - Resume configuration parameters

### 📝 Documentation (15 files)
- Complete implementation guides
- Test results
- Change summaries

### 🧪 Test Files (5)
- test_resume*.py - Various resume feature tests

## Migration Options

### Option A: Conservative Merge (RECOMMENDED) ⭐
**Time**: 3-4 hours | **Risk**: Low | **Success Rate**: High

1. Create migration branch
2. Extract your customizations as patches
3. Update garak/ directory from fresh repo (excluding custom files)
4. Re-apply patches with conflict resolution
5. Test thoroughly

**Advantages:**
- Preserves all customizations
- Gets latest garak features/fixes
- Clean git history
- Repeatable process

### Option B: File-by-File Cherry Pick
**Time**: 5-6 hours | **Risk**: Medium | **Success Rate**: Medium

1. Replace each garak core file with fresh version
2. Manually re-implement changes using RESUME_CONTINUITY_CHANGES.md
3. Test after each file

**Advantages:**
- Full control over each change
- Learn latest garak structure

**Disadvantages:**
- Time-consuming
- Error-prone

### Option C: Start Fresh + Copy Feature
**Time**: 8+ hours | **Risk**: High | **Success Rate**: Medium

1. Clone fresh garak
2. Re-implement resume feature from scratch
3. Use current code as reference

**Advantages:**
- Cleanest result

**Disadvantages:**
- Most time-consuming
- May introduce new bugs

## Recommended Approach: Conservative Merge (Option A)

### Phase 1: Preparation (15 minutes)
```bash
cd e:\SHRIKANT\projects\garak-resume-2

# Create migration branch
git checkout -b migrate-to-latest

# Tag current state for reference
git tag pre-migration
```

### Phase 2: Create Patches (30 minutes)
```bash
# Export customizations as patches
git diff --no-index e:\SHRIKANT\projects\garak-fresh\garak\cli.py garak\garak\cli.py > patches\cli.patch
git diff --no-index e:\SHRIKANT\projects\garak-fresh\garak\command.py garak\garak\command.py > patches\command.patch
# ... etc for each modified file
```

### Phase 3: Update Core Files (30 minutes)
```bash
# Backup customizations
mkdir -p backup_custom
cp garak/resumeservice.py backup_custom/
cp garak/cli.py backup_custom/
cp garak/command.py backup_custom/
cp garak/_config.py backup_custom/
cp garak/analyze/report_digest.py backup_custom/
cp garak/harnesses/probewise.py backup_custom/

# Copy fresh garak (excluding customizations)
xcopy /E /Y e:\SHRIKANT\projects\garak-fresh\garak garak_new\
# Then selectively replace
```

### Phase 4: Re-apply Customizations (1-2 hours)
For each file:
1. Compare fresh vs custom
2. Identify resume-specific changes
3. Merge into fresh version
4. Test compilation

### Phase 5: Testing (1 hour)
```bash
# Run existing tests
python -m pytest tests/test_resume_integration.py

# Manual smoke test
python -m garak --list-runs
python -m garak -m test -p av_spam_scanning --resumable
# Interrupt and resume
```

### Phase 6: Verification (30 minutes)
- Compare report outputs with original
- Verify run_id continuity
- Check for no duplicate digests
- Validate all resume features work

## Quick Reference: Files to Update

| Priority | File | Action | Notes |
|----------|------|--------|-------|
| 🔴 HIGH | resumeservice.py | COPY (new file) | No conflicts |
| 🔴 HIGH | cli.py | MERGE | Many changes |
| 🔴 HIGH | command.py | MERGE | Significant changes |
| 🟡 MEDIUM | harnesses/probewise.py | MERGE | Large diff |
| 🟡 MEDIUM | analyze/report_digest.py | MERGE | Smart digest logic |
| 🟢 LOW | _config.py | MERGE | Minimal changes |

## Risk Mitigation

1. **Git tags** at every major step
2. **Incremental commits** after each file migration
3. **Test after each change** (not just at the end)
4. **Keep backup_custom/** directory until fully tested
5. **Document any conflicts** encountered

## Rollback Plan

If migration fails:
```bash
git checkout master
# Or restore from specific tag:
git checkout pre-migration
```

## Success Criteria

✅ All resume features work as before
✅ Latest garak features available
✅ No version conflicts
✅ Tests pass
✅ Reports match expected format
✅ Documentation updated with new version

## Timeline Estimate

- **Optimistic**: 2-3 hours
- **Realistic**: 3-4 hours
- **Pessimistic**: 5-6 hours (with complications)

## Next Immediate Steps

1. Create migration branch
2. Run the automated patch extraction script (to be created)
3. Begin Phase 2

Ready to proceed? Start with:
```bash
cd e:\SHRIKANT\projects\garak-resume-2
git checkout -b migrate-to-latest
```
