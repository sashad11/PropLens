# PROPLENS - DATA EXTRACTION
# Purpose: Download LAQN air quality measurements and save the raw response.
# If the data has already been downloaded, reuse the saved file.


# Import the packages and modules we need.
import json                 # Converts Python data to/from JSON files.
from pathlib import Path    # Helps us work with files and folders.
import requests             # Lets Python communicate with the LAQN API.


# Set the monitoring station, pollutant and dates for our initial test.
# These values are temporary; we'll make them dynamic later.
site_code = "BX1"
species_code = "NO2"
start_date = "2026-10-19"
end_date = "2026-10-20"


# Construct the API URL using our variables.
# An f-string lets us insert variable values using curly brackets {}.
url = (
    f"https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
    f"SiteCode={site_code}/SpeciesCode={species_code}/"
    f"StartDate={start_date}/EndDate={end_date}/Json"
)


# Create a file path for the downloaded data.
# Each file name identifies the station, pollutant and date range.
# Path("data/raw") points to the raw data folder in our project.
file_path = Path("data/raw") / (
    f"{site_code}_{species_code}_{start_date}_{end_date}.json"
)


# Check whether we've already downloaded this data.
if file_path.exists():

    # If the file exists, read it instead of contacting the API.
    print("Saved file found. Loading existing data.")

    # Open the file in read mode ("r").
    # with automatically closes the file when we're finished.
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

else:

    # If the file doesn't exist, download the data from the API.
    print("No saved file found. Downloading data from LAQN API.")

    # Make the API request and set a maximum waiting time of 30 seconds.
    response = requests.get(url, timeout=30)

    # Raise an error if the API request was unsuccessful.
    response.raise_for_status()

    # Convert the JSON response into Python dictionaries and lists.
    data = response.json()

    # Open a new file in write mode ("w") to save the response.
    with open(file_path, "w", encoding="utf-8") as file:

        # Save the data as JSON.
        # indent=4 makes the saved file easier for humans to read.
        json.dump(data, file, indent=4)


# Extract the measurement records from the nested response.
raw_data = data["RawAQData"]
measurements = raw_data["Data"]


# Print a summary to verify that our data is available.
print(f"Station: {raw_data['@SiteCode']}")
print(f"Pollutant: {raw_data['@SpeciesCode']}")
print(f"Measurements retrieved: {len(measurements)}")
print(f"Raw data file: {file_path}")

# PROPLENS - FIRST DATA TRANSFORMATION TEST
# PROPLENS - TRANSFORM ALL MEASUREMENTS
# Purpose: Clean every hourly measurement returned by the API.


# Create an empty list to store our cleaned measurements.
# As we clean each measurement, we'll add it to this list.
cleaned_measurements = []


# A for loop repeats the same instructions for every item in a list.
# Here, 'measurement' represents one hourly reading at a time.
for measurement in measurements:

    # Extract the timestamp from the current measurement.
    timestamp = measurement["@MeasurementDateGMT"]

    # Extract the original pollution value, which is stored as text.
    raw_value = measurement["@Value"]

    # Check whether the API has provided a numerical value.
    # If the value is missing, represent it using None.
    if raw_value == "":
        value = None

    # Otherwise, convert the text into a decimal number.
    else:
        value = float(raw_value)

    # Organise the cleaned information into a dictionary.
    cleaned_measurement = {
        "site_code": site_code,
        "species_code": species_code,
        "measured_at": timestamp,
        "value": value
    }

    # Add the cleaned dictionary to our list.
    # append() puts a new item at the end of a list.
    cleaned_measurements.append(cleaned_measurement)


# Count how many cleaned records we now have.
print(f"Cleaned measurements: {len(cleaned_measurements)}")

# Display the first three records to check our results.
# [:3] means take the first three items from the list.
print("First three cleaned measurements:")

for measurement in cleaned_measurements[:3]:
    print(measurement)