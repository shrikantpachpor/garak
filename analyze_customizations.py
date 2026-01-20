"""
Analyze customizations in garak-resume-2 vs fresh garak
Identifies all modified and new files for migration planning
"""

import os
import difflib
from pathlib import Path
import json

# Define custom files based on documentation
CUSTOM_FILES = [
    "garak/resumeservice.py",  # Entirely new file
    "garak/cli.py",
    "garak/command.py", 
    "garak/_config.py",
    "garak/analyze/report_digest.py",
    "garak/harnesses/probewise.py",  # Might be modified
]

# Project root directories
CUSTOM_DIR = Path(r"e:\SHRIKANT\projects\garak-resume-2")
FRESH_DIR = Path(r"e:\SHRIKANT\projects\garak-fresh")

def file_exists_in(dir_path, rel_path):
    """Check if file exists in directory"""
    full_path = dir_path / rel_path
    return full_path.exists()

def read_file_safe(file_path):
    """Read file safely, return None if error"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"  ⚠ Error reading {file_path}: {e}")
        return None

def compare_files(custom_path, fresh_path):
    """Compare two files and return diff stats"""
    custom_lines = read_file_safe(custom_path)
    fresh_lines = read_file_safe(fresh_path)
    
    if custom_lines is None or fresh_lines is None:
        return None
    
    diff = list(difflib.unified_diff(fresh_lines, custom_lines, lineterm=''))
    added = len([l for l in diff if l.startswith('+')])
    removed = len([l for l in diff if l.startswith('-')])
    
    return {
        'added': added,
        'removed': removed,
        'total_changes': added + removed,
        'custom_lines': len(custom_lines),
        'fresh_lines': len(fresh_lines),
        'diff': diff[:50]  # First 50 lines of diff
    }

def analyze():
    """Main analysis function"""
    print("="*80)
    print("GARAK CUSTOMIZATION ANALYSIS")
    print("="*80)
    print()
    
    results = {
        'new_files': [],
        'modified_files': [],
        'analysis': {}
    }
    
    # Check each known custom file
    for rel_path in CUSTOM_FILES:
        print(f"\n📄 {rel_path}")
        print("-" * 80)
        
        custom_exists = file_exists_in(CUSTOM_DIR, rel_path)
        fresh_exists = file_exists_in(FRESH_DIR, rel_path)
        
        if not custom_exists:
            print("  ❌ File doesn't exist in custom repo")
            continue
            
        if not fresh_exists:
            print("  ✅ NEW FILE (doesn't exist in fresh garak)")
            results['new_files'].append(rel_path)
            custom_path = CUSTOM_DIR / rel_path
            lines = read_file_safe(custom_path)
            if lines:
                print(f"  📊 Lines: {len(lines)}")
                results['analysis'][rel_path] = {
                    'status': 'new',
                    'lines': len(lines)
                }
        else:
            print("  🔄 MODIFIED FILE (exists in both)")
            custom_path = CUSTOM_DIR / rel_path
            fresh_path = FRESH_DIR / rel_path
            
            diff_result = compare_files(custom_path, fresh_path)
            if diff_result:
                if diff_result['total_changes'] == 0:
                    print("  ✨ No changes detected (might be false positive)")
                else:
                    print(f"  📊 Changes: +{diff_result['added']} -{diff_result['removed']}")
                    print(f"  📏 Lines: custom={diff_result['custom_lines']}, fresh={diff_result['fresh_lines']}")
                    results['modified_files'].append(rel_path)
                    results['analysis'][rel_path] = {
                        'status': 'modified',
                        **diff_result
                    }
    
    # Check for resume-related test files
    print("\n\n" + "="*80)
    print("TEST FILES")
    print("="*80)
    
    test_files = list(CUSTOM_DIR.glob("test_resume*.py"))
    for test_file in test_files:
        print(f"  ✅ {test_file.name}")
    
    # Check documentation files
    print("\n\n" + "="*80)
    print("DOCUMENTATION FILES")
    print("="*80)
    
    doc_patterns = ["RESUME_*.md", "*RESUME*.md"]
    doc_files = []
    for pattern in doc_patterns:
        doc_files.extend(CUSTOM_DIR.glob(pattern))
    
    for doc_file in sorted(set(doc_files)):
        print(f"  📖 {doc_file.name}")
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n📦 New Files: {len(results['new_files'])}")
    for f in results['new_files']:
        print(f"   • {f}")
    
    print(f"\n🔧 Modified Files: {len(results['modified_files'])}")
    for f in results['modified_files']:
        stats = results['analysis'][f]
        print(f"   • {f} (+{stats.get('added', 0)} -{stats.get('removed', 0)} changes)")
    
    print(f"\n📝 Test Files: {len(test_files)}")
    print(f"📖 Documentation Files: {len(doc_files)}")
    
    # Save detailed results
    output_file = CUSTOM_DIR / "CUSTOMIZATION_ANALYSIS.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Remove diff from json (too large)
        for key in results['analysis']:
            if 'diff' in results['analysis'][key]:
                results['analysis'][key]['diff'] = f"<{len(results['analysis'][key]['diff'])} lines>"
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file.name}")
    
    # Next steps
    print("\n\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Review the modified files in detail:
   - Compare each file with fresh garak
   - Identify specific changes needed

2. Create migration branch:
   git checkout -b migrate-to-latest-garak

3. Copy fresh garak core files (excluding customizations)

4. Re-apply customizations:
   - Copy resumeservice.py (new file)
   - Merge changes to cli.py
   - Merge changes to command.py
   - Merge changes to _config.py
   - Merge changes to report_digest.py

5. Test the resume feature thoroughly

6. Update documentation with new garak version
""")
    
    return results

if __name__ == "__main__":
    analyze()
