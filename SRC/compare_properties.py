
# PROPLENS - BUILDING ENVIRONMENTAL COMPARISON
#
# Purpose:
# Compare historical NO2 measurements near six London buildings.
#
# Use our automatic station matches instead of manually
# selected stations.
#
# Important:
# Measurements describe conditions at monitoring stations,
# not the exact pollution exposure inside buildings.


# STEP 1: IMPORT OUR TOOLS

# Read and write CSV files.
import csv

# Work with project folders.
from pathlib import Path

# Query our air quality database.
import duckdb


# STEP 2: FIND OUR PROJECT FILES

# Find the main PropLens folder.
project_folder = Path(__file__).resolve().parents[1]

# Find the database and automatic station matching report.
database_path = project_folder / "Data/proplens.duckdb"
matches_path = project_folder / "Outputs/station_matches.csv"

# Decide where to save the comparison.
output_path = project_folder / "Outputs/property_comparison.csv"

# Create the output folder if necessary.
output_path.parent.mkdir(exist_ok=True)


# STEP 3: CONNECT TO DUCKDB

connection = duckdb.connect(str(database_path))

# Read our automatic station matches as a temporary SQL view.
# We only need matches for NO2.
# DuckDB needs the CSV path written directly into
# the SQL when creating a view.

# Convert the Windows file path into a SQL friendly path.
matches_sql_path = matches_path.as_posix().replace("'", "''")

# Create a temporary view containing only NO2 matches.
connection.execute(f"""
    CREATE OR REPLACE TEMP VIEW no2_matches AS

    SELECT *
    FROM read_csv_auto('{matches_sql_path}')

    WHERE pollutant = 'NO2'
""")


# STEP 4: CALCULATE HISTORICAL NO2 AVERAGES

# JOIN connects each building to the measurements
# collected at its selected monitoring station.
#
# We use the same 89-day historical period as our
# data quality and hourly analysis reports.
#
# AVG ignores NULL values automatically.

results = connection.execute("""
    SELECT
        p.property_name,
        p.building_type,
        p.station_code,
        p.station_name,
        p.station_type,
        p.distance_km,
        p.distance_status,

        -- Average NO2 reading at the monitoring station.
        ROUND(AVG(m.value), 2) AS average_no2,

        -- Number of hourly timestamps stored.
        COUNT(m.measured_at) AS recorded_hours,

        -- Number containing a numerical measurement.
        COUNT(m.value) AS valid_hours,

        -- Calculate completeness against all expected
        -- hours, including any entirely missing timestamps.
        ROUND(
            100.0 * COUNT(m.value) / 2136,
            1
        ) AS completeness_percent

    FROM no2_matches AS p

    LEFT JOIN measurements AS m
        ON p.station_code = m.site_code
        AND m.species_code = 'NO2'
        AND m.measured_at >= '2026-08-01'
        AND m.measured_at < '2026-10-29'

    GROUP BY
        p.property_name,
        p.building_type,
        p.station_code,
        p.station_name,
        p.station_type,
        p.distance_km,
        p.distance_status

    -- Alphabetical order keeps building reports easy
    -- to compare without implying a building ranking.
    ORDER BY p.property_name

""").fetchall()


# STEP 5: IDENTIFY SHARED MONITORING STATIONS

# Several buildings can share the same monitoring station.
# Those buildings will have identical pollution averages.
station_counts = {}

for row in results:

    station_code = row[2]

    station_counts[station_code] = (
        station_counts.get(station_code, 0) + 1
    )


# STEP 6: PREPARE OUR REPORT

report_rows = []

print("\nPROPLENS - NO2 BUILDING COMPARISON")
print("--------------------------------")

for row in results:

    (
        name,
        building_type,
        station_code,
        station_name,
        station_type,
        distance,
        distance_status,
        average,
        recorded,
        valid,
        completeness
    ) = row

    # Classify data completeness using our project rules.
    # These are not official LAQN quality classifications.
    if completeness >= 95:
        data_quality = "GOOD"

    elif completeness >= 80:
        data_quality = "CAUTION"

    else:
        data_quality = "POOR"

    # Check how many buildings share this station.
    shared_count = station_counts[station_code]

    if shared_count > 1:
        shared_station = "YES"
    else:
        shared_station = "NO"

    # Display the results.
    print(f"\nBuilding: {name}")
    print(f"Building type: {building_type}")
    print(f"Station: {station_name} ({station_code})")
    print(f"Station type: {station_type}")
    print(f"Distance: {distance:.2f} km ({distance_status})")

    if average is not None:
        print(f"Average NO2: {average:.2f} ug/m3")
    else:
        print("Average NO2: No valid measurements")

    print(f"Completeness: {completeness}%")
    print(f"Valid readings: {valid}/{recorded}")

    if shared_station == "YES":
        print(
            f"Note: This station is shared by "
            f"{shared_count} buildings."
        )

    if distance_status == "DISTANT":
        print(
            "Warning: Monitoring station is over 3 km away."
        )

    # Prepare a row for the CSV report.
    report_rows.append({
        "property_name": name,
        "building_type": building_type,
        "station_code": station_code,
        "station_name": station_name,
        "station_type": station_type,
        "distance_km": distance,
        "distance_status": distance_status,
        "average_no2_ug_m3": average,
        "recorded_hours": recorded,
        "valid_hours": valid,
        "completeness_percent": completeness,
        "data_quality": data_quality,
        "shared_station": shared_station
    })


# STEP 7: SAVE THE COMPARISON REPORT

# Define the order of our CSV columns.
columns = [
    "property_name",
    "building_type",
    "station_code",
    "station_name",
    "station_type",
    "distance_km",
    "distance_status",
    "average_no2_ug_m3",
    "recorded_hours",
    "valid_hours",
    "completeness_percent",
    "data_quality",
    "shared_station"
]

with open(
    output_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=columns)

    writer.writeheader()
    writer.writerows(report_rows)


# STEP 8: CLOSE THE DATABASE

connection.close()

print("\nNO2 comparison completed successfully.")
print(f"Buildings compared: {len(report_rows)}")
print("Saved to Outputs/property_comparison.csv")

