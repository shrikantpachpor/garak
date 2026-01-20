"""
Garak Compatibility Checker for Resume Feature
Checks if a fresh garak installation is compatible with resume feature implementation
"""

import os
import re
from pathlib import Path
import subprocess

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_file_exists(filepath):
    """Check if file exists"""
    exists = Path(filepath).exists()
    status = f"{Colors.GREEN}✅{Colors.END}" if exists else f"{Colors.RED}❌{Colors.END}"
    print(f"  {status} {filepath}")
    return exists

def check_function_exists(filepath, function_name):
    """Check if function exists in file"""
    if not Path(filepath).exists():
        print(f"  {Colors.RED}❌{Colors.END} {filepath} not found")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = f"def {function_name}"
    exists = pattern in content
    status = f"{Colors.GREEN}✅{Colors.END}" if exists else f"{Colors.YELLOW}⚠️{Colors.END}"
    print(f"  {status} {function_name}() in {filepath}")
    return exists

def check_pattern_exists(filepath, pattern, description):
    """Check if pattern exists in file"""
    if not Path(filepath).exists():
        print(f"  {Colors.RED}❌{Colors.END} {filepath} not found")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    exists = bool(re.search(pattern, content))
    status = f"{Colors.GREEN}✅{Colors.END}" if exists else f"{Colors.YELLOW}⚠️{Colors.END}"
    print(f"  {status} {description}")
    return exists

def check_garak_version():
    """Check garak version"""
    try:
        result = subprocess.run(['python', '-m', 'garak', '--version'], 
                              capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        version_match = re.search(r'v?(\d+\.\d+\.\d+[\.\w]*)', output)
        if version_match:
            version = version_match.group(1)
            print(f"  {Colors.GREEN}✅{Colors.END} Garak version: {version}")
            return version
        else:
            print(f"  {Colors.YELLOW}⚠️{Colors.END} Could not determine version")
            return "unknown"
    except Exception as e:
        print(f"  {Colors.RED}❌{Colors.END} Error checking version: {e}")
        return None

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}GARAK COMPATIBILITY CHECKER FOR RESUME FEATURE{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    scores = {'total': 0, 'passed': 0}
    
    # Check 1: Garak Version
    print(f"{Colors.BLUE}📦 Check 1: Garak Installation{Colors.END}")
    version = check_garak_version()
    scores['total'] += 1
    if version:
        scores['passed'] += 1
    
    # Check 2: Required Files
    print(f"\n{Colors.BLUE}📁 Check 2: Required Files Exist{Colors.END}")
    required_files = [
        'garak/cli.py',
        'garak/command.py',
        'garak/_config.py',
        'garak/analyze/report_digest.py',
        'garak/harnesses/probewise.py',
    ]
    
    for filepath in required_files:
        scores['total'] += 1
        if check_file_exists(filepath):
            scores['passed'] += 1
    
    # Check 3: CLI Structure
    print(f"\n{Colors.BLUE}🔧 Check 3: CLI Argument Parsing{Colors.END}")
    scores['total'] += 2
    if check_pattern_exists('garak/cli.py', r'import argparse|from argparse', 'Uses argparse'):
        scores['passed'] += 1
    if check_function_exists('garak/cli.py', 'main'):
        scores['passed'] += 1
    
    # Check 4: Configuration Structure
    print(f"\n{Colors.BLUE}⚙️ Check 4: Configuration Structure{Colors.END}")
    scores['total'] += 2
    if check_pattern_exists('garak/_config.py', r'run_params\s*=', 'Has run_params'):
        scores['passed'] += 1
    if check_pattern_exists('garak/_config.py', r'run\.seed', 'Has run.seed'):
        scores['passed'] += 1
    
    # Check 5: Report Handling
    print(f"\n{Colors.BLUE}📊 Check 5: Report Digest Handling{Colors.END}")
    scores['total'] += 1
    if check_function_exists('garak/analyze/report_digest.py', 'append_report_object'):
        scores['passed'] += 1
    
    # Check 6: Command Lifecycle
    print(f"\n{Colors.BLUE}🔄 Check 6: Command Lifecycle{Colors.END}")
    scores['total'] += 1
    if check_function_exists('garak/command.py', 'end_run'):
        scores['passed'] += 1
    
    # Check 7: Harness Structure
    print(f"\n{Colors.BLUE}🎯 Check 7: Probe Harness{Colors.END}")
    scores['total'] += 1
    if check_function_exists('garak/harnesses/probewise.py', 'run'):
        scores['passed'] += 1
    
    # Check 8: Python Version
    print(f"\n{Colors.BLUE}🐍 Check 8: Python Version{Colors.END}")
    try:
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True)
        python_version = result.stdout.strip()
        print(f"  {Colors.GREEN}✅{Colors.END} {python_version}")
        scores['total'] += 1
        scores['passed'] += 1
    except Exception as e:
        print(f"  {Colors.RED}❌{Colors.END} Error: {e}")
        scores['total'] += 1
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    percentage = (scores['passed'] / scores['total'] * 100) if scores['total'] > 0 else 0
    
    if percentage == 100:
        color = Colors.GREEN
        verdict = "✅ FULLY COMPATIBLE"
        recommendation = "Proceed with implementation using the guide!"
    elif percentage >= 80:
        color = Colors.GREEN
        verdict = "✅ COMPATIBLE"
        recommendation = "Minor adjustments may be needed. Review warnings."
    elif percentage >= 60:
        color = Colors.YELLOW
        verdict = "⚠️ PARTIALLY COMPATIBLE"
        recommendation = "Some modifications required. Manual review needed."
    else:
        color = Colors.RED
        verdict = "❌ NOT COMPATIBLE"
        recommendation = "Major structural changes detected. Significant work required."
    
    print(f"\n{color}Score: {scores['passed']}/{scores['total']} ({percentage:.1f}%){Colors.END}")
    print(f"{color}{verdict}{Colors.END}")
    print(f"\n{recommendation}")
    
    # Specific recommendations
    print(f"\n{Colors.BLUE}📋 RECOMMENDATIONS:{Colors.END}")
    
    if percentage >= 80:
        print(f"  1. {Colors.GREEN}✓{Colors.END} Structure is compatible")
        print(f"  2. Follow RESUME_FEATURE_IMPLEMENTATION_GUIDE.md step-by-step")
        print(f"  3. Run tests after each step")
        print(f"  4. Create git commits for each modification")
    else:
        print(f"  1. {Colors.YELLOW}!{Colors.END} Review failed checks above")
        print(f"  2. Compare fresh garak structure with expected structure")
        print(f"  3. Adjust implementation steps as needed")
        print(f"  4. Consider using compatibility layer or adapter pattern")
    
    if scores['passed'] < scores['total']:
        print(f"\n{Colors.YELLOW}Missing/Different Components:{Colors.END}")
        print(f"  - Review each ⚠️ and ❌ item above")
        print(f"  - Check if functionality moved to different files")
        print(f"  - Verify garak API hasn't changed significantly")
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"\n💡 Tip: Run this script in a fresh garak directory before implementing")
    print(f"📖 Guide: See RESUME_FEATURE_IMPLEMENTATION_GUIDE.md for details\n")

if __name__ == "__main__":
    main()
