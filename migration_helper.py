"""
Automated Migration Helper for Garak Resume Feature
Helps migrate custom resume feature to latest garak version
"""

import os
import shutil
from pathlib import Path
import subprocess
import json

# Paths
CUSTOM_DIR = Path(r"e:\SHRIKANT\projects\garak-resume-2")
FRESH_DIR = Path(r"e:\SHRIKANT\projects\garak-fresh")
BACKUP_DIR = CUSTOM_DIR / "backup_custom"
PATCHES_DIR = CUSTOM_DIR / "patches"

# Files to handle
CUSTOM_FILES = {
    'new': [
        'garak/resumeservice.py',
    ],
    'modified': [
        'garak/cli.py',
        'garak/command.py',
        'garak/_config.py',
        'garak/analyze/report_digest.py',
        'garak/harnesses/probewise.py',
    ]
}

def create_backup():
    """Backup all custom files"""
    print("\n" + "="*80)
    print("STEP 1: BACKING UP CUSTOM FILES")
    print("="*80)
    
    BACKUP_DIR.mkdir(exist_ok=True)
    
    all_files = CUSTOM_FILES['new'] + CUSTOM_FILES['modified']
    for file_path in all_files:
        src = CUSTOM_DIR / file_path
        dst = BACKUP_DIR / file_path
        
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✅ Backed up: {file_path}")
        else:
            print(f"  ⚠ Not found: {file_path}")
    
    print(f"\n✨ Backup complete at: {BACKUP_DIR}")

def analyze_changes():
    """Analyze what changed in each file"""
    print("\n" + "="*80)
    print("STEP 2: ANALYZING CHANGES")
    print("="*80)
    
    analysis = {}
    
    for file_path in CUSTOM_FILES['modified']:
        print(f"\n📄 {file_path}")
        custom_file = CUSTOM_DIR / file_path
        fresh_file = FRESH_DIR / file_path
        
        if not custom_file.exists():
            print("  ❌ Custom file not found")
            continue
        
        if not fresh_file.exists():
            print("  ⚠ Fresh file not found (might be new in your version)")
            continue
        
        # Count lines
        with open(custom_file, 'r', encoding='utf-8') as f:
            custom_lines = f.readlines()
        with open(fresh_file, 'r', encoding='utf-8') as f:
            fresh_lines = f.readlines()
        
        print(f"  📊 Custom: {len(custom_lines)} lines, Fresh: {len(fresh_lines)} lines")
        print(f"  📈 Difference: {len(custom_lines) - len(fresh_lines):+d} lines")
        
        analysis[file_path] = {
            'custom_lines': len(custom_lines),
            'fresh_lines': len(fresh_lines),
            'diff': len(custom_lines) - len(fresh_lines)
        }
    
    # Save analysis
    analysis_file = CUSTOM_DIR / "migration_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n✨ Analysis saved to: {analysis_file.name}")
    return analysis

def create_merge_guide():
    """Create a guide for manual merging"""
    print("\n" + "="*80)
    print("STEP 3: CREATING MERGE GUIDE")
    print("="*80)
    
    guide_content = """# Manual Merge Guide

## Overview
This guide helps you merge custom resume feature changes into the latest garak.

## Files to Merge

"""
    
    for idx, file_path in enumerate(CUSTOM_FILES['modified'], 1):
        guide_content += f"""
### {idx}. {file_path}

**Custom file**: `backup_custom/{file_path}`
**Fresh file**: `{FRESH_DIR.relative_to(CUSTOM_DIR.parent)}/{file_path}`
**Target**: `{file_path}`

**Merge steps:**
1. Open both files side by side in VS Code
2. Look for resume-related changes in custom file:
   - Search for "resume" (case insensitive)
   - Search for "resumeservice"
   - Look for imports of resumeservice
3. Copy resume-specific code blocks to fresh file
4. Test compilation: `python -m py_compile {file_path}`
5. Commit: `git add {file_path} && git commit -m "Merge: {file_path}"`

**Key changes to look for:**
"""
        
        if 'cli.py' in file_path:
            guide_content += """
- Resume command handling (--resume, --list-runs, --delete-run)
- parse_existing_report_metadata() function
- Original run_id and start_time preservation
"""
        elif 'command.py' in file_path:
            guide_content += """
- remove_trailing_metadata_entries() function
- Cleanup of old completion/digest entries
- start_time in completion entry
"""
        elif '_config.py' in file_path:
            guide_content += """
- resumable and resume_granularity parameters
- transient.resume_run_id handling
"""
        elif 'report_digest.py' in file_path:
            guide_content += """
- Smart digest replacement in append_report_object()
- Filtering of old digest/completion entries
"""
        elif 'probewise.py' in file_path:
            guide_content += """
- Integration with resumeservice
- Attempt tracking and completion marking
"""
    
    guide_content += """

## New Files to Copy

"""
    for file_path in CUSTOM_FILES['new']:
        guide_content += f"""
### {file_path}

Simply copy from backup:
```bash
cp backup_custom/{file_path} {file_path}
git add {file_path}
git commit -m "Add: {file_path}"
```
"""
    
    guide_content += """

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
"""
    
    guide_file = CUSTOM_DIR / "MERGE_GUIDE.md"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✨ Merge guide created: {guide_file.name}")
    print("\n📖 Open MERGE_GUIDE.md for step-by-step instructions")

def show_migration_plan():
    """Show the migration plan"""
    print("\n" + "="*80)
    print("MIGRATION PLAN")
    print("="*80)
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     MIGRATION APPROACH OPTIONS                        ║
╚══════════════════════════════════════════════════════════════════════╝

Option A: Semi-Automated (Recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Copy new files (resumeservice.py) → 5 min
2. Use VS Code to manually merge each modified file → 2-3 hours
3. Test after each file → 1 hour
Total: ~3-4 hours

Option B: Fresh Update + Manual Re-implementation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Replace entire garak/ directory with fresh version
2. Re-apply customizations using RESUME_CONTINUITY_CHANGES.md
3. Use backup_custom/ as reference
Total: ~4-6 hours

Option C: Scripted Merge (Risky)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Use git merge or patch to auto-merge
2. Resolve conflicts manually
Total: ~2-3 hours (if no major conflicts)

╔══════════════════════════════════════════════════════════════════════╗
║                     RECOMMENDED: Option A                             ║
╚══════════════════════════════════════════════════════════════════════╝

Next Steps:
1. Review MERGE_GUIDE.md for detailed instructions
2. Start with resumeservice.py (easiest - new file)
3. Then merge modified files one by one
4. Test after each file
5. Commit after successful merge

Ready to start? Run:
  cd backup_custom
  explorer .   # Open backup folder in Windows Explorer

Then follow MERGE_GUIDE.md step by step.
""")

def main():
    """Main migration helper"""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       GARAK RESUME FEATURE - MIGRATION HELPER                         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    # Step 1: Backup
    create_backup()
    
    # Step 2: Analyze
    analysis = analyze_changes()
    
    # Step 3: Create guide
    create_merge_guide()
    
    # Step 4: Show plan
    show_migration_plan()
    
    print("\n" + "="*80)
    print("✅ PREPARATION COMPLETE")
    print("="*80)
    print("\n📖 Next: Read MERGE_GUIDE.md and start merging")
    print("💾 Backups: backup_custom/")
    print("📊 Analysis: migration_analysis.json")
    print("🎯 Current branch:", end=" ")
    
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=CUSTOM_DIR)
        print(result.stdout.strip())
    except:
        print("(unknown)")

if __name__ == "__main__":
    main()
