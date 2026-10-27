# PROPLENS - MAIN ETL PIPELINE
# Purpose: Run data collection and database loading automatically.
#
# The steps must happen in order:
# 1. Collect new measurements from the LAQN API.
# 2. Load saved measurements into DuckDB.


# Import subprocess, a built-in Python module.
# It allows one Python program to run another program.
import subprocess

# Import sys so we can access the Python interpreter
# currently running our project.
import sys

# Import Path to locate our project files reliably.
from pathlib import Path


# Find the folder containing this script (SRC).
script_folder = Path(__file__).resolve().parent

# Find the main PropLens project folder.
# .parent moves up one folder from SRC.
project_folder = script_folder.parent


# STEP 1: Run the collection script.
print("STEP 1: Collecting new air quality data...", flush=True)

subprocess.run(
    [
        sys.executable,                  # Use our current Python environment.
        str(script_folder / "collect_new.py")
    ],
    cwd=project_folder,                  # Run from the PropLens folder.
    check=True                           # Stop if this script fails.
)


# STEP 2: Run the database loading script.
print("STEP 2: Loading measurements into DuckDB...", flush=True)

subprocess.run(
    [
        sys.executable,                  # Use the same Python environment.
        str(script_folder / "load.py")
    ],
    cwd=project_folder,
    check=True
)


# Only print this if both scripts completed successfully.
print("PropLens pipeline completed successfully!")