# PROPLENS - INCREMENTAL DATA COLLECTION

# Purpose: Download missing daily air quality measurements
# for the stations and pollutants selected in config.py.

# Previously downloaded JSON files are reused.
# A configurable limit controls downloads per target.


# Import Python's tools for working with dates.
from datetime import datetime, timedelta, timezone

# Import Path for working with files and folders.
from pathlib import Path

# Import json to save API responses.
import json

# Import requests to communicate with the LAQN API.
import requests
# Used to pause briefly between requests to the LAQN API.
import time

# Read our station choices, starting date and download limit
# from the configuration file.
from config import (
    monitoring_targets,
    historical_start_date,
    max_days_per_target
)


# STEP 1: Set up our dates and folders.

# Convert our configured starting date from text into a date.
start_date = datetime.strptime(
    historical_start_date, "%Y-%m-%d"
).date()

# Find yesterday's date in UTC.
# We avoid collecting today's incomplete measurements.
yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

# Choose the folder where raw JSON files are stored.
raw_folder = Path("Data/raw")

# Create the folder if it does not already exist.
raw_folder.mkdir(parents=True, exist_ok=True)


# STEP 2: Go through every monitoring target.

# This outer loop visits each dictionary in our shopping list.
for target in monitoring_targets:

    # Read the station and pollutant from the current dictionary.
    site_code = target["site_code"]
    species_code = target["species_code"]

    # Tell us which combination we're working on.
    print(f"\nChecking station {site_code}, pollutant {species_code}")

    # Begin checking dates from our configured starting date.
    current_date = start_date

    # Count how many days we've downloaded for this target.
    downloads_for_target = 0


    # STEP 3: Check which dates are missing.

    # This inner loop checks one calendar day at a time.
    while current_date <= yesterday:

        # Calculate the following date.
        next_date = current_date + timedelta(days=1)

        # Create a filename identifying this exact request.
        filename = (
            f"{site_code}_{species_code}_{current_date}_{next_date}.json"
        )

        # Find where the response should be saved.
        file_path = raw_folder / filename

        # If the file already exists, we don't need to download it.
        if file_path.exists():
            print(f"{current_date}: Already saved — skipping")

            # Move to the next day.
            current_date = next_date

            # Skip the remaining instructions in this iteration.
            continue


        # STEP 4: Download the missing day's measurements.

        # Build the API address using the current target and dates.
        url = (
            "https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
            f"SiteCode={site_code}/SpeciesCode={species_code}/"
            f"StartDate={current_date}/EndDate={next_date}/Json"
        )

        print(f"Downloading {site_code} {species_code}: {current_date}")

        # Send a request to the LAQN API.
        response = requests.get(url, timeout=30)

        # Raise an error if the HTTP request fails.
        response.raise_for_status()

        # Convert the response into Python dictionaries and lists.
        data = response.json()


        # STEP 5: Validate the response before saving.

        # Find the main section containing the measurements.
        raw_data = data.get("RawAQData")

        # Check that the section exists and is a dictionary.
        if not isinstance(raw_data, dict):
            raise ValueError("API response is missing RawAQData.")

        # Check that the station and pollutant match our request.
        if (
            raw_data.get("@SiteCode") != site_code
            or raw_data.get("@SpeciesCode") != species_code
        ):
            raise ValueError("API returned an unexpected station or pollutant.")

        # Get the hourly measurement list.
        measurements = raw_data.get("Data")

        # Confirm the measurement records are stored in a list.
        if not isinstance(measurements, list):
            raise ValueError("API response has no measurement list.")


        # STEP 6: Save the original API response.

        # Open a new file without overwriting an existing one.
        with open(file_path, "x", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        # Count readings that contain a numerical value.
        # Empty strings indicate missing measurements.
        valid_readings = sum(
            1 for measurement in measurements
            if measurement.get("@Value") not in ("", None)
        )

        print(f"Saved: {filename}")
        print(f"Hourly records: {len(measurements)}")
        print(f"Non-empty readings: {valid_readings}")

        # Increase the number of downloads made for this target.
        downloads_for_target += 1

        # Pause for one second between API requests.
        # This reduces how quickly we send requests to LAQN.
        time.sleep(1)

        # Move to the next date.
        current_date = next_date

        # Stop downloading for this target once we've reached
        # the maximum number of days allowed in config.py.
        # This helps us control how many API requests we make.
        if downloads_for_target >= max_days_per_target:
            break


# Confirm that we've checked every configured monitoring target.
print("\nData collection finished.")