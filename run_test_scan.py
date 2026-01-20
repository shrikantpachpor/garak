#!/usr/bin/env python3
"""Simple test runner for garak scan"""

import subprocess
import sys

print("Starting garak scan...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "garak", "--config", "garak-config.yaml"],
        cwd="e:\\SHRIKANT\\projects\\garak-resume-3"
    )
    print(f"Scan completed with return code: {result.returncode}")
except Exception as e:
    print(f"Error running scan: {e}")
    sys.exit(1)
