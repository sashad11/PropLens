# PROPLENS - DATABASE LOADING
# Purpose: Read saved air quality data and load it into DuckDB.
# Duplicate measurements should not be inserted again.


# Import the modules we need.
import json                 # Reads our saved JSON data.
import duckdb               # Lets Python communicate with DuckDB.
from pathlib import Path    # Helps us work with file paths.


# Identify the raw JSON file we previously downloaded.
raw_file = Path(
    "data/raw/BX1_NO2_2026-10-19_2026-10-20.json"
)


# Open the JSON file and convert its contents into Python data.
# The file is automatically closed when the 'with' block finishes.
with open(raw_file, "r", encoding="utf-8") as file:
    data = json.load(file)


# Access the information inside the nested JSON response.
raw_data = data["RawAQData"]

# Extract the monitoring station and pollutant codes.
site_code = raw_data["@SiteCode"]
species_code = raw_data["@SpeciesCode"]

# Get the list of hourly measurements.
measurements = raw_data["Data"]


# Create an empty list to hold our cleaned records.
cleaned_measurements = []


# Go through every hourly measurement.
for measurement in measurements:

    # Extract the timestamp.
    timestamp = measurement["@MeasurementDateGMT"]

    # Extract the original measurement value.
    raw_value = measurement["@Value"]

    # Convert numerical text into a number.
    # Missing values become None, which DuckDB stores as NULL.
    if raw_value == "":
        value = None
    else:
        value = float(raw_value)

    # Store the cleaned information as a tuple.
    # A tuple groups values in a fixed order.
    # The order matches our database columns.
    cleaned_measurements.append(
        (site_code, species_code, timestamp, value)
    )


# Connect to the database we created in Step 11.
connection = duckdb.connect("data/proplens.duckdb")


# Create the table if it does not already exist.
# This also allows the script to work if the database is new.
connection.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        site_code VARCHAR,
        species_code VARCHAR,
        measured_at TIMESTAMP,
        value DOUBLE,
        PRIMARY KEY (site_code, species_code, measured_at)
    )
""")


# Count how many rows are in the table BEFORE loading.
rows_before = connection.execute(
    "SELECT COUNT(*) FROM measurements"
).fetchone()[0]


# Insert our cleaned records into DuckDB.
# The ? symbols are placeholders for the four values in each tuple.
# ON CONFLICT DO NOTHING skips any record whose primary key
# already exists in the table.
connection.executemany(
    """
    INSERT INTO measurements
        (site_code, species_code, measured_at, value)
    VALUES (?, ?, ?, ?)
    ON CONFLICT DO NOTHING
    """,
    cleaned_measurements
)


# Count how many rows are in the table AFTER loading.
rows_after = connection.execute(
    "SELECT COUNT(*) FROM measurements"
).fetchone()[0]


# Calculate how many new rows were inserted.
new_rows = rows_after - rows_before


# Close the database connection.
connection.close()


# Print a summary so we can verify what happened.
print(f"Measurements processed: {len(cleaned_measurements)}")
print(f"New rows inserted: {new_rows}")
print(f"Total rows in database: {rows_after}")