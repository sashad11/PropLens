# PROPLENS - DATABASE LOADING
# Purpose: Load all saved LAQN JSON files into DuckDB.
# Existing measurements are skipped to prevent duplicates.


# Import the packages and modules we need.
import json
import duckdb
from pathlib import Path


# STEP 1: Find our saved data files.

# Identify the folder containing downloaded API responses.
raw_folder = Path("Data/raw")

# Find only our daily measurement files.
# Each filename ends with two dates in YYYY-MM-DD format.
# This excludes london_stations.json, which contains station information.
raw_files = sorted(
    raw_folder.glob("*_????-??-??_????-??-??.json")
)

# Display how many files we found.
print(f"Raw JSON files found: {len(raw_files)}")


# STEP 2: Connect to DuckDB.

# Open our existing database.
connection = duckdb.connect("Data/proplens.duckdb")

# Create the measurements table if it doesn't exist.
connection.execute("""
    CREATE TABLE IF NOT EXISTS measurements (

        -- Monitoring station identifier.
        site_code VARCHAR,

        -- Pollutant identifier.
        species_code VARCHAR,

        -- Date and time of the hourly measurement.
        measured_at TIMESTAMP,

        -- Pollution concentration.
        -- NULL is allowed because some readings are missing.
        value DOUBLE,

        -- Each station, pollutant and timestamp combination is unique.
        PRIMARY KEY (site_code, species_code, measured_at)
    )
""")
# Create a second table to remember which JSON files
# have already been successfully loaded into DuckDB.
connection.execute("""
    CREATE TABLE IF NOT EXISTS processed_files (

        -- Each filename can appear only once.
        filename VARCHAR PRIMARY KEY,

        -- Record when we finished loading the file.
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")


# STEP 3: Check how many records we already have.

rows_before = connection.execute(
    "SELECT COUNT(*) FROM measurements"
).fetchone()[0]


# STEP 4: Process every saved JSON file.

# Keep track of how many measurements we process.
total_processed = 0

for raw_file in raw_files:

    # Look for this filename in our processing log.
    already_processed = connection.execute(
        "SELECT 1 FROM processed_files WHERE filename = ?",
        [raw_file.name]
    ).fetchone()

    # Skip the file if we've already loaded it successfully.
    if already_processed:
        print(f"Already processed: {raw_file.name}")
        continue

    # Otherwise, we need to load this file.
    print(f"Processing: {raw_file.name}")

    # Open the saved file and read its JSON contents.
    with open(raw_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Access the nested air quality information.
    raw_data = data["RawAQData"]

    # Identify the station and pollutant.
    site_code = raw_data["@SiteCode"]
    species_code = raw_data["@SpeciesCode"]

    # Retrieve the list of hourly measurements.
    measurements = raw_data["Data"]

    # Create an empty list for this file's cleaned records.
    cleaned_measurements = []

    # Clean every measurement in the current file.
    for measurement in measurements:

        # Extract the date and time.
        timestamp = measurement["@MeasurementDateGMT"]

        # Extract the concentration as text.
        raw_value = measurement["@Value"]

        # Convert blank values into None.
        # Convert numerical text into a decimal number.
        if raw_value == "":
            value = None
        else:
            value = float(raw_value)

        # Group the cleaned fields in the order our SQL expects.
        cleaned_measurements.append(
            (site_code, species_code, timestamp, value)
        )

    # Count the records processed from this file.
    total_processed += len(cleaned_measurements)

        # Start a transaction so loading the measurements and
    # recording the processed file succeed together.
    connection.execute("BEGIN TRANSACTION")

    try:
        # Insert measurements into DuckDB.
        # Existing primary keys are skipped to prevent duplicates.
        if cleaned_measurements:
            connection.executemany(
                """
                INSERT INTO measurements
                    (site_code, species_code, measured_at, value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                cleaned_measurements
            )

        # Mark this JSON file as successfully processed.
        connection.execute(
            "INSERT INTO processed_files (filename) VALUES (?)",
            [raw_file.name]
        )

        # Save both changes permanently.
        connection.execute("COMMIT")

    except Exception:
        # Undo changes to this file's data if something fails.
        # This prevents a file being incorrectly marked as loaded.
        connection.execute("ROLLBACK")
        raise


# STEP 5: Check the results.

# Count the total rows after processing all files.
rows_after = connection.execute(
    "SELECT COUNT(*) FROM measurements"
).fetchone()[0]

# Calculate how many new measurements were inserted.
new_rows = rows_after - rows_before

# Close the database safely.
connection.close()


# Display a summary of the loading process.
print("------------------------------")
print(f"Measurements processed: {total_processed}")
print(f"New rows inserted: {new_rows}")
print(f"Total rows in database: {rows_after}")