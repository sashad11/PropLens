
# PROPLENS - DATABASE LOADING
#
# Purpose:
# Load saved LAQN measurements into DuckDB.
#
# The loader can:
# 1. Insert new measurements.
# 2. Update measurements corrected by LAQN.
# 3. Skip files that have not changed.
# 4. Report new, updated and unchanged readings.


# STEP 1: IMPORT THE TOOLS WE NEED

# Read the JSON files downloaded from LAQN.
import json

# Calculate a fingerprint of each JSON file.
import hashlib

# Work with files and folders.
from pathlib import Path

# Store and query our measurements.
import duckdb


# STEP 2: FIND OUR PROJECT FILES

# Find the main PropLens folder automatically.
# This works even if we run the script from another folder.
project_folder = Path(__file__).resolve().parents[1]

# Location of our downloaded JSON files.
raw_folder = project_folder / "Data/Raw"

# Location of our DuckDB database.
database_path = project_folder / "Data/proplens.duckdb"

# Find only daily measurement JSON files.
# This excludes the station metadata file.
raw_files = sorted(
    raw_folder.glob("*_????-??-??_????-??-??.json")
)

print(f"Raw JSON files found: {len(raw_files)}")


# STEP 3: CREATE A FILE FINGERPRINT FUNCTION

def file_hash(file_path):
    """
    Calculate a unique fingerprint of a file's contents.

    If the JSON file changes, its fingerprint changes.
    This helps us recognise corrected API data.
    """

    # Open the file in binary mode.
    with open(file_path, "rb") as file:
        contents = file.read()

    # SHA256 turns the file contents into a fingerprint.
    return hashlib.sha256(contents).hexdigest()


# STEP 4: CONNECT TO DUCKDB

connection = duckdb.connect(str(database_path))

# Create our measurements table if necessary.
connection.execute("""
    CREATE TABLE IF NOT EXISTS measurements (

        -- The monitoring station.
        site_code VARCHAR,

        -- The pollutant being measured.
        species_code VARCHAR,

        -- The hour of the measurement.
        measured_at TIMESTAMP,

        -- The pollution concentration.
        -- NULL represents an unavailable reading.
        value DOUBLE,

        -- A measurement is identified by its
        -- station, pollutant and timestamp.
        PRIMARY KEY (
            site_code,
            species_code,
            measured_at
        )
    )
""")


# STEP 5: SET UP THE PROCESSED FILES TABLE

