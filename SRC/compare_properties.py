
# PROPLENS - PROPERTY ENVIRONMENTAL COMPARISON
# Purpose: Combine property-to-station matches with
# historical LAQN pollution measurements.

import csv
import duckdb


# STEP 1: CONNECT TO OUR DATABASE

connection = duckdb.connect("Data/proplens.duckdb")

# Read the property matching results from our CSV.
# DuckDB can read CSV files directly using SQL.
connection.execute("""
    CREATE OR REPLACE TEMP VIEW property_matches AS
    SELECT *
    FROM read_csv_auto('Data/property_matches.csv')
""")


# STEP 2: COMPARE PROPERTY LOCATIONS

# Join each property to measurements from its matched station.
results = connection.execute("""
    SELECT
        p.property_name,
        p.station_code,
        p.distance_km,

        -- Calculate average NO2 concentration.
        -- AVG ignores NULL values automatically.
        ROUND(AVG(m.value), 2) AS average_no2,

        -- Count all stored hourly measurements.
        COUNT(*) AS recorded_hours,

        -- Count measurements containing numerical values.
        COUNT(m.value) AS valid_hours,

        -- Calculate completeness among stored records.
        ROUND(
            100.0 * COUNT(m.value) / COUNT(*),
            1
        ) AS completeness_percent

    FROM property_matches p

    -- Connect properties to their matched monitoring stations.
    JOIN measurements m
        ON p.station_code = m.site_code

    -- Only compare NO2 with NO2.
    WHERE m.species_code = 'NO2'

    GROUP BY
        p.property_name,
        p.station_code,
        p.distance_km

    -- Show properties from lowest to highest average NO2.
    ORDER BY average_no2 ASC
""").fetchall()


# STEP 3: DISPLAY THE RESULTS

print("\nPROPLENS - PROPERTY ENVIRONMENTAL COMPARISON")
print("------------------------------------------")

for row in results:
    name, station, distance, average, recorded, valid, completeness = row
        # Classify the measurement coverage using PropLens rules.
    # These are project thresholds, not official LAQN ratings.
    if completeness >= 95:
        quality_status = "GOOD"
    elif completeness >= 80:
        quality_status = "CAUTION"
    else:
        quality_status = "POOR"

    print(f"\nProperty: {name}")
    print(f"Station: {station}")
    print(f"Distance: {distance:.2f} km")
    print(f"Average NO2: {average:.2f}")
    print(f"Data completeness: {completeness}% ({valid}/{recorded})")
    # Show whether missing data may affect the comparison.
    print(f"Data quality: {quality_status}")


# STEP 4: CLOSE THE DATABASE

# STEP 4: SAVE THE PROPERTY COMPARISON

# Create a list to hold the final report rows.
report_rows = []

# Go through each result returned by our SQL query.
for row in results:

    # Unpack the values in the same order as our SQL SELECT.
    name, station, distance, average, recorded, valid, completeness = row

    # Apply our existing data-quality rules.
    if completeness >= 95:
        quality_status = "GOOD"
    elif completeness >= 80:
        quality_status = "CAUTION"
    else:
        quality_status = "POOR"

    # Store one report row for each property.
    report_rows.append({
        "property_name": name,
        "station_code": station,
        "distance_km": distance,
        "average_no2_ug_m3": average,
        "recorded_hours": recorded,
        "valid_hours": valid,
        "completeness_percent": completeness,
        "data_quality": quality_status
    })

# Choose the column names for our CSV report.
columns = [
    "property_name",
    "station_code",
    "distance_km",
    "average_no2_ug_m3",
    "recorded_hours",
    "valid_hours",
    "completeness_percent",
    "data_quality"
]

# Create the output folder if it doesn't exist.
from pathlib import Path
Path("Outputs").mkdir(exist_ok=True)

# Save the report as a CSV file.
with open(
    "Outputs/property_comparison.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    # Create the CSV writer and write the results.
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(report_rows)

print("\nReport saved to Outputs/property_comparison.csv")
connection.close()
