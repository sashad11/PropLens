# PROPLENS - COLLECTION PLANNER
# Purpose: Identify which days of air quality data still need downloading.
# This script DOES NOT make any API requests.


# Import Python's date and time tools.
from datetime import datetime, timedelta, timezone

# Import Path to check whether saved files exist.
from pathlib import Path


# Choose our test monitoring station and pollutant.
# These will become configurable when we expand PropLens.
site_code = "BX1"
species_code = "NO2"


# Define where our collection history begins.
# We've already downloaded measurements for this date.
start_date = datetime.strptime("2026-10-19", "%Y-%m-%d").date()


# Calculate yesterday's date using UTC.
# LAQN's hourly measurements are labelled in GMT.
# We avoid today because today's measurements are incomplete.
yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)


# Point to the folder containing our saved API responses.
# Match the capitalisation of your actual folders.
raw_folder = Path("Data/raw")


# Start checking from our earliest collection date.
current_date = start_date


# Repeat while the date is no later than yesterday.
while current_date <= yesterday:

    # Calculate the next calendar date.
    # The API uses a start date and an end date.
    next_date = current_date + timedelta(days=1)

    # Build the expected filename using our naming convention.
    filename = (
        f"{site_code}_{species_code}_{current_date}_{next_date}.json"
    )

    # Combine the folder path and filename.
    file_path = raw_folder / filename

    # Check whether we already have this day's response.
    if file_path.exists():
        print(f"{current_date}: Already saved — skip")

    else:
        # This is a date we still need to download.
        # We only print it for now, rather than calling the API.
        print(f"{current_date}: Needs downloading")

    # Move forward one day before repeating the loop.
    current_date = next_date