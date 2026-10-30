
# PROPLENS: INCREMENTAL DATA COLLECTION
#
# PURPOSE:
# Collect daily air quality measurements from LAQN.
#
# This script:
# 1. Reuses older downloaded JSON files.
# 2. Refreshes the most recent completed days.
# 3. Retries temporary API failures.
# 4. Checks responses before saving them.
# 5. Reports any unsuccessful downloads.


# STEP 1: IMPORT OUR TOOLS

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import time

import requests

# Our reusable API functions.
from api_utils import validate_response, download_data

# Our project settings.
from config import (
    monitoring_targets,
    historical_start_date,
    max_days_per_target,
    refresh_days
)


# STEP 2: SET UP THE DATES

# Convert the historical starting date into a Python date.
start_date = datetime.strptime(
    historical_start_date, "%Y-%m-%d"
).date()

# Collect only completed days.
# We use yesterday in UTC to avoid today's incomplete data.
yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

# Find the first day of our refresh period.
# With refresh_days = 7, we revisit the last seven days.
refresh_start = yesterday - timedelta(days=refresh_days - 1)


# STEP 3: SET UP OUR FOLDERS

# Find the main PropLens project folder.
project_folder = Path(__file__).resolve().parents[1]

# Find the folder containing downloaded measurements.
raw_folder = project_folder / "Data/Raw"

# Create the folder if it does not exist.
raw_folder.mkdir(parents=True, exist_ok=True)

# Remember any downloads that fail.
failed_downloads = []


# STEP 4: CHECK EACH STATION AND POLLUTANT

for target in monitoring_targets:

    # Identify the station and pollutant to collect.
    site_code = target["site_code"]
    species_code = target["species_code"]

    print(f"\nChecking station {site_code}, pollutant {species_code}")

    # Start checking from our historical starting date.
    current_date = start_date

    # Count successful API downloads for this target.
    downloads_for_target = 0


    # STEP 5: CHECK EVERY DATE

    while current_date <= yesterday:

        # Limit how many API downloads we make per target.
        if downloads_for_target >= max_days_per_target:
            break

        # LAQN uses a start date and an end date.
        next_date = current_date + timedelta(days=1)

        # Give each daily response a unique filename.
        filename = (
            f"{site_code}_{species_code}_{current_date}_{next_date}.json"
        )

        file_path = raw_folder / filename

        # Check whether this date is within our refresh period.
        needs_refresh = current_date >= refresh_start

        # Older cached files can be reused.
        if file_path.exists() and not needs_refresh:
            print(f"{current_date}: Already saved, skipping")

            current_date = next_date
            continue

        # Recent files should be downloaded again.
        if file_path.exists() and needs_refresh:
            print(f"{current_date}: Refreshing existing measurements")


        # STEP 6: BUILD THE API REQUEST

        url = (
            "https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
            f"SiteCode={site_code}/SpeciesCode={species_code}/"
            f"StartDate={current_date}/EndDate={next_date}/Json"
        )

        print(f"Downloading {site_code} {species_code}: {current_date}")


        # STEP 7: DOWNLOAD AND VALIDATE THE DATA

        try:

            # Download data using our retry function.
            data = download_data(url)

            # Check that LAQN returned the correct
            # station, pollutant and measurement structure.
            measurements = validate_response(
                data,
                site_code,
                species_code
            )


            # STEP 8: SAVE THE DATA SAFELY

            # First save to a temporary file.
            # This protects the previous JSON if a
            # download or validation fails.
            temporary_path = file_path.with_suffix(".json.tmp")

            with open(
                temporary_path,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(data, file, indent=4)

            # Replace the previous JSON only after
            # the new file has been written successfully.
            temporary_path.replace(file_path)


            # STEP 9: COUNT VALID READINGS

            # Empty values represent missing measurements.
            valid_readings = sum(
                1 for measurement in measurements
                if measurement.get("@Value") not in ("", None)
            )

            print(f"Saved: {filename}")
            print(f"Hourly records: {len(measurements)}")
            print(f"Non-empty readings: {valid_readings}")

            # Count this successful API download.
            downloads_for_target += 1

            # Pause briefly to avoid sending requests too quickly.
            time.sleep(1)


        # STEP 10: HANDLE FAILED DOWNLOADS

        except (requests.RequestException, ValueError, OSError) as error:

            print(f"FAILED: {filename}")
            print(f"Reason: {error}")

            # Remember the failure for our final report.
            failed_downloads.append({
                "file": filename,
                "reason": str(error)
            })

            # Do not replace the old JSON if the request fails.
            # The next run can attempt this date again.

        # Move to the following date.
        current_date = next_date


# STEP 11: REPORT THE RESULTS

print("\nData collection finished.")

if failed_downloads:

    print(f"Unsuccessful downloads: {len(failed_downloads)}")

    for failure in failed_downloads:
        print(f"{failure['file']}: {failure['reason']}")

    # Tell the pipeline that collection was incomplete.
    raise RuntimeError(
        f"Collection incomplete: {len(failed_downloads)} failed downloads."
    )

else:
    print("No download failures detected.")
