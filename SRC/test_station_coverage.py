# PROPLENS - STATION DATA AVAILABILITY TEST
# Purpose: Check whether six London stations provide
# actual numerical measurements for our chosen pollutants.

import json                 # Read and save JSON data.
import requests             # Retrieve data from the LAQN API.
from pathlib import Path    # Work with folders and filenames.

# Import csv, a built-in Python module for working with CSV files.
# CSV stands for comma-separated values, a simple table format.
import csv

# One station and pollutant combination for each region.
# These are candidates that we're testing, not final choices.
# PROPLENS - SECOND STATION AVAILABILITY TEST
# Purpose: Find alternative usable measurements in areas
# where our first test returned no numerical values.

test_targets = [
    ("TH4", "NO2"),    # East London: try NO2 instead of PM2.5.
    ("HG1", "NO2"),    # North London: try another Haringey station.
    ("LH0", "NO2")     # West London: try NO2 instead of PM2.5.
]


# Test one completed day that we've used previously.
start_date = "2026-10-19"
end_date = "2026-10-20"

# Use our existing raw data folder.
raw_folder = Path("Data/raw")

# Create an empty list to collect our test results.
# Each result will describe one station and pollutant combination.
coverage_results = []

# Check every station and pollutant combination.
for site_code, species_code in test_targets:

    # Create the expected filename for this request.
    filename = (
        f"{site_code}_{species_code}_{start_date}_{end_date}.json"
    )

    # Identify where its response should be saved.
    file_path = raw_folder / filename

    # Reuse existing data whenever possible.
    if file_path.exists():

        # Read the previously saved JSON file.
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

    else:

        # Construct the API URL using the station,
        # pollutant and dates we're testing.
        url = (
            "https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
            f"SiteCode={site_code}/SpeciesCode={species_code}/"
            f"StartDate={start_date}/EndDate={end_date}/Json"
        )

        # Request the measurements.
        response = requests.get(url, timeout=30)

        # Stop if the request was unsuccessful.
        response.raise_for_status()

        # Convert the response into Python data.
        data = response.json()

        # Check that the response contains the expected structure.
        raw_data = data.get("RawAQData")

        if not isinstance(raw_data, dict):
            raise ValueError(f"Unexpected API response for {site_code}")

        if (
            raw_data.get("@SiteCode") != site_code
            or raw_data.get("@SpeciesCode") != species_code
            or not isinstance(raw_data.get("Data"), list)
        ):
            raise ValueError(f"Invalid measurements for {site_code}")

        # Preserve the original response for future use.
        with open(file_path, "x", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    # Access the measurement list from the response.
    measurements = data["RawAQData"]["Data"]

    # Count readings that can actually be converted into numbers.
    # This excludes empty and non-numeric values.
    valid_readings = 0

    for measurement in measurements:

        # Extract the measurement value.
        value = measurement.get("@Value")

        # Missing values are not counted as valid.
        if value in ("", None):
            continue

        # Check whether the value represents a number.
        try:
            float(value)
            valid_readings += 1

        # Ignore values that cannot be converted into numbers.
        except (ValueError, TypeError):
            continue

    # Show how much usable data this station returned.
    print(
        f"{site_code} | {species_code} | "
        f"{valid_readings}/{len(measurements)} numerical readings"
    )


    # Save the current station's results in a dictionary.
# This gives us one structured record for each test.
coverage_results.append({
    "site_code": site_code,
    "species_code": species_code,
    "start_date": start_date,
    "hourly_records": len(measurements),
    "numerical_readings": valid_readings
})

# Choose where to save our coverage test results.
output_path = Path("Data/station_coverage.csv")

# Create or replace a CSV file containing this test run's results.
# newline="" avoids unnecessary blank lines on Windows.
with open(output_path, "w", newline="", encoding="utf-8") as file:

    # Define the column names for our CSV table.
    columns = [
        "site_code",
        "species_code",
        "start_date",
        "hourly_records",
        "numerical_readings"
    ]

    # Create a CSV writer that understands dictionaries.
    writer = csv.DictWriter(file, fieldnames=columns)

    # Write the column headings.
    writer.writeheader()

    # Write one row for each tested station.
    writer.writerows(coverage_results)

# Confirm where the results were saved.
print(f"Coverage results saved to: {output_path}")