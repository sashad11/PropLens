
# PROPLENS - INCREMENTAL DATA COLLECTION
#
# Download missing daily LAQN measurements.
# Reuse saved files, retry temporary API failures,
# validate responses and report unsuccessful downloads.

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import time

import requests

from api_utils import validate_response

from config import (
    monitoring_targets,
    historical_start_date,
    max_days_per_target
)


# STEP 1: SET UP DATES AND FOLDERS

start_date = datetime.strptime(
    historical_start_date, "%Y-%m-%d"
).date()

# Yesterday is our latest complete collection date.
yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

# Keep the folder name consistent across operating systems.
raw_folder = Path("Data/Raw")
raw_folder.mkdir(parents=True, exist_ok=True)

# Collect unsuccessful requests so we can report them later.
failed_downloads = []

MAX_ATTEMPTS = 3


# STEP 3: REQUEST DATA WITH RETRIES

def download_data(url):
    """
    Retry temporary network/server problems up to three times.
    Return the downloaded JSON if successful.
    """

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:
            response = requests.get(url, timeout=30)

            # Most 4xx errors indicate a request problem.
            # 429 means rate-limited, so we can retry it.
            if (
                400 <= response.status_code < 500
                and response.status_code != 429
            ):
                response.raise_for_status()

            response.raise_for_status()

            # A successful HTTP response might still contain
            # invalid JSON. The caller will report that failure.
            return response.json()

        except requests.RequestException as error:

            # Do not retry ordinary client errors such as 404.
            status = getattr(
                getattr(error, "response", None),
                "status_code",
                None
            )

            if status is not None and 400 <= status < 500 and status != 429:
                raise

            print(
                f"Attempt {attempt}/{MAX_ATTEMPTS} failed: {error}"
            )

            if attempt == MAX_ATTEMPTS:
                raise

            # Gradually increase the wait between attempts.
            time.sleep(2 * attempt)


# STEP 4: CHECK EVERY TARGET AND DATE

for target in monitoring_targets:

    site_code = target["site_code"]
    species_code = target["species_code"]

    print(f"\nChecking station {site_code}, pollutant {species_code}")

    current_date = start_date
    downloads_for_target = 0

    while current_date <= yesterday:

        # Respect the per-target download limit.
        if downloads_for_target >= max_days_per_target:
            break

        next_date = current_date + timedelta(days=1)

        filename = (
            f"{site_code}_{species_code}_{current_date}_{next_date}.json"
        )

        file_path = raw_folder / filename

        # Cached days require no new API request.
        if file_path.exists():
            print(f"{current_date}: Already saved - skipping")
            current_date = next_date
            continue

        url = (
            "https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
            f"SiteCode={site_code}/SpeciesCode={species_code}/"
            f"StartDate={current_date}/EndDate={next_date}/Json"
        )

        print(f"Downloading {site_code} {species_code}: {current_date}")

        try:
            # Fetch and validate before saving.
            data = download_data(url)

            measurements = validate_response(
                data, site_code, species_code
            )

            # Write to a temporary file first.
            # Only rename it to .json when writing succeeds.
            temporary_path = file_path.with_suffix(".json.tmp")

            with open(
                temporary_path,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(data, file, indent=4)

            temporary_path.replace(file_path)

            valid_readings = sum(
                1 for measurement in measurements
                if measurement.get("@Value") not in ("", None)
            )

            print(f"Saved: {filename}")
            print(f"Hourly records: {len(measurements)}")
            print(f"Non-empty readings: {valid_readings}")

            downloads_for_target += 1

            # Give the API a short break between downloads.
            time.sleep(1)

        except (requests.RequestException, ValueError) as error:

            print(f"FAILED: {filename} - {error}")

            failed_downloads.append({
                "file": filename,
                "reason": str(error)
            })

            # Leave the daily JSON absent so a future run
            # knows it still needs downloading.

        # Continue checking subsequent dates.
        current_date = next_date


# STEP 5: REPORT THE OUTCOME

print("\nData collection finished.")

if failed_downloads:

    print(f"\nUnsuccessful downloads: {len(failed_downloads)}")

    for failure in failed_downloads:
        print(f"{failure['file']}: {failure['reason']}")

    # A non-zero exit code makes the failure visible to
    # pipeline.py rather than silently claiming success.
    raise RuntimeError(
        f"Collection incomplete: {len(failed_downloads)} failed downloads."
    )

else:
    print("No download failures detected.")
