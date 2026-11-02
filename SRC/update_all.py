# PROPLENS UPDATE CONTROLLER
#
# WHY THIS FILE EXISTS
# Previously we ran the collector, loader and reporting scripts separately.
# That was easy to forget or run in the wrong order. This file puts those
# existing scripts into one repeatable sequence.
#
# HOW IT WORKS
# 1. subprocess starts each script as a separate Python process.
# 2. sys.executable means every script uses the SAME Python environment
#    as this controller, including its installed packages.
# 3. cwd=PROJECT sets the working folder to the project root so relative
#    paths such as Data/ and Outputs/ resolve correctly.
# 4. check=True raises an error and STOPS the sequence if any script fails.
#    This avoids running later reports after a known earlier failure.
#
# IMPORTANT LIMITATIONS
# The scripts write files as they run. If a late step fails, earlier files
# may already have changed. This is NOT an all-or-nothing transaction.
# It also does not schedule itself: you still run it manually.
# Run from the project root with:
# .\.venv\Scripts\python.exe SRC/update_all.py

# PROPLENS: ONE COMMAND TO UPDATE COLLECTION, DATABASE AND REPORTS.
# Run from project root: .\.venv\Scripts\python.exe SRC/update_all.py

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "SRC"

steps = [
    "collect_new.py",
    "load.py",
    "set_reporting_period.py",
    "station_quality.py",
    "match_stations.py",
    "compare_properties.py",
    "compare_pm25.py",
    "monthly_trends.py",
    "monthly_pm25.py",
    "hourly_patterns.py",
]

for number, script in enumerate(steps, start=1):
    print(f"\nSTEP {number}/{len(steps)}: {script}", flush=True)
    subprocess.run([sys.executable, str(SRC / script)], cwd=PROJECT, check=True)

print("\nPropLens update finished successfully. Restart or rerun Streamlit to view updated reports.")
