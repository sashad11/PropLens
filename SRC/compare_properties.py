
# PROPLENS - BUILDING ENVIRONMENTAL COMPARISON
#
# Purpose:
# Compare historical NO2 measurements near six London buildings.
# Include the building type, station distance and data quality.
#
# Important:
# Station measurements describe the monitoring location,
# not the exact pollution exposure of people inside a building.


# IMPORTS

import csv
from pathlib import Path

import duckdb


# STEP 1: CONNECT TO OUR DATABASE

# Open the DuckDB database containing historical LAQN readings.
connection = duckdb.connect("Data/proplens.duckdb")

# Read our building-to-station matches as a temporary SQL view.
# A view lets us query the CSV without copying it into a new table.
connection.execute("""
    CREATE OR REPLACE TEMP VIEW property_matches AS
    SELECT *
    FROM read_csv_auto('Data/property_matches.csv')
""")


# STEP 2: CALCULATE THE AIR QUALITY COMPARISON

# JOIN connects each building to measurements from its station.
# We only compare NO2 readings so the units are consistent.
results = connection.execute("""
    SELECT
        p.property_name,
        p.building_type,
        p.station_code,
        p.distance_km,

        -- Average of available numerical NO2 readings.
        -- AVG automatically ignores NULL values.
        ROUND(AVG(m.value), 2) AS average_no2,

        -- Total hourly records stored for this station.
        COUNT(*) AS recorded_hours,

        -- Number of records with a numerical reading.
        COUNT(m.value) AS valid_hours,

        -- Percentage of stored records containing readings.
        ROUND(
            100.0 * COUNT(m.value) / COUNT(*),
            1
        ) AS completeness_percent

    FROM property_matches AS p

    JOIN measurements AS m
        ON p.station_code = m.site_code

    WHERE m.species_code = 'NO2'

    GROUP BY
        p.property_name,
        p.building_type,
        p.station_code,
        p.distance_km

    -- Show buildings from lowest to highest average NO2.
    ORDER BY average_no2 ASC, p.property_name
""").fetchall()


# STEP 3: IDENTIFY SHARED MONITORING STATIONS

# Several buildings may use the same station.
# Their averages will be identical because the source is identical.
station_counts = {}

for row in results:

    station_code = row[2]

    # Count how many buildings use each station.
    station_counts[station_code] = (
        station_counts.get(station_code, 0) + 1
    )


# STEP 4: PREPARE AND DISPLAY THE REPORT

print("\nPROPLENS - BUILDING ENVIRONMENTAL COMPARISON")
print("--------------------------------------------")

# Store the report results so we can export them to CSV.
report_rows = []

for row in results:

    # Unpack the SQL results in the order they were selected.
    (
        name,
        building_type,
        station,
        distance,
        average,
        recorded,
        valid,
        completeness
    ) = row

    # Classify measurement completeness.
    # These are PropLens project rules, not official LAQN ratings.
    if completeness >= 95:
        quality_status = "GOOD"
    elif completeness >= 80:
        quality_status = "CAUTION"
    else:
        quality_status = "POOR"

    # Classify distance between the building and station.
    # These are practical project flags, NOT scientific cutoffs.
    if distance <= 2:
        distance_status = "NEARBY"
    elif distance <= 3:
        distance_status = "CAUTION"
    else:
        distance_status = "DISTANT"

    # Check whether other buildings use the same station.
    shared_count = station_counts[station]

    if shared_count > 1:
        shared_station = "YES"
    else:
        shared_station = "NO"

    # Display the results in the terminal.
    print(f"\nBuilding: {name}")
    print(f"Building type: {building_type}")
    print(f"Station: {station}")
    print(f"Distance: {distance:.2f} km ({distance_status})")
    print(f"Average NO2: {average:.2f} µg/m³")
    print(f"Data completeness: {completeness}% ({valid}/{recorded})")
    print(f"Data quality: {quality_status}")

    if shared_station == "YES":
        print(
            f"Note: This station is shared by "
            f"{shared_count} buildings."
        )

    if distance_status == "DISTANT":
        print(
            "Warning: The station is over 3 km away. "
            "Its readings may not represent conditions "
            "near this building."
        )

    # Prepare a row for the final CSV report.
    report_rows.append({
        "property_name": name,
        "building_type": building_type,
        "station_code": station,
        "distance_km": distance,
        "distance_status": distance_status,
        "average_no2_ug_m3": average,
        "recorded_hours": recorded,
        "valid_hours": valid,
        "completeness_percent": completeness,
        "data_quality": quality_status,
        "shared_station": shared_station
    })


# STEP 5: SAVE THE COMPARISON TO CSV

# Create the output folder if it doesn't already exist.
Path("Outputs").mkdir(exist_ok=True)

# Define our report columns in the order we want them.
columns = [
    "property_name",
    "building_type",
    "station_code",
    "distance_km",
    "distance_status",
    "average_no2_ug_m3",
    "recorded_hours",
    "valid_hours",
    "completeness_percent",
    "data_quality",
    "shared_station"
]

# Export the report so it can be reviewed outside Python.
output_file = "Outputs/property_comparison.csv"

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=columns)

    # Write column headings followed by the six building rows.
    writer.writeheader()
    writer.writerows(report_rows)


# STEP 6: CLOSE THE DATABASE

# Close the connection after all SQL queries have finished.
connection.close()

print(f"\nReport saved to {output_file}")