# This table remembers which JSON files were loaded.
connection.execute("""
    CREATE TABLE IF NOT EXISTS processed_files (

        filename VARCHAR PRIMARY KEY,

        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# The old version of PropLens only stored filenames.
# Our improved loader also needs to store a file hash.
#
# Check which columns already exist.
existing_columns = [
    row[1]
    for row in connection.execute(
        "PRAGMA table_info('processed_files')"
    ).fetchall()
]

# Add the file_hash column if it does not exist.
# This updates the existing table without deleting its rows.
if "file_hash" not in existing_columns:

    connection.execute("""
        ALTER TABLE processed_files
        ADD COLUMN file_hash VARCHAR
    """)

    print("Added file_hash column to processed_files.")


# STEP 6: PREPARE OUR COUNTERS

# Count the different types of measurement changes.
new_rows = 0
updated_rows = 0
unchanged_rows = 0

# Count how many files needed processing.
processed_file_count = 0

# Count files we could safely skip.
skipped_file_count = 0


# STEP 7: CHECK EVERY SAVED JSON FILE

for raw_file in raw_files:

    # Calculate the fingerprint of the current file.
    current_hash = file_hash(raw_file)

    # Look up the fingerprint stored from its previous load.
    previous_file = connection.execute(
        """
        SELECT file_hash
        FROM processed_files
        WHERE filename = ?
        """,
        [raw_file.name]
    ).fetchone()

    # If the filename AND its contents are unchanged,
    # there is no reason to load this file again.
    if (
        previous_file is not None
        and previous_file[0] == current_hash
    ):

        skipped_file_count += 1
        continue

    # A new fingerprint means this is either:
    # 1. A completely new file.
    # 2. A file whose contents have changed.
    # 3. An older file without a stored fingerprint.
    print(f"Processing: {raw_file.name}")

    # Read the JSON response.
    with open(raw_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Find the measurements inside the response.
    raw_data = data["RawAQData"]

    # Read the station and pollutant identifiers.
    site_code = raw_data["@SiteCode"]
    species_code = raw_data["@SpeciesCode"]

    # Get the hourly measurement records.
    measurements = raw_data["Data"]

    # Prepare the measurements for DuckDB.
    cleaned_measurements = []

    for measurement in measurements:

        # Read the measurement timestamp.
        timestamp = measurement["@MeasurementDateGMT"]

        # Read the concentration as text.
        raw_value = measurement["@Value"]

        # Convert missing values into Python None.
        # DuckDB will store these as NULL.
        if raw_value in ("", None):
            value = None

        else:
            value = float(raw_value)

        cleaned_measurements.append(
            (site_code, species_code, timestamp, value)
        )

    # Track changes for this individual file.
    file_new = 0
    file_updated = 0
    file_unchanged = 0

    # STEP 8: START A DATABASE TRANSACTION
    #
    # A transaction keeps the measurements and file log
    # together. If something goes wrong, DuckDB undoes
    # this file's changes.

    connection.execute("BEGIN TRANSACTION")

    try:

        # STEP 9: INSERT OR UPDATE EACH MEASUREMENT

        for (
            measurement_site,
            measurement_species,
            timestamp,
            new_value
        ) in cleaned_measurements:

            # Check whether this measurement already exists.
            existing_row = connection.execute(
                """
                SELECT value
                FROM measurements
                WHERE site_code = ?
                  AND species_code = ?
                  AND measured_at = ?
                """,
                [
                    measurement_site,
                    measurement_species,
                    timestamp
                ]
            ).fetchone()

            if existing_row is None:

                # This timestamp has never been stored.
                file_new += 1

            elif existing_row[0] != new_value:

                # The measurement exists, but its value changed.
                # This also detects changes to or from NULL.
                file_updated += 1

            else:

                # The value is the same as before.
                file_unchanged += 1

            # Insert a new measurement when no row exists.
            #
            # If the primary key already exists, update its
            # value only when it is different.
            #
            # IS DISTINCT FROM also compares NULL values
            # correctly, unlike a normal != comparison.
            connection.execute(
                """
                INSERT INTO measurements (
                    site_code,
                    species_code,
                    measured_at,
                    value
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT (
                    site_code,
                    species_code,
                    measured_at
                )

                DO UPDATE SET
                    value = EXCLUDED.value

                WHERE measurements.value
                      IS DISTINCT FROM EXCLUDED.value
                """,
                [
                    measurement_site,
                    measurement_species,
                    timestamp,
                    new_value
                ]
            )

        # STEP 10: REMEMBER THIS FILE'S NEW FINGERPRINT
        #
        # Also update its processing timestamp.
        # This allows us to skip it on the next run,
        # unless its contents change again.

        connection.execute(
            """
            INSERT INTO processed_files (
                filename,
                file_hash,
                processed_at
            )
            VALUES (?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT (filename)

            DO UPDATE SET
                file_hash = EXCLUDED.file_hash,
                processed_at = EXCLUDED.processed_at
            """,
            [raw_file.name, current_hash]
        )

        # Save the measurements and fingerprint together.
        connection.execute("COMMIT")

    except Exception:

        # Undo the current file's database changes.
        connection.execute("ROLLBACK")

        # Show which file caused the problem.
        print(f"Failed while processing: {raw_file.name}")

        raise

    # Only add the counts after the transaction succeeds.
    new_rows += file_new
    updated_rows += file_updated
    unchanged_rows += file_unchanged

    processed_file_count += 1

    print(
        f"New: {file_new} | "
        f"Updated: {file_updated} | "
        f"Unchanged: {file_unchanged}"
    )


# STEP 11: CHECK THE FINAL DATABASE SIZE

total_rows = connection.execute(
    "SELECT COUNT(*) FROM measurements"
).fetchone()[0]

# Close the connection.
connection.close()


# STEP 12: DISPLAY THE FINAL REPORT

print("\nPROPLENS - DATABASE LOADING REPORT")
print("----------------------------------")

print(f"JSON files processed: {processed_file_count}")
print(f"Unchanged files skipped: {skipped_file_count}")

print(f"\nNew measurements: {new_rows}")
print(f"Updated measurements: {updated_rows}")
print(f"Unchanged measurements: {unchanged_rows}")

print(f"\nTotal rows in database: {total_rows}")
print("\nDatabase loading completed successfully.")
